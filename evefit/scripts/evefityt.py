"""YouTube helpers for evefit: metadata, description/comment fits, frames.

The module does not decide which fit is right. It collects evidence:
  * video metadata (description, chapters, comments);
  * EFT-looking blocks found in that text, with source and timestamp;
  * video frames and contact sheets for fits shown only on screen.

Nothing here validates game rules; run `evefit.py validate` afterwards.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

CACHE_ENV = "EVEFIT_CACHE"


def cache_root() -> Path:
    explicit = os.environ.get(CACHE_ENV)
    if explicit:
        return Path(explicit).expanduser()
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base) / "evefit"


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


# --------------------------------------------------------------------------
# yt-dlp plumbing
# --------------------------------------------------------------------------


def have_ytdlp() -> bool:
    try:
        import yt_dlp  # noqa: F401
    except Exception:
        return False
    return True


def ensure_ytdlp(auto_install: bool = True) -> None:
    if have_ytdlp():
        return
    if auto_install:
        log("evefit: installing yt-dlp (one time)")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "yt-dlp>=2024.12", "pillow>=10"],
            check=True,
        )
    if not have_ytdlp():
        raise RuntimeError(
            "yt-dlp is missing. Install it with:\n"
            f"  {sys.executable} -m pip install 'yt-dlp>=2024.12' pillow"
        )


def ensure_pillow() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except Exception:
        pass
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pillow>=10"], check=True)
        return True
    except Exception:
        return False


def ytdlp_executable() -> str:
    found = shutil.which("yt-dlp")
    if found and Path(found).stat().st_size > 0:
        return found
    sibling = Path(sys.executable).parent / "yt-dlp"
    if sibling.exists() and sibling.stat().st_size > 0:
        return str(sibling)
    ensure_ytdlp()
    return str(sibling)


def video_id(url_or_id: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|live/|embed/)([A-Za-z0-9_-]{11})", url_or_id)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    return re.sub(r"[^A-Za-z0-9_-]+", "_", url_or_id)[:60]


def _trim(info: dict) -> dict:
    """Keep the fields fits need; full yt-dlp info JSON is huge."""
    keys = (
        "id", "title", "channel", "channel_url", "uploader", "uploader_url",
        "upload_date", "duration", "description", "chapters", "view_count",
        "like_count", "webpage_url", "tags",
    )
    out = {k: info.get(k) for k in keys if info.get(k) is not None}
    comments = []
    for c in info.get("comments") or []:
        comments.append({
            "author": c.get("author"),
            "text": c.get("text"),
            "like_count": c.get("like_count"),
            "parent": c.get("parent"),
            "timestamp": c.get("timestamp"),
            "time_text": c.get("time_text"),
            "is_favorited": c.get("is_favorited"),
        })
    out["comments"] = comments
    return out


def fetch_info(url: str, comments: int = 40, cookies: Path | None = None,
               refresh: bool = False) -> dict:
    """Return trimmed metadata for one video, cached under the evefit cache."""
    vid = video_id(url)
    store = cache_root() / "youtube"
    store.mkdir(parents=True, exist_ok=True)
    path = store / f"{vid}.json"
    if path.exists() and not refresh:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if len(data.get("comments") or []) >= min(comments, 1) and data.get("description") is not None:
                log(f"evefit: using cached metadata {path} (use --refresh to refetch)")
                return data
        except Exception:
            pass
    ensure_ytdlp()
    import yt_dlp

    opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "getcomments": comments > 0,
        "extractor_args": {
            "youtube": {
                "comment_sort": ["top"],
                "max_comments": [str(max(comments, 1))],
            }
        },
    }
    if cookies:
        opts["cookiefile"] = str(cookies)
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    data = _trim(info or {})
    data["url"] = data.get("webpage_url") or url
    data["fetched"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if comments <= 0:
        data.pop("comments", None)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


# --------------------------------------------------------------------------
# Text fit extraction
# --------------------------------------------------------------------------

HEADER_RE = re.compile(r"^\s*\[(?P<ship>[^\[\],]{2,60}),\s*(?P<name>[^\[\]]{0,60})\]\s*$")
TIME_RE = re.compile(r"(?<!\d)(\d{1,2}):([0-5]\d)(?::([0-5]\d))?(?!\d)")
CHAPTER_LINE_RE = re.compile(r"^\s*(\d{1,2}:[0-5]\d(?::[0-5]\d)?)\s*[-–—:|]?\s*(.*)$")
STACK_PREFIX_RE = re.compile(r"^\s*(\d{1,2})\s*[x×]\s+(.+)$", re.I)
STACK_SUFFIX_RE = re.compile(r"^\s*(.+?)\s+[x×]\s*(\d{1,2})\s*$", re.I)


def parse_timestamp(text: str) -> int | None:
    m = TIME_RE.search(text or "")
    if not m:
        return None
    h, mnt, sec = m.group(1), m.group(2), m.group(3)
    if sec is None:
        return int(h) * 60 + int(mnt)
    return int(h) * 3600 + int(mnt) * 60 + int(sec)


def fmt_timestamp(seconds: int | float | None) -> str:
    if seconds is None:
        return "?"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def _is_item_line(line: str) -> bool:
    raw = line.strip()
    if not raw or len(raw) > 90:
        return False
    text = re.sub(r"^[-*•·–—>]+\s*", "", raw).strip()
    if not text or text.startswith(("http", "www.", "#", "//")):
        return False
    if "://" in text or text.startswith("["):
        return False
    if re.match(r"^\d{1,2}:\d{2}", text):
        return False
    if not re.search(r"[A-Za-z]", text):
        return False
    if text.endswith((".", "!", "?")) and len(text.split()) > 4:
        return False
    if re.match(r"^(module|modules|high|mid|medium|low|rigs?|drones?|cargo|implants?|"
                r"fit|eft|skills?|notes?|cost|price|link|source)\s*:?$", text, re.I):
        return False
    return True


def normalize_stack(line: str) -> list[str]:
    """Turn `3x Hammerhead II` / `Hammerhead II x3` into repeated EFT lines."""
    text = line.strip()
    m = STACK_PREFIX_RE.match(text)
    if not m:
        m = STACK_SUFFIX_RE.match(text)
        if m:
            count, name = int(m.group(2)), m.group(1)
        else:
            return [text]
    else:
        count, name = int(m.group(1)), m.group(2)
    if count < 2 or count > 8:
        return [text]
    return [name.strip()] * count


def extract_fit_blocks(text: str) -> list[dict]:
    """Find EFT-shaped blocks in free text (description or one comment)."""
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    fits: list[dict] = []
    i = 0
    while i < len(lines):
        m = HEADER_RE.match(lines[i])
        if not m:
            i += 1
            continue
        items: list[str] = []
        blanks = 0
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if HEADER_RE.match(line):
                break
            if not line.strip():
                blanks += 1
                if blanks >= 3:
                    break
                j += 1
                continue
            blanks = 0
            if line.lstrip().startswith("```"):
                break
            if not _is_item_line(line):
                break
            cleaned = re.sub(r"^[-*•·–—>]+\s*", "", line.strip())
            items.extend(normalize_stack(cleaned))
            j += 1
        if items:
            fits.append({
                "ship": m.group("ship").strip(),
                "name": m.group("name").strip() or "YouTube fit",
                "items": items,
                "eft": "\n".join([f"[{m.group('ship').strip()}, {m.group('name').strip() or 'YouTube fit'}]"] + items),
                "line": i,
            })
        i = max(j, i + 1)
    return fits


def description_chapters(description: str) -> list[dict]:
    chapters = []
    for idx, line in enumerate((description or "").split("\n")):
        m = CHAPTER_LINE_RE.match(line)
        if m:
            chapters.append({
                "line": idx,
                "seconds": parse_timestamp(m.group(1)),
                "title": (m.group(2) or "").strip(),
            })
    return chapters


def fits_from_metadata(data: dict) -> list[dict]:
    """Extract fits from description and comments, annotating their origin."""
    out: list[dict] = []
    desc = data.get("description") or ""
    desc_chapters = description_chapters(desc)
    for fit in extract_fit_blocks(desc):
        near = [c for c in desc_chapters if c["line"] <= fit["line"]]
        if near:
            fit["timestamp"] = near[-1]["seconds"]
            fit["chapter"] = near[-1]["title"]
        fit["source"] = "description"
        fit["url"] = data.get("url")
        fit["channel"] = data.get("channel")
        fit["video_title"] = data.get("title")
        out.append(fit)
    for idx, comment in enumerate(data.get("comments") or []):
        text = comment.get("text") or ""
        for fit in extract_fit_blocks(text):
            fit["source"] = "comment"
            fit["author"] = comment.get("author")
            fit["comment_like_count"] = comment.get("like_count")
            fit["timestamp"] = parse_timestamp(text) or comment.get("timestamp")
            time_text = comment.get("time_text") or ""
            if time_text and not fit.get("timestamp"):
                fit["timestamp"] = parse_timestamp(time_text)
            fit["url"] = data.get("url")
            fit["channel"] = data.get("channel")
            fit["video_title"] = data.get("title")
            out.append(fit)
    seen = set()
    unique = []
    for fit in out:
        key = re.sub(r"\s+", " ", fit["eft"].lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(fit)
    return unique


# --------------------------------------------------------------------------
# Frames
# --------------------------------------------------------------------------


def ffmpeg_bin() -> str | None:
    return shutil.which("ffmpeg")


def ffprobe_duration(path: Path) -> float | None:
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    res = subprocess.run(
        [exe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(res.stdout.strip())
    except Exception:
        return None


def download_video(url: str, out_dir: Path, height: int = 480,
                   cookies: Path | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = ytdlp_executable()
    cmd = [
        exe,
        "-f", f"bv*[height<={height}]+ba/b[height<={height}]/b",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--quiet", "--no-warnings",
        "-o", str(out_dir / "video.%(ext)s"),
    ]
    if cookies:
        cmd += ["--cookies", str(cookies)]
    cmd.append(url)
    log(f"evefit: downloading video (<= {height}p) with yt-dlp")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(
            "yt-dlp could not download the video:\n"
            + (res.stderr.strip().splitlines()[-1] if res.stderr.strip() else "unknown error")
        )
    candidates = sorted(out_dir.glob("video.*"))
    if not candidates:
        raise RuntimeError(f"yt-dlp finished but no file appeared in {out_dir}")
    return candidates[0]


def _parse_showinfo(stderr: str) -> list[float]:
    times = []
    for line in stderr.splitlines():
        m = re.search(r"pts_time:([0-9.]+)", line)
        if m:
            times.append(float(m.group(1)))
    return times


def extract_frames(video: Path, out_dir: Path, scene: float = 0.25,
                   interval: float | None = None, at: list[str] | None = None,
                   max_frames: int = 24, width: int = 640) -> list[dict]:
    exe = ffmpeg_bin()
    if not exe:
        raise RuntimeError("ffmpeg is required for frame extraction and was not found on PATH")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.jpg"):
        old.unlink()
    frames: list[dict] = []
    scale = f"scale={width}:-2"

    if at:
        for stamp in at:
            seconds = parse_timestamp(stamp)
            if seconds is None:
                raise SystemExit(f"cannot parse timestamp {stamp!r} (use mm:ss or hh:mm:ss)")
            name = f"frame_{seconds:06d}.jpg"
            target = out_dir / name
            res = subprocess.run(
                [exe, "-v", "error", "-ss", str(seconds), "-i", str(video),
                 "-frames:v", "1", "-vf", scale, "-q:v", "3", "-y", str(target)],
                capture_output=True, text=True,
            )
            if res.returncode != 0 or not target.exists():
                log(f"evefit: no frame at {stamp} ({res.stderr.strip()[:200] or 'past end of video'})")
                continue
            frames.append({"path": target, "seconds": seconds})
        return frames

    if interval:
        selector = f"fps=1/{interval}"
    else:
        selector = f"select='gt(scene,{scene})'"
    vf = f"{selector},{scale},showinfo"
    times_source = True
    pattern = out_dir / "frame_%05d.jpg"
    res = subprocess.run(
        [exe, "-v", "info", "-i", str(video), "-vf", vf, "-vsync", "vfr",
         "-frames:v", str(max_frames), "-q:v", "3", "-y", str(pattern)],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise RuntimeError("ffmpeg frame extraction failed:\n" + res.stderr.strip()[-800:])
    times = _parse_showinfo(res.stderr) if times_source else []
    paths = sorted(out_dir.glob("frame_*.jpg"))
    for idx, path in enumerate(paths):
        seconds = times[idx] if idx < len(times) else (idx * interval if interval else None)
        frames.append({"path": path, "seconds": seconds})
    return frames


def build_sheets(frames: list[dict], out_dir: Path, cols: int = 3,
                 cell=(480, 270)) -> list[Path]:
    """Build labelled contact sheets (3x3 by default) to limit image count."""
    if not frames:
        return []
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return _sheets_with_ffmpeg(frames, out_dir, cols)
    per = cols * cols
    sheets: list[Path] = []
    for page in range(0, len(frames), per):
        chunk = frames[page:page + per]
        rows = (len(chunk) + cols - 1) // cols
        canvas = Image.new("RGB", (cell[0] * cols, cell[1] * rows), (12, 12, 12))
        draw = ImageDraw.Draw(canvas)
        for idx, frame in enumerate(chunk):
            img = Image.open(frame["path"]).convert("RGB")
            img.thumbnail(cell)
            x = (idx % cols) * cell[0]
            y = (idx // cols) * cell[1]
            canvas.paste(img, (x, y))
            label = f"{page + idx + 1}  {fmt_timestamp(frame.get('seconds'))}"
            draw.rectangle([x, y, x + 110, y + 16], fill=(0, 0, 0))
            draw.text((x + 3, y + 3), label, fill=(255, 235, 120))
        path = out_dir / f"sheet_{page // per + 1:02d}.jpg"
        canvas.save(path, quality=88)
        sheets.append(path)
    return sheets


def _sheets_with_ffmpeg(frames: list[dict], out_dir: Path, cols: int) -> list[Path]:
    exe = ffmpeg_bin()
    if not exe:
        return []
    per = cols * cols
    sheets = []
    for page in range(0, len(frames), per):
        chunk = frames[page:page + per]
        tmp = out_dir / f".sheet_seq_{page}"
        tmp.mkdir(exist_ok=True)
        for idx, frame in enumerate(chunk):
            shutil.copy(frame["path"], tmp / f"{idx:03d}.jpg")
        out = out_dir / f"sheet_{page // per + 1:02d}.jpg"
        subprocess.run(
            [exe, "-v", "error", "-pattern_type", "glob", "-i", str(tmp / "*.jpg"),
             "-filter_complex", f"tile={cols}x{cols}", "-frames:v", "1", "-y", str(out)],
            check=False,
        )
        shutil.rmtree(tmp, ignore_errors=True)
        if out.exists():
            sheets.append(out)
    return sheets


def ocr_image(path: Path) -> str:
    try:
        import pytesseract  # noqa: F401
        from PIL import Image
    except Exception as exc:
        raise RuntimeError(
            "OCR is unavailable (needs the `tesseract` binary plus `pytesseract` and "
            f"`pillow` in this interpreter): {exc}"
        )
    import pytesseract
    from PIL import Image

    return pytesseract.image_to_string(Image.open(path))
