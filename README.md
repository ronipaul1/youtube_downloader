# YouTube Downloader Tools (web + CLI)

Two tools now come with a minimal Flask front end.
- `audio_downloader.py`: helper/CLI to save MP3.
- `video_downloader.py`: helper/CLI to save videos.
- `app.py`: Flask web page with two forms (audio + video) and direct file responses.

## Setup
```bash
python -m venv .venv
. .venv/Scripts/activate  # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Requires `ffmpeg` on PATH for mp3 conversion and muxing. If it is installed elsewhere, set env var `FFMPEG_PATH` to its folder or binary path.

### Handling "Sign in to confirm you’re not a bot" (YouTube)
Some videos require cookies. Two options:
- Quick: use your browser cookies directly. Example (Chrome): set env `YT_COOKIES_BROWSER=chrome` before running Flask/CLI.
- Manual: export cookies.txt from your browser (see yt-dlp wiki) and set `YT_COOKIES_FILE=C:\path\to\cookies.txt`.

Both env vars work for audio and video downloads.

### Supported sites
Anything yt-dlp supports will work (YouTube, Vimeo, Facebook, X/Twitter, Instagram reels, TikTok, etc.). Some DRM or paywalled sites will not work.

## Run the web page
```bash
flask --app app run --reload
# open http://127.0.0.1:5000/
```
Paste a URL, pick video/audio, and the browser will download the resulting file.

## CLI usage (still works)
```bash
python audio_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
python video_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID" --quality 720p
```

## Notes
- Outputs land in `downloads/audio` and `downloads/video` under this folder.
- If downloads start failing, update yt-dlp: `python -m pip install -U yt-dlp`.
