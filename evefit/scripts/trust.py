#!/usr/bin/env python3
"""Trust gate for eveshipfit-dogma-engine and its SDE data package.

Policy: no package code is installed or imported until its exact wheel and the
public source it was built from have been reviewed and recorded. Every version
or wheel change invalidates the record and requires a fresh review.

This module never imports the package under review. It downloads wheels with
plain urllib (no build hooks run), hashes them, unpacks them as zip archives,
and compares the installed files against the verified wheel.

Commands:
    status
    prepare [--version V] [--sde-version V]
    approve --version V --notes TEXT [--ack-findings]
    check [--require-install]
    adopt --notes TEXT        record the currently installed files (needs review)
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

PACKAGE = "eveshipfit-dogma-engine"
SDE_PACKAGE = "eveshipfit-sde"
REPO = "https://github.com/EVEShipFit/dogma-engine"

SHIPPED_PREFIXES = (
    "crates/esf-python/",
    "crates/esf-data/",
    "crates/esf-format/",
    "crates/esf-dogma-engine/",
)


class TrustError(RuntimeError):
    pass


def cache_root() -> Path:
    explicit = os.environ.get("EVEFIT_CACHE")
    if explicit:
        return Path(explicit).expanduser()
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "evefit"


def trust_dir() -> Path:
    path = cache_root() / "trust"
    path.mkdir(parents=True, exist_ok=True)
    return path


def approved_path() -> Path:
    return trust_dir() / "approved.json"


def pending_path() -> Path:
    return trust_dir() / "pending.json"


def wheels_dir() -> Path:
    path = trust_dir() / "wheels"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(root: Path) -> tuple[str, dict[str, str]]:
    """Content hash of a source tree plus per-file hashes."""
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith((".git/", "target/")):
            continue
        files[rel] = sha256_file(path)
    digest = hashlib.sha256()
    for rel, file_digest in files.items():
        digest.update(rel.encode() + b"\0" + file_digest.encode() + b"\n")
    return digest.hexdigest(), files


# --------------------------------------------------------------------------
# PyPI
# --------------------------------------------------------------------------


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "evefit-trust"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def latest_version(pkg: str) -> str:
    return _get_json(f"https://pypi.org/pypi/{pkg}/json")["info"]["version"]


def release_info(pkg: str, version: str) -> dict:
    return _get_json(f"https://pypi.org/pypi/{pkg}/{version}/json")


def _wheel_arch_match(filename: str) -> int:
    """Rank a wheel for this machine. 0 means unusable."""
    machine = platform.machine().lower()
    sysname = sys.platform
    name = filename
    score = 0
    if sysname.startswith("linux"):
        if "manylinux" not in name and "linux" not in name:
            return 0
    elif sysname == "win32":
        if "win_amd64" not in name and "win32" not in name:
            return 0
        return 3 if ("win_amd64" in name and machine in ("amd64", "x86_64")) else 1
    elif sysname == "darwin":
        if "macosx" not in name:
            return 0
        if machine in ("arm64", "aarch64"):
            return 3 if ("arm64" in name or "universal2" in name) else 0
        return 3 if ("x86_64" in name or "universal2" in name) else 0
    else:
        return 0
    if machine in ("x86_64", "amd64"):
        score = 3 if ("x86_64" in name or "amd64" in name) else 0
    elif machine in ("aarch64", "arm64"):
        score = 3 if ("aarch64" in name or "arm64" in name) else 0
    if "abi3" in name:
        score += 1
    return score


def pick_wheel(pkg: str, version: str) -> dict:
    info = release_info(pkg, version)
    candidates = []
    for file in info.get("urls", []):
        if not file["filename"].endswith(".whl"):
            continue
        if "none-any" in file["filename"]:
            score = 5
        else:
            score = _wheel_arch_match(file["filename"])
        if score:
            candidates.append((score, file))
    if not candidates:
        raise TrustError(
            f"no wheel of {pkg} {version} for {platform.machine()} / {sys.platform}"
        )
    candidates.sort(key=lambda item: -item[0])
    file = candidates[0][1]
    return {
        "filename": file["filename"],
        "url": file["url"],
        "sha256": file["digests"]["sha256"],
        "size": file["size"],
        "upload_time": file.get("upload_time"),
    }


def fetch_wheel(entry: dict) -> Path:
    target = wheels_dir() / entry["filename"]
    if target.exists() and sha256_file(target) == entry["sha256"]:
        return target
    tmp = target.with_suffix(".part")
    req = urllib.request.Request(entry["url"], headers={"User-Agent": "evefit-trust"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    digest = sha256_file(tmp)
    if digest != entry["sha256"]:
        tmp.unlink(missing_ok=True)
        raise TrustError(
            f"wheel hash mismatch for {entry['filename']}: got {digest}, "
            f"PyPI says {entry['sha256']}"
        )
    tmp.replace(target)
    return target


# --------------------------------------------------------------------------
# Source
# --------------------------------------------------------------------------


def github_tag(version: str) -> dict:
    tags = _get_json(f"https://api.github.com/repos/EVEShipFit/dogma-engine/tags?per_page=100")
    for tag in tags:
        if tag["name"] in (f"v{version}", version):
            return {"tag": tag["name"], "commit": tag["commit"]["sha"]}
    raise TrustError(f"no GitHub tag v{version} in {REPO}")


def fetch_source(version: str, tag: str) -> Path:
    root = trust_dir() / "review" / f"{PACKAGE}-{version}"
    src = root / "source"
    if (src / "Cargo.toml").exists():
        return src
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "source.tar.gz"
    url = f"https://codeload.github.com/EVEShipFit/dogma-engine/tar.gz/refs/tags/{tag}"
    req = urllib.request.Request(url, headers={"User-Agent": "evefit-trust"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(archive, "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    with tarfile.open(archive) as tar:
        members = []
        for member in tar.getmembers():
            if member.name.startswith("/") or ".." in Path(member.name).parts:
                raise TrustError(f"unsafe path in source archive: {member.name}")
            members.append(member)
        try:
            tar.extractall(root, members=members, filter="data")
        except TypeError:
            tar.extractall(root, members=members)
    extracted = [p for p in root.iterdir() if p.is_dir() and p.name.startswith("dogma-engine-")]
    if not extracted:
        raise TrustError("source archive did not contain the repository")
    extracted[0].rename(src)
    return src


# --------------------------------------------------------------------------
# Static scan
# --------------------------------------------------------------------------

SCAN_RULES = [
    (r"\bCommand::new\b", "high", "spawns a process"),
    (r"\bstd::process\b", "high", "process API"),
    (r"\bos\.system\b", "high", "shell execution"),
    (r"\bsubprocess\.", "high", "subprocess execution"),
    (r"\beval\s*\(", "high", "dynamic code execution"),
    (r"\bexec\s*\(", "high", "dynamic code execution"),
    (r"\b__import__\s*\(", "high", "dynamic import"),
    (r"\bctypes\b", "high", "native FFI"),
    (r"\bTcpStream\b|\bUdpSocket\b|\bstd::net\b", "high", "network sockets"),
    (r"\breqwest\b|\bureq\b|\bhyper\b", "high", "HTTP client"),
    (r"https?://[^\s\"']+", "low", "URL literal"),
    (r"\bopenssl\b|\bnative-tls\b", "medium", "TLS dependency"),
    (r"\binclude_bytes!\s*\(", "medium", "embedded binary blob"),
    (r"\bstd::fs::write\b|\bFile::create\b", "medium", "writes files"),
    (r"\bset_permissions\b|\bchmod\b", "high", "changes permissions"),
    (r"\bdirs::home_dir\b|\bstd::env::var\b", "low", "reads environment/home"),
    (r"AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----", "high", "credential-like literal"),
]
SCAN_RE = [(re.compile(rx), sev, label) for rx, sev, label in SCAN_RULES]
TEXT_SUFFIXES = {".py", ".rs", ".toml", ".yml", ".yaml", ".json", ".txt", ".md", ".sh", ".ps1"}
SKIP_SCAN = ("/target/", "/fuzz/", "/tests/", "Cargo.lock", "package-lock.json")


def scan_text_tree(root: Path) -> list[dict]:
    findings: list[dict] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in f"/{rel}" for part in SKIP_SCAN):
            continue
        shipped = any(rel.startswith(prefix) for prefix in SHIPPED_PREFIXES)
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for lineno, line in enumerate(lines, 1):
            for regex, severity, label in SCAN_RE:
                if regex.search(line):
                    if severity == "low" and not shipped:
                        continue
                    if shipped and label == "URL literal":
                        pass
                    findings.append({
                        "severity": severity if shipped else "info",
                        "label": label,
                        "path": rel,
                        "line": lineno,
                        "excerpt": line.strip()[:160],
                    })
    return findings


def scan_wheel(root: Path) -> list[dict]:
    findings: list[dict] = []
    patterns = [
        (b"https://", "low", "URL in wheel"),
        (b"http://", "low", "URL in wheel"),
        (b"/bin/sh", "high", "shell path"),
        (b"powershell", "high", "PowerShell string"),
        (b"curl ", "high", "curl invocation"),
        (b"wget ", "high", "wget invocation"),
    ]
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                for regex, severity, label in SCAN_RE:
                    if regex.search(line) and severity != "low":
                        findings.append({
                            "severity": severity, "label": label, "path": rel,
                            "line": lineno, "excerpt": line.strip()[:160],
                        })
            continue
        data = path.read_bytes()
        for token, severity, label in patterns:
            if token in data:
                findings.append({
                    "severity": severity, "label": label, "path": rel,
                    "line": 0, "excerpt": f"binary contains {token.decode(errors='replace')!r}",
                })
    return findings


def summarize(findings: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding["severity"]] = counts.get(finding["severity"], 0) + 1
    return counts


# --------------------------------------------------------------------------
# Prepare / approve
# --------------------------------------------------------------------------


def _unpack_wheel(wheel: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    marker = dest / ".unpacked"
    if marker.exists():
        return
    with zipfile.ZipFile(wheel) as zf:
        for member in zf.infolist():
            if member.filename.startswith("/") or ".." in Path(member.filename).parts:
                raise TrustError(f"unsafe path in wheel: {member.filename}")
            zf.extract(member, dest)
    marker.write_text("ok", encoding="utf-8")


def prepare(engine_version: str | None = None, sde_version: str | None = None) -> dict:
    engine_version = engine_version or latest_version(PACKAGE)
    sde_version = sde_version or latest_version(SDE_PACKAGE)
    print(f"preparing {PACKAGE} {engine_version} and {SDE_PACKAGE} {sde_version}")

    engine_wheel = pick_wheel(PACKAGE, engine_version)
    sde_wheel = pick_wheel(SDE_PACKAGE, sde_version)
    engine_path = fetch_wheel(engine_wheel)
    sde_path = fetch_wheel(sde_wheel)
    print(f"wheel verified: {engine_wheel['filename']} {engine_wheel['sha256']}")
    print(f"wheel verified: {sde_wheel['filename']} {sde_wheel['sha256']}")

    tag = github_tag(engine_version)
    src = fetch_source(engine_version, tag["tag"])
    digest, files = tree_hash(src)
    print(f"source: {tag['tag']} commit {tag['commit']} tree {digest[:16]}")

    review = trust_dir() / "review" / f"{PACKAGE}-{engine_version}"
    wheel_root = review / "wheel"
    _unpack_wheel(engine_path, wheel_root)

    source_findings = scan_text_tree(src)
    wheel_findings = scan_wheel(wheel_root)
    findings = source_findings + wheel_findings

    previous = load_json(approved_path())
    changes = None
    if previous and previous.get("source", {}).get("files"):
        old = previous["source"]["files"]
        added = sorted(set(files) - set(old))
        removed = sorted(set(old) - set(files))
        modified = sorted(p for p in set(files) & set(old) if files[p] != old[p])
        changes = {"added": added, "removed": removed, "modified": modified}
        print(f"changes vs approved {previous.get('version')}: "
              f"{len(added)} added, {len(modified)} modified, {len(removed)} removed")
        for label, items in (("added", added), ("modified", modified), ("removed", removed)):
            for item in items[:40]:
                print(f"  {label}: {item}")
        if len(added) + len(modified) + len(removed) > 40:
            print("  ...")

    print("\nscan findings:")
    if not findings:
        print("  none")
    for finding in findings:
        loc = f"{finding['path']}:{finding['line']}" if finding["line"] else finding["path"]
        print(f"  [{finding['severity']}] {loc}: {finding['label']} | {finding['excerpt']}")
    counts = summarize(findings)
    print("counts:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none")

    pending = {
        "package": PACKAGE,
        "version": engine_version,
        "prepared_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine_wheel": {**engine_wheel, "path": str(engine_path)},
        "sde": {
            "version": sde_version,
            **sde_wheel,
            "path": str(sde_path),
        },
        "source": {
            "repo": REPO,
            "tag": tag["tag"],
            "commit": tag["commit"],
            "tree_sha256": digest,
            "files": files,
        },
        "changes_from_approved": changes,
        "findings": findings,
        "finding_counts": counts,
    }
    save_json(pending_path(), pending)
    print(f"\nreport written to {pending_path()}")
    print("Review the source and the findings. Only then run:")
    print(f'  python3 scripts/trust.py approve --version {engine_version} '
          f'--notes "what you reviewed and why it is acceptable"')
    return pending


def approve(version: str, notes: str, ack_findings: bool = False) -> dict:
    pending = load_json(pending_path())
    if not pending or pending.get("version") != version:
        raise TrustError(
            f"no prepared report for {version}; run `trust.py prepare --version {version}` first"
        )
    if not notes or len(notes.strip()) < 10:
        raise TrustError("approval needs review notes (at least 10 characters)")
    high = [f for f in pending.get("findings", []) if f["severity"] == "high"]
    if high and not ack_findings:
        raise TrustError(
            f"{len(high)} high-severity finding(s) present; resolve them or pass "
            "--ack-findings with an explanation in --notes"
        )
    record = {
        **pending,
        "approved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "review_notes": notes.strip(),
        "findings_acknowledged": bool(high),
    }
    save_json(approved_path(), record)
    pending_path().unlink(missing_ok=True)
    print(f"approved {PACKAGE} {version} ({pending['engine_wheel']['sha256'][:16]})")
    return record


# --------------------------------------------------------------------------
# Installed state
# --------------------------------------------------------------------------

_PROBE = (
    "import importlib.metadata as m, json, sys;"
    "out={};\n"
    "for name in ('%s','%s'):\n"
    " try:\n"
    "  d=m.distribution(name); out[name]={'version':d.version,'root':str(d.locate_file(''))}\n"
    " except Exception: out[name]=None\n"
    "print(json.dumps(out))"
) % (PACKAGE, SDE_PACKAGE)


def installed_info(py: Path) -> dict:
    if not Path(py).exists():
        return {}
    res = subprocess.run([str(py), "-c", _PROBE], capture_output=True, text=True)
    if res.returncode != 0:
        return {}
    try:
        data = json.loads(res.stdout)
    except Exception:
        return {}
    return {k: v for k, v in data.items() if v}


def _wheel_files(root: Path) -> dict[str, str]:
    files = {}
    dist = next(root.glob("*.dist-info"), None)
    if not dist:
        raise TrustError(f"no dist-info in {root}")
    record = dist / "RECORD"
    for line in record.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rel, digest = (line.split(",") + ["", ""])[:2]
        if not digest.startswith("sha256="):
            continue
        files[rel] = digest.split("=", 1)[1]
    return files


def _b64_digest(path: Path) -> str:
    import base64

    return base64.urlsafe_b64encode(hashlib.sha256(path.read_bytes()).digest()).decode().rstrip("=")


def verify_installed(py: Path, record: dict | None = None) -> tuple[bool, list[str]]:
    record = record or load_json(approved_path())
    if not record:
        return False, ["no approved trust record"]
    info = installed_info(py)
    problems: list[str] = []
    for key, pkg in (("engine_wheel", PACKAGE), ("sde", SDE_PACKAGE)):
        entry = record.get(key) or {}
        actual = info.get(pkg)
        if not actual:
            problems.append(f"{pkg} is not installed")
            continue
        if actual["version"] != entry.get("version") and entry.get("version"):
            problems.append(f"{pkg} installed version {actual['version']} != approved {entry['version']}")
    if problems:
        return False, problems
    for key, pkg in (("engine_wheel", PACKAGE), ("sde", SDE_PACKAGE)):
        entry = record.get(key) or {}
        path = entry.get("path")
        if not path or not Path(path).exists():
            problems.append(f"verified wheel for {pkg} is missing from the cache")
            continue
        if entry.get("sha256") and sha256_file(Path(path)) != entry["sha256"]:
            problems.append(f"cached wheel hash mismatch for {pkg}: {path}")
            continue
        root = trust_dir() / "review" / f"{PACKAGE}-{record['version']}" / ("wheel" if key == "engine_wheel" else "sde-wheel")
        if not root.exists():
            _unpack_wheel(Path(path), root)
        site = Path(info[pkg]["root"])
        for rel, expected in _wheel_files(root).items():
            target = site / rel
            if not target.exists():
                if rel.endswith(("RECORD", "INSTALLER", "REQUESTED", "direct_url.json")):
                    continue
                problems.append(f"missing installed file: {rel}")
                continue
            if _b64_digest(target) != expected:
                problems.append(f"hash mismatch: {rel}")
    return (not problems), problems


def require_approved() -> dict:
    record = load_json(approved_path())
    if not record:
        raise TrustError(
            "dogma-engine has no approved trust record.\n"
            "  1. python3 scripts/trust.py prepare\n"
            "  2. review the printed findings and the source at the printed commit\n"
            "  3. python3 scripts/trust.py approve --version <version> --notes \"...\""
        )
    return record


def install_approved(py: Path) -> dict:
    record = require_approved()
    entries = [record["engine_wheel"], record["sde"]]
    for entry in entries:
        path = Path(entry["path"])
        if not path.exists() or sha256_file(path) != entry["sha256"]:
            fetch_wheel(entry)
    engine_path = Path(record["engine_wheel"]["path"])
    sde_path = Path(record["sde"]["path"])
    print(f"installing verified wheels: {engine_path.name}, {sde_path.name}")
    subprocess.run(
        [str(py), "-m", "pip", "install", "-q", "--no-cache-dir", str(engine_path), str(sde_path)],
        check=True,
    )
    ok, problems = verify_installed(py, record)
    if not ok:
        raise TrustError("installation does not match the approved files:\n  " + "\n  ".join(problems))
    return record


def ensure_trusted(py: Path) -> dict:
    record = require_approved()
    info = installed_info(py)
    if PACKAGE not in info:
        return install_approved(py)
    sde_info = info.get(SDE_PACKAGE) or {}
    if info[PACKAGE].get("version") != record.get("version") or \
            sde_info.get("version") != (record.get("sde") or {}).get("version"):
        print(f"evefit: installing approved {record['version']} instead of "
              f"{info[PACKAGE].get('version')}")
        return install_approved(py)
    ok, problems = verify_installed(py, record)
    if not ok:
        raise TrustError(
            "installed dogma-engine does not match the approved build:\n  "
            + "\n  ".join(problems)
            + "\nRun `python3 scripts/trust.py status`, then prepare and approve the new build."
        )
    return record


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def cmd_status(_args) -> None:
    record = load_json(approved_path())
    pending = load_json(pending_path())
    print(f"trust store: {trust_dir()}")
    if record:
        print(f"approved: {PACKAGE} {record['version']} "
              f"({record['engine_wheel']['sha256'][:16]}) + {SDE_PACKAGE} {record['sde']['version']}")
        print(f"  source: {record['source']['tag']} commit {record['source']['commit'][:12]}")
        print(f"  approved: {record['approved_at']} | notes: {record['review_notes']}")
    else:
        print("approved: none")
    if pending:
        print(f"pending review: {pending['version']} prepared {pending['prepared_at']}")
        print("  approve with: python3 scripts/trust.py approve --version "
              f"{pending['version']} --notes \"...\"")
    try:
        latest = latest_version(PACKAGE)
        if record and latest != record["version"]:
            print(f"update available: {latest} (requires review before install)")
        elif record:
            print("up to date with PyPI")
    except Exception as exc:
        print(f"PyPI latest: unavailable ({exc})")
    venv = cache_root() / "venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    info = installed_info(py) if py.exists() else {}
    if info:
        engine = info.get(PACKAGE, {})
        print(f"installed: {PACKAGE} {engine.get('version')}")
        if record:
            ok, problems = verify_installed(py, record)
            print("installed matches approved" if ok else "installed MISMATCH:\n  " + "\n  ".join(problems))
    else:
        print("installed: not installed")


def cmd_prepare(args) -> None:
    prepare(args.version, args.sde_version)


def cmd_approve(args) -> None:
    approve(args.version, args.notes, ack_findings=args.ack_findings)


def cmd_check(args) -> None:
    record = require_approved()
    venv = cache_root() / "venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not args.require_install:
        print(f"approved record: {PACKAGE} {record['version']} ({record['engine_wheel']['sha256'][:16]})")
        return
    ensure_trusted(py)
    print("installed files match the approved build")


def cmd_adopt(args) -> None:
    """Record the currently installed files after manual review (no download)."""
    if not args.notes or len(args.notes.strip()) < 10:
        raise TrustError("adopt needs review notes")
    venv = cache_root() / "venv"
    py = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    info = installed_info(py)
    if PACKAGE not in info:
        raise TrustError("dogma-engine is not installed in the evefit venv")
    record = {
        "package": PACKAGE,
        "version": info[PACKAGE]["version"],
        "sde": {"version": info[SDE_PACKAGE]["version"] if SDE_PACKAGE in info else None},
        "source": {},
        "adopted": True,
        "approved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "review_notes": args.notes.strip(),
    }
    save_json(approved_path(), record)
    print("adopted installed files; run `trust.py prepare` before the next update")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="trust.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)

    p_prepare = sub.add_parser("prepare", help="download and scan a release for review")
    p_prepare.add_argument("--version")
    p_prepare.add_argument("--sde-version")
    p_prepare.set_defaults(func=cmd_prepare)

    p_approve = sub.add_parser("approve", help="accept a prepared release after review")
    p_approve.add_argument("--version", required=True)
    p_approve.add_argument("--notes", required=True)
    p_approve.add_argument("--ack-findings", action="store_true")
    p_approve.set_defaults(func=cmd_approve)

    p_check = sub.add_parser("check", help="verify the installed build against the record")
    p_check.add_argument("--require-install", action="store_true")
    p_check.set_defaults(func=cmd_check)

    p_adopt = sub.add_parser("adopt", help="record currently installed files after review")
    p_adopt.add_argument("--notes", required=True)
    p_adopt.set_defaults(func=cmd_adopt)

    args = parser.parse_args()
    try:
        args.func(args)
    except TrustError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
