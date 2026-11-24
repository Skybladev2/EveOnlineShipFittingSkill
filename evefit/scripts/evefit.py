#!/usr/bin/env python3
"""evefit - build and validate EVE Online ship fits.

Data comes from two places:
  * the official EVE SDE over HTTP (sde.evetech.net), cached under the evefit
    cache directory as JSON Lines tables;
  * EVEShip.fit's dogma-engine, which proves that CPU, powergrid, calibration,
    slots, drones, charges and skills allow the fit (all skills at level 5).

Run `evefit.py --help` for commands.
"""

from __future__ import annotations

import argparse
import difflib
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SDE_API_URL = "https://sde.evetech.net"
SDE_TENANT = "tranquility"
SDE_TENANT_URL = f"{SDE_API_URL}/{SDE_TENANT}/"
SDE_LATEST_URL = f"{SDE_TENANT_URL}latest/"
SDE_TABLES = (
    "types",
    "groups",
    "categories",
    "dogmaAttributes",
    "dogmaEffects",
    "typeDogma",
)
REQUIREMENTS = "eveshipfit-dogma-engine[sde]>=15.0"
YT_REQUIREMENTS = "yt-dlp>=2024.12"

CAT_SHIP = 6
CAT_MODULE = 7
CAT_CHARGE = 8
CAT_SKILL = 16
CAT_DRONE = 18
CAT_IMPLANT = 20
CAT_SUBSYSTEM = 32

# Attribute IDs used when printing ship cards.
SHIP_ATTRS = {
    9: "structureHP",
    11: "powergrid",
    12: "lowSlots",
    13: "mediumSlots",
    14: "highSlots",
    48: "cpu",
    101: "launcherHardpoints",
    102: "turretHardpoints",
    263: "shieldHP",
    265: "armorHP",
    283: "droneBay",
    422: "techLevel",
    482: "capacitor",
    552: "signatureRadius",
    1132: "calibration",
    1137: "rigSlots",
    1154: "calibrationSlots",
    1271: "droneBandwidth",
    1547: "rigSize",
}
SKILL_ATTRS = {182 + i: 277 + i for i in range(6)}  # requiredSkill1..6 / levels

RESOURCE_LABELS = {
    "cpu": "CPU",
    "powergrid": "Powergrid",
    "calibration": "Calibration",
    "drone_bay": "Drone bay",
    "drone_bandwidth": "Drone bandwidth",
    "launched_drones": "Launched drones",
    "fighter_bay": "Fighter bay",
    "fighter_tubes": "Fighter tubes",
    "light_fighter_tubes": "Light fighter tubes",
    "support_fighter_tubes": "Support fighter tubes",
    "heavy_fighter_tubes": "Heavy fighter tubes",
    "cargo_bay": "Cargo bay",
    "charge_capacity": "Charge capacity",
}
SLOT_LABELS = {
    "high": "High slots",
    "medium": "Medium slots",
    "low": "Low slots",
    "rig": "Rig slots",
    "subsystem": "Subsystem slots",
    "service": "Service slots",
    "turret": "Turret hardpoints",
    "launcher": "Launcher hardpoints",
}
RIG_SIZES = {1: "Small", 2: "Medium", 3: "Large", 4: "Capital", 5: "Extra large"}


def cache_root() -> Path:
    explicit = os.environ.get("EVEFIT_CACHE")
    if explicit:
        return Path(explicit).expanduser()
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "evefit"


def sde_root() -> Path:
    return cache_root() / "sde"


def build_dir(identifier: int | str) -> Path:
    return sde_root() / str(identifier)


def venv_python() -> Path:
    venv = cache_root() / "venv"
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


# --------------------------------------------------------------------------
# Environment bootstrap
# --------------------------------------------------------------------------


def have_engine() -> bool:
    try:
        import esf_dogma_engine  # noqa: F401
    except Exception:
        return False
    return True


def trust_module():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import trust

    return trust


def ensure_engine() -> None:
    """Verify the approved build, install only verified wheels, then re-exec."""
    if os.environ.get("EVEFIT_BOOTSTRAPPED") == "1":
        return
    py = venv_python()
    if not py.exists():
        log(f"evefit: creating venv at {cache_root() / 'venv'}")
        subprocess.run([sys.executable, "-m", "venv", str(cache_root() / "venv")], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    tr = trust_module()
    try:
        tr.ensure_trusted(py)
    except tr.TrustError as exc:
        sys.exit(
            f"{exc}\n\n"
            "No package code is installed or imported before review. "
            "See references/trust.md."
        )
    probe = subprocess.run(
        [str(py), "-c", "import esf_dogma_engine"], capture_output=True
    )
    if probe.returncode != 0:
        sys.exit(
            "dogma-engine could not be imported after installing the approved wheels.\n"
            f"Delete {cache_root() / 'venv'} and run again."
        )
    env = dict(os.environ, EVEFIT_BOOTSTRAPPED="1")
    os.execve(str(py), [str(py), str(Path(__file__).resolve()), *sys.argv[1:]], env)


def engine_versions() -> tuple[str, str] | None:
    """Return (dogma-engine, SDE package) versions from the venv if present."""
    code = (
        "import importlib.metadata as m;"
        "print(m.version('eveshipfit-dogma-engine'));"
        "print(m.version('eveshipfit-sde'))"
    )
    py = venv_python()
    if py.exists():
        result = subprocess.run([str(py), "-c", code], capture_output=True, text=True)
        if result.returncode == 0:
            parts = result.stdout.split()
            if len(parts) == 2:
                return parts[0], parts[1]
    if have_engine():
        from importlib.metadata import version

        return version("eveshipfit-dogma-engine"), version("eveshipfit-sde")
    return None


# --------------------------------------------------------------------------
# SDE download and cache
# --------------------------------------------------------------------------


def _sde_request(url: str, timeout: int = 30) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": "evefit-skill",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip",
        },
    )


def fetch_sde_json(url: str, timeout: int = 30):
    """Fetch one SDE API document, decompressing the CDN's gzip response."""
    with urllib.request.urlopen(_sde_request(url, timeout), timeout=timeout) as resp:
        raw = resp.read()
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
    if "gzip" in encoding:
        raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def latest_sde_release(timeout: int = 30) -> dict:
    """Return the release document that `/latest/` currently points at."""
    doc = fetch_sde_json(SDE_LATEST_URL, timeout=timeout)
    if not doc.get("release") or not isinstance(doc.get("tables"), dict):
        raise RuntimeError("SDE latest response has no release or tables")
    return doc


def release_for_build(build: int, timeout: int = 30) -> dict:
    """Resolve a build number to a release; newer releases win ties."""
    tenant = fetch_sde_json(SDE_TENANT_URL, timeout=timeout)
    for entry in tenant.get("releases", []):
        doc = fetch_sde_json(entry["releaseUrl"], timeout=timeout)
        if int(doc.get("buildNumber", -1)) == build:
            return doc
    raise RuntimeError(
        f"build {build} is not in the retained releases; use --release with "
        f"a release id from {SDE_TENANT_URL}"
    )


def release_url(release: str) -> str:
    return f"{SDE_TENANT_URL}{release}/"


def cached_releases() -> list[dict]:
    """Cached releases, newest first; old zip caches are still readable."""
    if not sde_root().is_dir():
        return []
    out: list[dict] = []
    for path in sde_root().iterdir():
        if not path.is_dir() or not (path / "index.json").exists():
            continue
        manifest = path / "manifest.json"
        try:
            meta = load_json(manifest) if manifest.exists() else {}
        except Exception:
            meta = {}
        release = meta.get("release")
        build = meta.get("build")
        if build is None:
            try:
                build = load_json(path / "index.json").get("build")
            except Exception:
                build = int(path.name) if path.name.isdigit() else 0
        if release:
            out.append(
                {
                    "release": release,
                    "build": int(build or 0),
                    "releaseDate": meta.get("releaseDate", ""),
                    "source": meta.get("source", release_url(release)),
                    "tables": meta.get("tables", {}),
                    "dir": path,
                }
            )
        elif path.name.isdigit():
            out.append(
                {
                    "release": None,
                    "build": int(path.name),
                    "releaseDate": "",
                    "source": "",
                    "tables": {},
                    "dir": path,
                }
            )
    return sorted(
        out,
        key=lambda row: (
            1 if row["release"] else 0,
            row["releaseDate"] or row["release"] or "",
            row["build"],
        ),
        reverse=True,
    )


def newest_cached_release() -> dict | None:
    releases = cached_releases()
    return releases[0] if releases else None


def newest_cached_build() -> int | None:
    release = newest_cached_release()
    return release["build"] if release else None


def download_sde_table(table: str, meta: dict, dest: Path) -> Path:
    """Download one gzip JSON Lines table and leave it uncompressed on disk."""
    url = meta["jsonl"]["url"]
    tmp = dest / f"{table}.jsonl.part"
    target = dest / f"{table}.jsonl"
    log(f"evefit: downloading {table}")
    start = time.time()
    with urllib.request.urlopen(_sde_request(url, 300), timeout=300) as resp:
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
        body = gzip.GzipFile(fileobj=resp) if "gzip" in encoding else resp
        with open(tmp, "wb") as fh:
            shutil.copyfileobj(body, fh, length=1 << 20)
    tmp.replace(target)
    log(f"evefit: {table} {target.stat().st_size / 1e6:.1f} MB "
        f"in {time.time() - start:.0f}s")
    return target


def reuse_sde_table(previous: dict | None, table: str, meta: dict, dest: Path) -> bool:
    """Copy a table from the previous release when its version is unchanged."""
    if not previous:
        return False
    old = (previous.get("tables") or {}).get(table) or {}
    source = previous["dir"] / f"{table}.jsonl"
    if old.get("version") != meta.get("version") or not source.exists():
        return False
    target = dest / f"{table}.jsonl"
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)
    log(f"evefit: reusing {table} (unchanged since {previous.get('release') or previous['build']})")
    return True


def build_indexes(dest: Path, build: int, release: str | None = None) -> None:
    groups: dict[int, tuple[str, int]] = {}
    with open(dest / "groups.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            groups[row["groupID"]] = (row["name"]["en"], row["categoryID"])

    types: dict[str, list] = {}
    ship_ids: set[int] = set()
    skill_ids: list[int] = []
    with open(dest / "types.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            tid = row["typeID"]
            gid = row.get("groupID", 0)
            gname, cat = groups.get(gid, ("", 0))
            name = row.get("name", {}).get("en", "")
            if not name:
                continue
            types[str(tid)] = [name, gname, cat, bool(row.get("published"))]
            if cat == CAT_SHIP:
                ship_ids.add(tid)
            elif cat == CAT_SKILL:
                skill_ids.append(tid)

    index = {"build": build, "types": types}
    if release:
        index["release"] = release
    (dest / "index.json").write_text(
        json.dumps(index, separators=(",", ":")), encoding="utf-8"
    )

    ships: dict[str, dict] = {}
    with open(dest / "typeDogma.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            tid = row["typeID"]
            if tid not in ship_ids:
                continue
            attrs = {str(a["attributeID"]): a["value"] for a in row.get("dogmaAttributes", [])}
            name, gname, cat, pub = types[str(tid)]
            ships[str(tid)] = {"name": name, "group": gname, "published": pub, "attrs": attrs}

    (dest / "ships.json").write_text(
        json.dumps(ships, separators=(",", ":")), encoding="utf-8"
    )

    attr_names: dict[str, dict] = {}
    with open(dest / "dogmaAttributes.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            attr_names[str(row["attributeID"])] = {
                "name": row["name"],
                "display": row.get("displayName", {}).get("en", row["name"]),
            }
    (dest / "attrs.json").write_text(
        json.dumps(attr_names, separators=(",", ":")), encoding="utf-8"
    )

    effect_names: dict[str, str] = {}
    with open(dest / "dogmaEffects.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            effect_names[str(row["effectID"])] = row.get("name", "")
    (dest / "effects.json").write_text(
        json.dumps(effect_names, separators=(",", ":")), encoding="utf-8"
    )

    skills = sorted(skill_ids)
    skill_data = {"build": build, "skills": skills}
    if release:
        skill_data["release"] = release
    (dest / "skills.json").write_text(json.dumps(skill_data), encoding="utf-8")
    # Keep a stable copy so validation still works if the build dir is pruned.
    (cache_root() / "skills.json").write_text(json.dumps(skill_data), encoding="utf-8")


def prune_releases(keep: int = 2) -> None:
    """Keep the current and previous HTTP releases; drop older ones."""
    releases = [row for row in cached_releases() if row["release"]]
    for row in releases[keep:]:
        shutil.rmtree(row["dir"], ignore_errors=True)


def ensure_sde(release: dict | str | None = None, force: bool = False) -> dict:
    if isinstance(release, str):
        release = fetch_sde_json(release_url(release))
    if release is None:
        try:
            release = latest_sde_release()
        except Exception as exc:  # offline fallback
            cached = newest_cached_release()
            if cached is None:
                sys.exit(f"cannot reach the SDE API ({exc}) and no cache exists")
            log(f"evefit: offline, using cached SDE release "
                f"{cached.get('release') or cached['build']}")
            return cached

    rid = release.get("release")
    if not rid:
        sys.exit("SDE release document has no release id")
    build = int(release.get("buildNumber") or release.get("build") or 0)
    dest = build_dir(rid)
    if (dest / "index.json").exists() and not force:
        cached = next((row for row in cached_releases() if row["release"] == rid), None)
        return cached or {
            "release": rid,
            "build": build,
            "releaseDate": release.get("releaseDate", ""),
            "source": release_url(rid),
            "tables": release.get("tables", {}),
            "dir": dest,
        }

    dest.mkdir(parents=True, exist_ok=True)
    previous = next(
        (row for row in cached_releases() if row["release"] and row["release"] != rid),
        None,
    )
    tables = release.get("tables") or {}
    for table in SDE_TABLES:
        meta = tables.get(table)
        if not meta or not meta.get("jsonl", {}).get("url"):
            sys.exit(f"SDE release {rid} has no JSONL table {table}")
        if not force and reuse_sde_table(previous, table, meta, dest):
            continue
        download_sde_table(table, meta, dest)

    log("evefit: building indexes")
    build_indexes(dest, build, rid)
    manifest = {
        "release": rid,
        "build": build,
        "releaseDate": release.get("releaseDate", ""),
        "source": release_url(rid),
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tables": {
            table: {
                "version": (tables.get(table) or {}).get("version", ""),
                "url": (tables.get(table) or {}).get("jsonl", {}).get("url", ""),
            }
            for table in SDE_TABLES
        },
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    leftover = dest / "sde.zip"
    if leftover.exists():
        leftover.unlink()
    prune_releases()
    log(f"evefit: SDE {rid} (build {build}) ready at {dest}")
    return {
        "release": rid,
        "build": build,
        "releaseDate": release.get("releaseDate", ""),
        "source": release_url(rid),
        "tables": manifest["tables"],
        "dir": dest,
    }


def data_dir() -> Path:
    """Directory of the newest cached release, downloading it if needed."""
    release = newest_cached_release()
    if release is None:
        release = ensure_sde()
    return release["dir"]


def load_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_types(build_path: Path | None = None) -> dict[str, list]:
    return load_json((build_path or data_dir()) / "index.json")["types"]


def load_ships(build_path: Path | None = None) -> dict[str, dict]:
    return load_json((build_path or data_dir()) / "ships.json")


def load_attr_names(build_path: Path | None = None) -> dict[str, dict]:
    return load_json((build_path or data_dir()) / "attrs.json")


def load_effect_names(build_path: Path | None = None) -> dict[str, str]:
    return load_json((build_path or data_dir()) / "effects.json")


def load_skills() -> list[int]:
    path = cache_root() / "skills.json"
    if not path.exists():
        release = newest_cached_release()
        if release is not None and (release["dir"] / "skills.json").exists():
            return load_json(release["dir"] / "skills.json")["skills"]
        sys.exit("no skills index yet; run: evefit.py sde update")
    return load_json(path)["skills"]


def name_hints(query: str, names: list[str], n: int = 5) -> list[str]:
    words = [w for w in re.findall(r"[A-Za-z0-9']+", query.lower()) if len(w) > 1]
    ordered: list[str] = []
    if words:
        candidates = [
            nm for nm in names if nm.lower().startswith(words[0])
        ]
        last = words[-1]
        if last.isdigit() or last in ("i", "ii", "iii", "iv", "v"):
            candidates = [
                nm for nm in candidates
                if nm.lower().split()[-1].strip("'") == last
            ]
        candidates.sort(key=lambda nm: (len(nm), nm))
        ordered.extend(candidates[:n])
    for nm in difflib.get_close_matches(query, names, n=n, cutoff=0.55):
        if len(ordered) >= n:
            break
        if nm not in ordered:
            ordered.append(nm)
    return ordered[:n]


def find_type(types: dict[str, list], query: str, exact: bool = False) -> tuple[str, list]:
    q = query.strip().lower()
    exact_hits = [(tid, row) for tid, row in types.items() if row[0].lower() == q]
    if exact_hits:
        return exact_hits[0]
    if exact:
        sys.exit(f"unknown type: {query!r} (use `search` to find the exact name)")
    hits = [(tid, row) for tid, row in types.items() if q in row[0].lower()]
    hits.sort(key=lambda x: (not x[1][3], len(x[1][0]), x[1][0]))
    if not hits:
        hints = name_hints(query, [row[0] for row in types.values()])
        extra = ("\n  did you mean: " + "; ".join(hints)) if hints else ""
        sys.exit(f"unknown type: {query!r}{extra}")
    if len(hits) > 1:
        log(f"evefit: {len(hits)} matches for {query!r}, using {hits[0][1][0]}; "
            "run `search` to see more")
    return hits[0]


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def cmd_sde_status(args) -> None:
    print(f"cache: {cache_root()}")
    releases = cached_releases()
    if releases:
        shown = []
        for row in releases:
            if row["release"]:
                shown.append(f"{row['release']} (build {row['build']})")
            else:
                shown.append(f"{row['build']} (legacy zip)")
        print("cached SDE releases: " + ", ".join(shown))
    else:
        print("cached SDE releases: none")
    try:
        latest = latest_sde_release()
        latest_build = int(latest["buildNumber"])
        print(f"latest official SDE release: {latest['release']} "
              f"(build {latest_build}, {latest.get('releaseDate', '')})")
    except Exception as exc:
        latest_build = None
        print(f"latest official SDE release: unavailable ({exc})")
    versions = engine_versions()
    if versions:
        esf_sde = versions[1]
        engine_build = int(esf_sde.split(".")[1])
        print(f"dogma-engine: {versions[0]} | SDE package: {esf_sde} (build {engine_build})")
        if latest_build and engine_build != latest_build:
            print("WARNING: engine data is not the latest build; "
                  "run `evefit.py env update` to refresh it")
    else:
        print("dogma-engine: not installed (will bootstrap on validate)")
    if releases:
        row = releases[0]
        label = row["release"] or f"build {row['build']}"
        print(f"lookup data will use: {label}")


def cmd_sde_update(args) -> None:
    requested = None
    pinned = bool(args.release or args.build)
    try:
        if args.release:
            requested = fetch_sde_json(release_url(args.release))
        elif args.build:
            requested = release_for_build(args.build)
        saved = ensure_sde(requested, force=args.force)
    except Exception as exc:
        if pinned:
            sys.exit(f"cannot update SDE: {exc}")
        cached = newest_cached_release()
        if cached is None:
            sys.exit(f"cannot update SDE: {exc}")
        log(f"evefit: update failed ({exc}); keeping cached SDE "
            f"{cached.get('release') or cached['build']}")
        saved = cached
    label = saved.get("release") or f"build {saved['build']}"
    print(f"SDE {label} (build {saved['build']}) cached at {saved['dir']}")
    versions = engine_versions()
    if versions:
        engine_build = int(versions[1].split(".")[1])
        if engine_build != saved["build"]:
            log(f"evefit: dogma-engine still uses build {engine_build}; "
                "run `python3 scripts/evefit.py env update`")
    else:
        log("evefit: dogma-engine not installed yet; validate will bootstrap it")


def cmd_env_update(args) -> None:
    ensure_engine()
    tr = trust_module()
    py = venv_python()
    record = tr.load_json(tr.approved_path())
    latest = tr.latest_version(tr.PACKAGE)
    latest_sde = tr.latest_version(tr.SDE_PACKAGE)
    approved_engine = record.get("version") if record else None
    approved_sde = (record.get("sde") or {}).get("version") if record else None
    if not record or latest != approved_engine or latest_sde != approved_sde:
        print(f"approved: {approved_engine} + SDE {approved_sde}")
        print(f"latest:   {latest} + SDE {latest_sde}")
        pending = tr.load_json(tr.pending_path())
        if not pending or pending.get("version") != latest:
            tr.prepare(latest, latest_sde)
        print("\nUpdate NOT installed. Review the report, then run:")
        print(f'  python3 scripts/trust.py approve --version {latest} --notes "..."')
        print("After approval: python3 scripts/evefit.py env update")
        raise SystemExit(3)
    tr.install_approved(py)
    from importlib.metadata import version

    print("dogma-engine:", version("eveshipfit-dogma-engine"))
    print("SDE package:", version("eveshipfit-sde"))


def cmd_doctor(args) -> None:
    print(f"python: {sys.version.split()[0]} ({sys.executable})")
    print(f"cache: {cache_root()}")
    versions = engine_versions()
    print(f"engine available: {bool(versions)}")
    if versions:
        print(f"dogma-engine: {versions[0]}")
        print(f"SDE package: {versions[1]}")
    releases = cached_releases()
    if releases:
        row = releases[0]
        print(f"SDE cache: {row.get('release') or row['build']} (build {row['build']})")
    else:
        print("SDE cache: none")
    try:
        latest = latest_sde_release()
        print(f"official latest: {latest['release']} (build {latest['buildNumber']})")
    except Exception as exc:
        print(f"official latest: unavailable ({exc})")
    try:
        print(f"skills indexed: {len(load_skills())}")
    except SystemExit:
        print("skills indexed: 0")
    tr = trust_module()
    record = tr.load_json(tr.approved_path())
    if record:
        print(f"trust: approved {record['version']} wheel {record['engine_wheel']['sha256'][:16]}")
        ok, problems = tr.verify_installed(venv_python(), record)
        print("trust: installed files match" if ok else "trust: MISMATCH - " + "; ".join(problems))
    else:
        print("trust: no approved build (validate will not run)")


def cmd_search(args) -> None:
    types = load_types()
    q = args.query.lower()
    hits = [
        (tid, row)
        for tid, row in types.items()
        if q in row[0].lower() and (args.all or row[3])
    ]
    hits.sort(key=lambda x: (x[1][2], len(x[1][0]), x[1][0]))
    if not hits:
        print("no matches")
        return
    for tid, row in hits[: args.limit]:
        name, group, cat, published = row
        flag = "" if published else " [unpublished]"
        print(f"{int(tid):>7}  {name:<45} {group:<28} cat={cat}{flag}")
    if len(hits) > args.limit:
        print(f"... {len(hits) - args.limit} more")


def _fmt(value) -> str:
    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.0f}"
        return f"{value:g}"
    return str(value)


def cmd_ship(args) -> None:
    ships = load_ships()
    types = None
    q = args.query.strip().lower()
    exact = [(tid, s) for tid, s in ships.items() if s["name"].lower() == q]
    if exact:
        tid, ship = exact[0]
    else:
        hits = [(tid, s) for tid, s in ships.items() if q in s["name"].lower()]
        hits.sort(key=lambda x: (not x[1]["published"], len(x[1]["name"])))
        if not hits:
            sys.exit(f"unknown ship: {args.query!r}")
        tid, ship = hits[0]
        if len(hits) > 1:
            log(f"evefit: {len(hits)} ships match, showing {ship['name']}")
    a = ship["attrs"]
    print(f"{ship['name']} ({tid}) - {ship['group']}")
    print(
        "slots: "
        f"{_fmt(a.get('14', 0))} high / {_fmt(a.get('13', 0))} medium / "
        f"{_fmt(a.get('12', 0))} low / {_fmt(a.get('1137', 0))} rig"
    )
    print(
        f"cpu {_fmt(a.get('48', 0))} tf | powergrid {_fmt(a.get('11', 0))} MW | "
        f"calibration {_fmt(a.get('1132', 0))} ({_fmt(a.get('1154', 0))} slots)"
    )
    print(
        f"hardpoints: {_fmt(a.get('102', 0))} turret / {_fmt(a.get('101', 0))} launcher"
    )
    print(
        f"drones: {_fmt(a.get('283', 0))} m3 / {_fmt(a.get('1271', 0))} Mbit/s | "
        f"cap {_fmt(a.get('482', 0))} GJ | sig {_fmt(a.get('552', 0))} m"
    )
    print(
        f"hp: shield {_fmt(a.get('263', 0))} / armor {_fmt(a.get('265', 0))} / "
        f"structure {_fmt(a.get('9', 0))}"
    )
    tech = a.get("422")
    rig = a.get("1547")
    extras = []
    if tech:
        extras.append(f"tech {_fmt(tech)}")
    if rig:
        extras.append(f"rig size {RIG_SIZES.get(int(rig), _fmt(rig))}")
    if extras:
        print(" | ".join(extras))
    if types is None:
        types = load_types()
    skills = []
    for skill_attr, level_attr in SKILL_ATTRS.items():
        sid = a.get(str(skill_attr))
        if sid:
            level = a.get(str(level_attr), 0)
            sname = types.get(str(int(sid)), [f"type {int(sid)}"])[0]
            skills.append(f"{sname} {_fmt(level)}")
    if skills:
        print("required skills: " + ", ".join(skills))
    if not any(a.get(k) for k in ("14", "13", "12")) and "Strategic Cruiser" in ship["group"]:
        print("note: T3 hull slots come from fitted subsystems")


def cmd_attrs(args) -> None:
    types = load_types()
    tid, row = find_type(types, args.type, exact=args.exact)
    attr_names = load_attr_names()
    effect_names = load_effect_names()
    attrs = {}
    effects = []
    with open(data_dir() / "typeDogma.jsonl", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            if str(d["typeID"]) != str(tid):
                continue
            attrs = {str(x["attributeID"]): x["value"] for x in d.get("dogmaAttributes", [])}
            effects = [x["effectID"] for x in d.get("dogmaEffects", [])]
            break
    print(f"{row[0]} ({tid}) - {row[1]}")
    print("attributes:")
    shown = 0
    for aid, value in sorted(attrs.items(), key=lambda kv: attr_names.get(kv[0], {}).get("name", kv[0])):
        if not args.all and value == 0:
            continue
        meta = attr_names.get(aid, {"name": f"attr {aid}", "display": f"attr {aid}"})
        label = meta["display"]
        if int(aid) in SKILL_ATTRS and value:
            label += f": {_item_name(types, int(value))}"
        print(f"  {aid:>5}  {meta['name']:<32} {_fmt(value):>12}  {label}")
        shown += 1
    if not shown:
        print("  (none)")
    if effects and args.all:
        print("effects:")
        for eid in effects:
            print(f"  {eid:>5}  {effect_names.get(str(eid), '')}")


def _item_name(index: dict[str, list], type_id) -> str:
    row = index.get(str(type_id))
    return row[0] if row else f"type {type_id}"


def describe_violation(v: dict, index: dict[str, list], groups: dict[int, str]) -> str:
    target = v.get("target", {})
    rule = v.get("rule", {})
    where = "ship"
    if target.get("type") == "item":
        where = _item_name(index, target.get("type_id", "?"))
    elif target.get("type") == "charge":
        where = "charge"
    kind = rule.get("type")
    if kind == "resource":
        label = RESOURCE_LABELS.get(rule.get("resource"), rule.get("resource"))
        return f"{where}: {label} {_fmt(rule.get('used'))} used / {_fmt(rule.get('available'))} available"
    if kind == "slots":
        label = SLOT_LABELS.get(rule.get("slot"), rule.get("slot"))
        return f"{where}: {label} {_fmt(rule.get('used'))} used / {_fmt(rule.get('available'))} available"
    if kind == "skill":
        name = _item_name(index, rule.get("type_id"))
        return f"{where}: requires {name} {rule.get('required')} (have {rule.get('level')})"
    if kind == "wrong_slot":
        return f"{where}: belongs in {rule.get('expected')} slot"
    if kind == "not_a_module":
        return f"{where}: not a module"
    if kind == "slot_taken":
        return f"{where}: slot already occupied"
    if kind == "wrong_slot_index":
        return f"{where}: belongs in slot {rule.get('expected')}"
    if kind == "subsystem_taken":
        return f"{where}: another subsystem covers this part"
    if kind == "rig_size":
        return f"{where}: rig size {rule.get('item')} but ship takes {rule.get('ship')}"
    if kind == "ship_restricted":
        return f"{where}: cannot be fitted to this ship"
    if kind == "capital_item":
        return f"{where}: capital module on a subcapital"
    if kind == "max_group":
        return f"{where}: too many from group {rule.get('group_id')}"
    if kind == "max_type":
        return f"{where}: too many of this type"
    if kind == "charge_group":
        return f"{where}: charge group not accepted"
    if kind == "charge_size":
        return f"{where}: charge size mismatch"
    if kind == "not_a_hull":
        return "target is not a ship hull"
    return f"{where}: {json.dumps(rule, separators=(',', ':'))}"


CHARGE_MODULES = (
    ("ancillary armor repairer", "Nanite Repair Paste"),
    ("ancillary shield booster", "Cap Booster 50"),
    ("capacitor booster", "Cap Booster 50"),
)


def charge_warnings(text: str) -> list[str]:
    """Warn when a charge-fed module carries no charge on its own EFT line."""
    warnings = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("[") or "," in line:
            continue
        low = line.lower()
        for needle, charge in CHARGE_MODULES:
            if needle in low:
                warnings.append(
                    f"{line}: no charge loaded; write '{line}, {charge}' on the module line "
                    "(a cargo line does not load it)"
                )
                break
    return warnings



def _hit_chance(orbit: float, speed: float, tracking: float, sig_res: float,
                target_sig: float, optimal: float, falloff: float) -> float:
    """Turret hit chance for an orbiting attacker at the given real range."""
    angular = speed / orbit if orbit > 0 else 0.0
    effective_tracking = tracking * (target_sig / sig_res)
    term = (angular / effective_tracking) ** 2 if effective_tracking > 0 else 0.0
    if orbit > optimal:
        term += ((orbit - optimal) / falloff) ** 2 if falloff > 0 else 0.0
    return 0.5 ** term


def _fit_gun_stats(path: str) -> dict:
    """All-V turret, range, speed and DPS figures for one EFT file."""
    ensure_engine()
    import esf_dogma_engine as dogma
    from eveshipfit_sde import sde_path

    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    dogma.load_sde_from_file(str(sde_path()))
    skills = load_skills()
    fit = dogma.post_load({**dogma.load_eft(text),
                           "character": {"skills": {sid: 5 for sid in skills}}})
    calc = dogma.calculate(fit, {"validate": True})

    def g(attrs, ident):
        entry = attrs.get(ident) or attrs.get(str(ident))
        return entry.get("value") if entry else None

    ship = calc["ship"]["attributes"]
    guns = [it for it in calc["items"] if g(it.get("attributes", {}), 160)]
    if not guns:
        sys.exit("hit: fit has no turret with tracking")
    attrs = guns[0]["attributes"]
    # trackingSpeed (160) is stored in milliradians per second.
    return {
        "tracking": g(attrs, 160) / 1000.0,
        "sigres": (g(attrs, 620) or 40000.0) / 1000.0,
        "optimal": g(attrs, 54),
        "falloff": g(attrs, 158),
        "speed": g(ship, 37),
        "dps": g(ship, -12),
    }


def cmd_hit(args) -> None:
    stats = {}
    if args.fit:
        stats = _fit_gun_stats(args.fit)
        print(f"fit: tracking {stats['tracking']:.4f} rad/s | sig res {stats['sigres']:g} m | "
              f"optimal {stats['optimal']:g} m | falloff {stats['falloff']:g} m | "
              f"speed {stats['speed']:g} m/s | dps {stats['dps']:.1f}")
    tracking = args.tracking if args.tracking is not None else stats.get("tracking")
    sig_res = args.sigres if args.sigres is not None else stats.get("sigres", 40.0)
    optimal = args.optimal if args.optimal is not None else stats.get("optimal")
    falloff = args.falloff if args.falloff is not None else stats.get("falloff")
    speed = args.speed if args.speed is not None else stats.get("speed")
    dps = args.dps if args.dps else stats.get("dps", 0.0)
    missing = [name for name, value in (("tracking", tracking), ("optimal", optimal),
                                        ("falloff", falloff), ("speed", speed))
               if value is None]
    if missing:
        sys.exit("hit: missing " + ", ".join("--" + m for m in missing) + " (or pass --fit)")
    offset = args.offset
    if offset is None:
        offset = {"ab": 1000.0, "mwd": 3000.0}.get(args.prop, 0.0)
    if offset:
        print(f"real orbit = configured + {offset:.0f} m ({args.prop or 'offset'})")
    if args.sweep:
        start, end, step = (float(x) for x in args.sweep.split(":"))
        rows = []
        cursor = start
        while cursor <= end + 1e-9:
            rows.append((cursor, cursor + offset))
            cursor += step
    else:
        rows = [(args.orbit, args.orbit + offset)]
    print(f"tracking {tracking:g} rad/s | sig res {sig_res:g} m | target sig {args.target_sig:g} m")
    print(f"optimal {optimal:g} m | falloff {falloff:g} m | speed {speed:g} m/s")
    print(f"{'configured':>10} {'real':>7} {'hit':>5} {'applied dps':>12} {'ttk':>7}")
    for configured, real in rows:
        hit = _hit_chance(real, speed, tracking, sig_res, args.target_sig,
                          optimal, falloff)
        applied = dps * hit
        ttk = f"{args.target_ehp / applied:,.0f}s" if args.target_ehp and applied > 0 else "-"
        print(f"{configured:10.0f} {real:7.0f} {hit:5.2f} {applied:12.1f} {ttk:>7}")


def cmd_validate(args) -> None:
    ensure_engine()
    import esf_dogma_engine as dogma
    from eveshipfit_sde import sde_path

    text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    build = dogma.load_sde_from_file(str(sde_path()))
    skills = load_skills()
    index = {}
    try:
        index = load_types()
    except SystemExit:
        pass
    cached = newest_cached_build()
    if cached and cached != build:
        log(f"evefit: engine data is build {build}, lookup cache is {cached}; "
            "run `evefit.py env update` and `evefit.py update`")
    try:
        fit = dogma.load_eft(text)
    except Exception as exc:
        msg = str(exc)
        hint = ""
        match = re.search(r"unknown type (.+)$", msg)
        if match and index:
            bad = match.group(1).strip().strip("'\"")
            near = name_hints(bad, [row[0] for row in index.values()])
            if near:
                hint = "\n  did you mean: " + "; ".join(near)
        sys.exit(f"cannot parse EFT: {msg}{hint}")
    if args.profile:
        fit = {
            **fit,
            "environment": {
                "damage_profile": {args.profile: 1.0},
                "reactive_armor": "damage_profile",
            },
        }
    fit = dogma.post_load({**fit, "character": {"skills": {sid: 5 for sid in skills}}})
    calc = dogma.calculate(fit, {"validate": True})

    a = calc["ship"]["attributes"]

    def av(aid: int, default=0.0) -> float:
        entry = a.get(aid) or a.get(str(aid))
        if not entry:
            return default
        return entry.get("value", default)

    cpu_out = av(48)
    pg_out = av(11)
    cal_out = av(1132)
    cpu_free = av(-9)
    pg_free = av(-10)
    cal_free = av(-69)
    stats = {
        "cpu": round(cpu_out - cpu_free, 1),
        "cpu_out": round(cpu_out, 1),
        "powergrid": round(pg_out - pg_free, 1),
        "powergrid_out": round(pg_out, 1),
        "calibration": round(cal_out - cal_free, 1),
        "calibration_out": round(cal_out, 1),
        "ehp": round(av(-43), 0),
        "dps": round(av(-12), 1),
        "dps_with_reload": round(av(-13), 1),
        "drone_dps": round(av(-14), 1),
        "cap_stable": round(av(-72), 1),
    }
    violations = calc.get("violations") or []
    ok = not violations
    if args.eft_only:
        print(dogma.save_eft(fit))
        raise SystemExit(0 if ok else 2)
    if args.json:
        print(json.dumps({
            "ok": ok,
            "sde_build": build,
            "ship": fit.get("ship", {}),
            "stats": stats,
            "profile": args.profile,
            "violations": violations,
            "warnings": charge_warnings(text),
            "eft": dogma.save_eft(fit),
        }, indent=2))
        raise SystemExit(0 if ok else 2)

    ship_name = _item_name(index, fit.get("ship", {}).get("type_id"))
    print(f"ship: {ship_name}")
    print(f"sde build: {build} | skills: all 5 ({len(skills)} skills)")
    if args.profile:
        print(f"damage profile: {args.profile} only (Reactive Armor Hardener adapted)")
    print(
        f"cpu {stats['cpu']:g}/{stats['cpu_out']:g} tf | "
        f"powergrid {stats['powergrid']:g}/{stats['powergrid_out']:g} MW | "
        f"calibration {stats['calibration']:g}/{stats['calibration_out']:g}"
    )
    line = f"ehp {stats['ehp']:,.0f} | dps {stats['dps']:g}"
    if stats["dps_with_reload"]:
        line += f" (reload {stats['dps_with_reload']:g})"
    if stats["drone_dps"]:
        line += f" | drone dps {stats['drone_dps']:g}"
    if stats["cap_stable"]:
        line += f" | cap stable {stats['cap_stable']:g}%"
    print(line)
    for warning in charge_warnings(text):
        print(f"warning: {warning}")
    if ok:
        print("RESULT: OK - CPU, powergrid, calibration, slots, drones, charges and skills fit")
    else:
        print(f"RESULT: INVALID - {len(violations)} violation(s)")
        for v in violations:
            print("  - " + describe_violation(v, index, {}))
    print()
    print(dogma.save_eft(fit))
    raise SystemExit(0 if ok else 2)



# --------------------------------------------------------------------------
# YouTube sources
# --------------------------------------------------------------------------


def youtube_module():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import evefityt  # noqa: WPS433 (local helper module)

    return evefityt


def _youtube_meta(args):
    yt = youtube_module()
    from_json = getattr(args, "from_json", None)
    if from_json:
        return load_json(Path(from_json))
    yt.ensure_ytdlp()
    cookies = Path(args.cookies).expanduser() if getattr(args, "cookies", None) else None
    return yt.fetch_info(
        args.url,
        comments=getattr(args, "comments", 40),
        cookies=cookies,
        refresh=getattr(args, "refresh", False),
    )



def _trim_unknown_items(fit: dict, known: set[str]) -> dict:
    """Drop prose lines that trailed a pasted fit; keep typos inside the fit."""
    def base(item: str) -> str:
        name = re.sub(r"\s+[x×]\s*\d+$", "", item.strip())
        return name.split(",", 1)[0].strip().lower()

    flags = [base(item) in known for item in fit.get("items") or []]
    if not any(flags):
        fit["unverified"] = True
        return fit
    first = flags.index(True)
    last = len(flags) - 1 - flags[::-1].index(True)
    items = (fit.get("items") or [])[first:last + 1]
    if len(items) != len(fit.get("items") or []):
        fit["items"] = items
        fit["eft"] = "\n".join([f"[{fit['ship']}, {fit['name']}]"] + items)
        fit["trimmed"] = True
    return fit


def cmd_youtube(args) -> None:
    ensure_engine()
    yt = youtube_module()
    action = args.yt_action

    if action == "info":
        try:
            data = _youtube_meta(args)
        except SystemExit:
            raise
        except Exception as exc:
            sys.exit(f"youtube info failed: {exc}\n"
                     "Check network access or cookies, or pass --from-json with saved metadata.")

        if getattr(args, "save", None):
            Path(args.save).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            log(f"evefit: saved metadata to {args.save}")
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=1))
            return
        print(f"title: {data.get('title')}")
        print(f"channel: {data.get('channel')}")
        print(f"url: {data.get('url')}")
        print(f"uploaded: {data.get('upload_date')} | duration: {yt.fmt_timestamp(data.get('duration'))}")
        chapters = data.get("chapters") or yt.description_chapters(data.get("description") or "")
        if chapters:
            print("chapters:")
            for ch in chapters:
                start = ch.get("start_time", ch.get("seconds"))
                print(f"  {yt.fmt_timestamp(start)}  {ch.get('title') or ''}")
        print(f"description: {len(data.get('description') or '')} chars | "
              f"comments: {len(data.get('comments') or [])}")
        fits = yt.fits_from_metadata(data)
        print(f"text fits found: {len(fits)}"
              + ("" if fits else "  (next: youtube frames, then read the fitting window)"))
        return

    if action == "fits":
        try:
            data = _youtube_meta(args)
        except SystemExit:
            raise
        except Exception as exc:
            sys.exit(f"youtube fits failed: {exc}\n"
                     "Check network access or cookies, or pass --from-json with saved metadata.")

        fits = yt.fits_from_metadata(data)
        known = {row[0].lower() for row in load_types().values()}
        fits = [_trim_unknown_items(fit, known) for fit in fits]
        if args.json:
            payload = [{**f, "path": str(f.get("path"))} for f in fits]
            print(json.dumps(payload, ensure_ascii=False, indent=1))
            return
        if not fits:
            print("no EFT-style fit found in the description or comments")
            print("next: python3 scripts/evefit.py youtube frames URL --out DIR  (read the fitting window)")
            raise SystemExit(3)
        out_dir = Path(args.out) if args.out else None
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
        for idx, fit in enumerate(fits, 1):
            where = fit.get("source")
            if fit.get("author"):
                where += f" by {fit['author']}"
            if fit.get("timestamp") is not None:
                where += f" @ {yt.fmt_timestamp(fit['timestamp'])}"
            print(f"--- fit {idx}: {fit['ship']} / {fit['name']}  [{where}]")
            print(fit["eft"])
            print()
            if out_dir:
                safe = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{idx:02d}_{fit['ship']}_{fit['name']}").strip("_")
                path = out_dir / f"{safe[:80]}.eft"
                path.write_text(fit["eft"] + "\n", encoding="utf-8")
                print(f"saved: {path}")
        print("next: evefit.py checknames <fit.eft> && evefit.py validate <fit.eft>")
        return

    if action == "download":
        out_dir = Path(args.out)
        yt.ensure_ytdlp()
        cookies = Path(args.cookies).expanduser() if args.cookies else None
        path = yt.download_video(args.url, out_dir, height=args.height, cookies=cookies)
        print(path)
        return

    if action == "frames":
        out_dir = Path(args.out)
        source = args.source
        local = Path(source).expanduser()
        if local.exists():
            video = local
        else:
            yt.ensure_ytdlp()
            cookies = Path(args.cookies).expanduser() if args.cookies else None
            video = yt.download_video(source, out_dir, height=args.height, cookies=cookies)
        scene = None if args.interval else args.scene
        frames = yt.extract_frames(
            video,
            out_dir,
            scene=scene if scene is not None else 0.25,
            interval=args.interval,
            at=args.at or None,
            max_frames=args.max,
        )
        if not frames:
            print("no frames extracted; try a lower --scene value or --interval 5")
            raise SystemExit(3)
        yt.ensure_pillow()
        sheets = yt.build_sheets(frames, out_dir)
        print(f"video: {video}")
        print(f"frames: {len(frames)}")
        for frame in frames:
            print(f"  {frame['path']}  @ {yt.fmt_timestamp(frame.get('seconds'))}")
        for sheet in sheets:
            print(f"sheet: {sheet}")
        print("next: inspect the sheet for the fitting window; read module, rig, drone and")
        print("      charge names, then rebuild the EFT and run `evefit.py checknames`.")
        return

    if action == "ocr":
        for image in args.images:
            print(f"--- {image}")
            try:
                print(yt.ocr_image(Path(image)))
            except RuntimeError as exc:
                sys.exit(str(exc))
        return

    sys.exit(f"unknown youtube action: {action}")


def cmd_checknames(args) -> None:
    text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    types = load_types()
    exact = {row[0].lower(): row[0] for row in types.values()}
    all_names = [row[0] for row in types.values()]
    bad = 0
    checked = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("[") or line.startswith("#"):
            continue
        # Stacked drone/cargo lines are valid EFT; the count is not part of the name.
        line = re.sub(r"\s+[x×]\s*\d+$", "", line)
        name = line.split(",", 1)[0].strip()
        if not name:
            continue
        checked += 1
        if name.lower() in exact:
            continue
        bad += 1
        hints = name_hints(name, all_names)
        extra = (" | did you mean: " + "; ".join(hints)) if hints else ""
        print(f"unknown: {name}{extra}")
    print(f"checked {checked} item(s), {bad} unknown")
    raise SystemExit(0 if bad == 0 else 2)



def cmd_trust(args) -> None:
    tr = trust_module()
    argv = list(args.args or [])
    if not argv:
        argv = ["status"]
    sys.argv = ["trust.py", *argv]
    tr.main()

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="evefit.py", description="Build and validate EVE Online ship fits."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="show SDE cache and engine versions")
    p_status.set_defaults(func=cmd_sde_status)

    p_update = sub.add_parser("update", help="download and index the latest SDE")
    pinned = p_update.add_mutually_exclusive_group()
    pinned.add_argument("--release", help="pin a specific SDE release id, "
                        "for example 20261120T165826Z")
    pinned.add_argument("--build", type=int, help="pin a build number; resolves "
                        "to the newest retained release with that build")
    p_update.add_argument("--force", action="store_true", help="rebuild even if cached")
    p_update.set_defaults(func=cmd_sde_update)

    p_env = sub.add_parser("env", help="manage the dogma-engine installation")
    p_env.add_argument("action", choices=["update"])
    p_env.set_defaults(func=cmd_env_update)

    p_doctor = sub.add_parser("doctor", help="print environment diagnostics")
    p_doctor.set_defaults(func=cmd_doctor)

    p_search = sub.add_parser("search", help="search type names in the SDE")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--all", action="store_true", help="include unpublished types")
    p_search.set_defaults(func=cmd_search)

    p_ship = sub.add_parser("ship", help="show a ship card (slots, resources, drones)")
    p_ship.add_argument("query")
    p_ship.set_defaults(func=cmd_ship)

    p_attrs = sub.add_parser("attrs", help="show dogma attributes of a type")
    p_attrs.add_argument("type")
    p_attrs.add_argument("--all", action="store_true", help="include zero values and effects")
    p_attrs.add_argument("--exact", action="store_true")
    p_attrs.set_defaults(func=cmd_attrs)

    p_val = sub.add_parser("validate", help="validate an EFT fit with all skills at 5")
    p_val.add_argument("file", help="EFT file, or - for stdin")
    p_val.add_argument("--json", action="store_true")
    p_val.add_argument("--eft-only", action="store_true", help="print only the EFT block")
    p_val.add_argument("--profile", choices=["em", "thermal", "kinetic", "explosive"], help="score EHP against a single damage type; adapts a Reactive Armor Hardener")
    p_hit = sub.add_parser("hit", help="turret hit chance and applied DPS by orbit radius")
    p_hit.add_argument("--fit", help="EFT file (or -) to read all-V tracking, range, speed and DPS from")
    p_hit.add_argument("--tracking", type=float, help="turret tracking in rad/s; overrides --fit")
    p_hit.add_argument("--sigres", type=float, help="turret signature resolution in m; overrides --fit")
    p_hit.add_argument("--target-sig", type=float, required=True, help="target signature radius in m")
    p_hit.add_argument("--optimal", type=float, help="optimal range in m after ammo and skills; overrides --fit")
    p_hit.add_argument("--falloff", type=float, help="falloff in m after skills; overrides --fit")
    p_hit.add_argument("--speed", type=float, help="orbiting ship all-V max velocity in m/s; overrides --fit")
    p_hit.add_argument("--dps", type=float, default=0.0, help="paper DPS to apply the hit chance to")
    p_hit.add_argument("--target-ehp", type=float, default=0.0, help="target effective HP, for TTK")
    p_hit.add_argument("--orbit", type=float, default=0.0, help="single real orbit radius in m")
    p_hit.add_argument("--sweep", help="START:END:STEP real orbit radii, e.g. 500:3500:500")
    p_hit.add_argument("--offset", type=float, default=None, help="real orbit minus configured orbit")
    p_hit.add_argument("--prop", choices=["ab", "mwd"], help="frigate default offset: ab=+1000 m, mwd=+3000 m")
    p_hit.set_defaults(func=cmd_hit)
    p_val.set_defaults(func=cmd_validate)

    p_names = sub.add_parser("checknames", help="check EFT item names against the SDE")
    p_names.add_argument("file", help="EFT file, or - for stdin")
    p_names.set_defaults(func=cmd_checknames)

    p_yt = sub.add_parser("youtube", help="read fits from EVE YouTube videos")
    yt_sub = p_yt.add_subparsers(dest="yt_action", required=True)

    p_yi = yt_sub.add_parser("info", help="video metadata, chapters and comment count")
    p_yi.add_argument("url")
    p_yi.add_argument("--comments", type=int, default=40, help="comments to fetch (0 = none)")
    p_yi.add_argument("--cookies", help="cookie file for age/region restricted videos")
    p_yi.add_argument("--refresh", action="store_true", help="ignore cached metadata")
    p_yi.add_argument("--from-json", help="read saved metadata instead of the network")
    p_yi.add_argument("--save", help="write the metadata JSON to this path")
    p_yi.add_argument("--json", action="store_true")
    p_yi.set_defaults(func=cmd_youtube)

    p_yf = yt_sub.add_parser("fits", help="extract EFT fits from description and comments")
    p_yf.add_argument("url")
    p_yf.add_argument("--comments", type=int, default=40)
    p_yf.add_argument("--cookies")
    p_yf.add_argument("--refresh", action="store_true")
    p_yf.add_argument("--from-json", help="read saved metadata instead of the network")
    p_yf.add_argument("--out", help="write each candidate as a .eft file in this directory")
    p_yf.add_argument("--json", action="store_true")
    p_yf.set_defaults(func=cmd_youtube)

    p_yd = yt_sub.add_parser("download", help="download the video at low resolution")
    p_yd.add_argument("url")
    p_yd.add_argument("--out", required=True)
    p_yd.add_argument("--height", type=int, default=480)
    p_yd.add_argument("--cookies")
    p_yd.set_defaults(func=cmd_youtube)

    p_yfr = yt_sub.add_parser("frames", help="extract frames and contact sheets")
    p_yfr.add_argument("source", help="video URL, or a local video file")
    p_yfr.add_argument("--out", required=True)
    p_yfr.add_argument("--scene", type=float, default=0.25, help="scene-change threshold (0-1)")
    p_yfr.add_argument("--interval", type=float, help="sample every N seconds instead of scenes")
    p_yfr.add_argument("--at", action="append", metavar="TIME",
                       help="exact timestamp (mm:ss); repeat for several frames")
    p_yfr.add_argument("--max", type=int, default=24, help="frame cap (keep sheets small)")
    p_yfr.add_argument("--height", type=int, default=480)
    p_yfr.add_argument("--cookies")
    p_yfr.set_defaults(func=cmd_youtube)

    p_yo = yt_sub.add_parser("ocr", help="optional OCR of saved frames (needs tesseract)")
    p_yo.add_argument("images", nargs="+")
    p_yo.set_defaults(func=cmd_youtube)

    p_trust = sub.add_parser("trust", help="review and approve dogma-engine builds")
    p_trust.add_argument("args", nargs=argparse.REMAINDER,
                         help="status | prepare | approve | check | adopt")
    p_trust.set_defaults(func=cmd_trust)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
