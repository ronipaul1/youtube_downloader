"""Helpers to download YouTube audio as MP3 using yt-dlp.

Functions are import-safe for reuse in the web app.
"""
import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Tuple
from zipfile import ZipFile, ZIP_DEFLATED
from yt_dlp import YoutubeDL


def _safe_name(name: str, fallback: str = "playlist") -> str:
    sanitized = re.sub(r'[<>:"/\\\\|?*]+', "_", name).strip()
    return sanitized or fallback


def _prepare_cookiefile(cookie_path: str | None) -> str | None:
    """Ensure cookie file is Netscape format; convert JSON export if needed."""
    if not cookie_path:
        return None
    path = Path(cookie_path)
    if path.suffix.lower() != ".json":
        return cookie_path

    data = json.loads(path.read_text(encoding="utf-8"))
    cookies = data.get("cookies") if isinstance(data, dict) else data
    if not isinstance(cookies, list):
        raise RuntimeError("Cookie JSON not understood; expected a list or a dict with 'cookies'")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    lines = []
    for c in cookies:
        domain = c.get("domain", "")
        include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
        pathv = c.get("path", "/")
        secure = "TRUE" if c.get("secure", False) else "FALSE"
        expires = int(c.get("expirationDate", c.get("expires", 0)) or 0)
        name = c.get("name", "")
        value = c.get("value", "")
        lines.append(f"{domain}\t{include_subdomains}\t{pathv}\t{secure}\t{expires}\t{name}\t{value}\n")
    tmp.write("".join(lines).encode("utf-8"))
    tmp.flush()
    return tmp.name


def _common_opts(outdir: Path, ignore_errors: bool = False) -> Tuple[dict, str, str]:
    ffmpeg_location = os.getenv("FFMPEG_PATH")
    cookies_file = os.getenv("YT_COOKIES_FILE")
    if not cookies_file:
        default_txt = Path(__file__).parent / "YT_COOKIES_FILE.txt"
        if default_txt.exists():
            cookies_file = str(default_txt)
    cookies_from_browser = os.getenv("YT_COOKIES_BROWSER")
    proxy = os.getenv("YTDLP_PROXY")  # optional HTTP/HTTPS proxy, e.g. http://127.0.0.1:7890
    cookiefile_resolved = _prepare_cookiefile(cookies_file)
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(outdir / "%(title)s.%(ext)s"),
        "ignoreerrors": ignore_errors,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    if ffmpeg_location:
        opts["ffmpeg_location"] = ffmpeg_location
    if cookiefile_resolved:
        opts["cookiefile"] = cookiefile_resolved
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)
    if proxy:
        opts["proxy"] = proxy
    return opts


def download_audio(url: str, outdir: Path) -> Path:
    """Download the given video URL as an MP3 file into outdir.

    Returns the Path to the saved MP3.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    ffmpeg_location = os.getenv("FFMPEG_PATH")  # optional override
    opts = _common_opts(outdir, ignore_errors=False)
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise RuntimeError("yt-dlp returned no info (download may have failed).")
        base = Path(ydl.prepare_filename(info))
    return base.with_suffix(".mp3")


def download_audio_playlist(url: str, outdir: Path) -> Path:
    """Download an entire playlist as mp3s and return the zip path."""
    outdir.mkdir(parents=True, exist_ok=True)
    # temp staging to avoid partials in output folder
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        opts = _common_opts(tmp, ignore_errors=True)
        # keep playlist structure inside temp
        opts["outtmpl"] = str(tmp / "%(playlist_title)s/%(title)s.%(ext)s")
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            playlist_title = info.get("title") or "playlist"

        exts = {".mp3", ".m4a", ".opus", ".webm"}
        files = [p for p in tmp.rglob("*") if p.is_file() and p.suffix.lower() in exts]
        if not files:
            raise RuntimeError("No audio files were downloaded from the playlist (yt-dlp may have failed or needs cookies).")

        zip_name = _safe_name(playlist_title) + ".zip"
        zip_path = outdir / zip_name
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, arcname=f.relative_to(tmp))
        return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download YouTube audio as MP3")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--outdir",
        default=Path("downloads/audio"),
        type=Path,
        help="Output directory (default: downloads/audio)",
    )
    args = parser.parse_args()
    dest = download_audio(args.url, args.outdir)
    print(f"Saved: {dest}")


if __name__ == "__main__":
    main()
