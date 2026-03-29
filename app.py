from pathlib import Path
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from audio_downloader import download_audio, download_audio_playlist
from video_downloader import download_video, download_video_playlist, QUALITY_MAP

app = Flask(__name__)
app.secret_key = "yt-tools-secret-key"

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "downloads" / "audio"
VIDEO_DIR = BASE_DIR / "downloads" / "video"


@app.route("/")
def index():
    return render_template("index.html", qualities=QUALITY_MAP.keys())


@app.post("/download/audio")
def handle_audio():
    url = request.form.get("url", "").strip()
    if not url:
        flash("Please paste a YouTube URL for audio download.", "error")
        return redirect(url_for("index"))
    try:
        filepath = download_audio(url, AUDIO_DIR)
        flash(f"Audio ready: {filepath.name}", "success")
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filepath.name,
            mimetype="audio/mpeg",
        )
    except Exception as exc:  # pragma: no cover - runtime feedback
        flash(f"Audio download failed: {exc}", "error")
        return redirect(url_for("index"))


@app.post("/download/audio_playlist")
def handle_audio_playlist():
    url = request.form.get("url", "").strip()
    if not url:
        flash("Please paste a playlist URL for audio download.", "error")
        return redirect(url_for("index"))
    try:
        zip_path = download_audio_playlist(url, AUDIO_DIR)
        flash(f"Playlist ready: {zip_path.name}", "success")
        return send_file(zip_path, as_attachment=True, download_name=zip_path.name, mimetype="application/zip")
    except Exception as exc:  # pragma: no cover
        if request.headers.get("X-Requested-With") == "fetch":
            return (f"Playlist audio failed: {exc}", 400)
        flash(f"Playlist audio failed: {exc}", "error")
        return redirect(url_for("index"))


@app.post("/download/video")
def handle_video():
    url = request.form.get("url", "").strip()
    quality = request.form.get("quality", "best")
    if not url:
        flash("Please paste a YouTube URL for video download.", "error")
        return redirect(url_for("index"))
    try:
        filepath = download_video(url, VIDEO_DIR, quality)
        flash(f"Video ready: {filepath.name}", "success")
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filepath.name,
            mimetype="video/mp4",
        )
    except Exception as exc:  # pragma: no cover - runtime feedback
        flash(f"Video download failed: {exc}", "error")
        return redirect(url_for("index"))


@app.post("/download/video_playlist")
def handle_video_playlist():
    url = request.form.get("url", "").strip()
    quality = request.form.get("quality", "best")
    if not url:
        flash("Please paste a playlist URL for video download.", "error")
        return redirect(url_for("index"))
    try:
        zip_path = download_video_playlist(url, VIDEO_DIR, quality)
        flash(f"Playlist ready: {zip_path.name}", "success")
        return send_file(zip_path, as_attachment=True, download_name=zip_path.name, mimetype="application/zip")
    except Exception as exc:  # pragma: no cover
        if request.headers.get("X-Requested-With") == "fetch":
            return (f"Playlist video failed: {exc}", 400)
        flash(f"Playlist video failed: {exc}", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    # Run: flask --app app run --reload
    app.run(debug=True)
