
import asyncio
import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Manna Downloader")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# BgUtils automatically generates YouTube Proof-of-Origin tokens for yt-dlp.
# This is used only for YouTube extraction and does not store personal account cookies.
YOUTUBE_EXTRACTOR_ARGS = {
    "youtube": "player_client=mweb;youtubepot-bgutilscript:server_home=/root/bgutil-ytdlp-pot-provider/server",
}

YTDLP_COMMON_OPTS = {
    "noplaylist": True,
    "extractor_args": YOUTUBE_EXTRACTOR_ARGS,
}


class VideoRequest(BaseModel):
    url: HttpUrl
    format_id: str = "best"
    media_type: str = "video"


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Please enter a valid HTTP/HTTPS URL.")
    return url


def clean_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name[:120].strip(" .") or "video"


def extract_info(url: str):
    opts = {
        **YTDLP_COMMON_OPTS,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not analyze this URL: {exc}")


def cleanup_file(path: str):
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


@app.get("/")
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Manna Downloader"}


@app.post("/api/info")
async def info(request: VideoRequest):
    url = validate_url(str(request.url))
    data = await asyncio.to_thread(extract_info, url)

    if request.media_type == "audio":
        return {
            "title": data.get("title") or "Audio",
            "thumbnail": data.get("thumbnail"),
            "duration": data.get("duration"),
            "uploader": data.get("uploader") or data.get("channel"),
            "formats": [{"id": "audio", "label": "MP3 • 320 kbps", "height": 0}],
        }

    # Build one option per useful height, selecting the best video stream
    # for that height. Audio is merged during the download step.
    best_by_height = {}
    for f in data.get("formats", []):
        if f.get("vcodec") in (None, "none"):
            continue
        height = f.get("height")
        fid = f.get("format_id")
        if not height or not fid:
            continue
        existing = best_by_height.get(height)
        filesize = f.get("filesize") or f.get("filesize_approx") or 0
        current_filesize = (existing or {}).get("filesize") or 0
        # Prefer the larger/better bitrate format at the same height.
        if existing is None or filesize >= current_filesize:
            best_by_height[height] = {
                "id": str(fid),
                "label": f"{height}p",
                "height": height,
                "filesize": filesize,
            }

    formats = sorted(best_by_height.values(), key=lambda x: x["height"], reverse=True)

    return {
        "title": data.get("title") or "Video",
        "thumbnail": data.get("thumbnail"),
        "duration": data.get("duration"),
        "uploader": data.get("uploader") or data.get("channel"),
        "formats": formats[:20],
    }


def _download(url: str, opts: dict):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


@app.post("/api/download")
async def download(request: VideoRequest, background_tasks: BackgroundTasks):
    url = validate_url(str(request.url))
    data = await asyncio.to_thread(extract_info, url)
    job_id = uuid.uuid4().hex
    title = clean_name(data.get("title") or "video")

    if request.media_type == "audio":
        output_template = str(DOWNLOAD_DIR / f"{job_id}_{title}.%(ext)s")
        opts = {
            **YTDLP_COMMON_OPTS,
            "format": "ba/b",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        }
    else:
        output_template = str(DOWNLOAD_DIR / f"{job_id}_{title}.%(ext)s")
        requested = request.format_id.strip()

        # Merge selected video quality with the best available audio.
        if requested == "best":
            selector = "bv*+ba/b"
        else:
            selector = f"{requested}+ba/{requested}/b"

        opts = {
            **YTDLP_COMMON_OPTS,
            "format": selector,
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

    try:
        await asyncio.to_thread(_download, url, opts)
    except Exception as exc:
        for p in DOWNLOAD_DIR.glob(f"{job_id}_*"):
            cleanup_file(str(p))
        raise HTTPException(status_code=400, detail=f"Download failed: {exc}")

    candidates = [
        p for p in DOWNLOAD_DIR.glob(f"{job_id}_*")
        if p.is_file() and not p.name.endswith((".part", ".ytdl"))
    ]

    if not candidates:
        raise HTTPException(status_code=500, detail="The output file was not found.")

    file_path = max(candidates, key=lambda p: p.stat().st_mtime)
    download_name = file_path.name.split("_", 1)[-1]

    # Remove the temporary server-side file after the response is sent.
    background_tasks.add_task(cleanup_file, str(file_path))

    media_type = "audio/mpeg" if file_path.suffix.lower() == ".mp3" else "video/mp4"
    return FileResponse(file_path, media_type=media_type, filename=download_name)


@app.on_event("shutdown")
def shutdown():
    pass
