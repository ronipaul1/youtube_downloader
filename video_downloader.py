"""Helpers to download full YouTube videos using yt-dlp."""
import argparse
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Tuple
from zipfile import ZipFile, ZIP_DEFLATED
from yt_dlp import YoutubeDL

QUALITY_MAP = {
    "best": "bestvideo+bestaudio/best",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
}


def _safe_name(name: str, fallback: str = "playlist") -> str:
    sanitized = re.sub(r'[<>:"/\\\\|?*]+', "_", name).strip()
    return sanitized or fallback


def _common_opts(outdir: Path, quality: str, ignore_errors: bool = False) -> dict:
    fmt = QUALITY_MAP.get(quality, QUALITY_MAP["best"])
    ffmpeg_location = os.getenv("FFMPEG_PATH")  # optional override
    cookies_file = os.getenv("YT_COOKIES_FILE")  # optional: exported cookies.txt
    cookies_from_browser = os.getenv("YT_COOKIES_BROWSER")  # optional: e.g., "chrome"
    proxy = os.getenv("YTDLP_PROXY")  # optional HTTP/HTTPS proxy
    opts = {
        "format": fmt,
        "merge_output_format": "mp4",
        "outtmpl": str(outdir / "%(title)s.%(ext)s"),
        "ignoreerrors": ignore_errors,
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


def download_video(url: str, outdir: Path, quality: str) -> Path:
    """Download the given video URL to outdir with selected quality.

    Returns the Path to the saved video file (mp4).
    """
    outdir.mkdir(parents=True, exist_ok=True)
    opts = _common_opts(outdir, quality, ignore_errors=False)
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise RuntimeError("yt-dlp returned no info (download may have failed).")
        base = Path(ydl.prepare_filename(info))
    return base.with_suffix(".mp4")


def download_video_playlist(url: str, outdir: Path, quality: str) -> Path:
    """Download an entire playlist as mp4s and return the zip path."""
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        opts = _common_opts(tmp, quality, ignore_errors=True)
        opts["outtmpl"] = str(tmp / "%(playlist_title)s/%(title)s.%(ext)s")
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            playlist_title = info.get("title") or "playlist"

        exts = {".mp4", ".mkv", ".webm", ".m4v"}
        files = [p for p in tmp.rglob("*") if p.is_file() and p.suffix.lower() in exts]
        if not files:
            raise RuntimeError("No video files were downloaded from the playlist (yt-dlp may have failed or needs cookies).")

        zip_name = _safe_name(playlist_title) + ".zip"
        zip_path = outdir / zip_name
        with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, arcname=f.relative_to(tmp))
        return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download YouTube video")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--outdir",
        default=Path("downloads/video"),
        type=Path,
        help="Output directory (default: downloads/video)",
    )
    parser.add_argument(
        "--quality",
        choices=list(QUALITY_MAP.keys()),
        default="best",
        help="Video quality/size preset",
    )
    args = parser.parse_args()
    dest = download_video(args.url, args.outdir, args.quality)
    print(f"Saved: {dest}")


if __name__ == "__main__":
    main()
