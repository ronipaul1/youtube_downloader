"""Helpers to download YouTube audio as MP3 using yt-dlp.

Functions are import-safe for reuse in the web app.
"""
import argparse
from pathlib import Path
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


def _common_opts(outdir: Path, ignore_errors: bool = False) -> Tuple[dict, str, str]:
    ffmpeg_location = os.getenv("FFMPEG_PATH")
    cookies_file = os.getenv("YT_COOKIES_FILE")
    cookies_from_browser = os.getenv("YT_COOKIES_BROWSER")
    proxy = os.getenv("YTDLP_PROXY")  # optional HTTP/HTTPS proxy, e.g. http://127.0.0.1:7890
    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(outdir / "%(title)s.%(ext)s"),
        "ignoreerrors": True,  # keep going if some items fail (e.g., geo-blocked)
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
    if cookies_file:
        opts["cookiefile"] = cookies_file
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
