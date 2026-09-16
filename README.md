# Manna Downloader

A responsive video/audio downloader web app built with FastAPI and yt-dlp.

## Local Windows test

1. Install Python 3.10+.
2. Double-click `run.bat`.
3. Open `http://127.0.0.1:8000`.
4. Paste a supported URL and click Analyze.

## Deploy to Render

This project includes a Dockerfile and `render.yaml`.

1. Create a GitHub repository.
2. Upload all project files to the repository.
3. In Render, create a new Web Service from that GitHub repository.
4. Render should detect the Dockerfile automatically.
5. Choose the Free plan.
6. Deploy.
7. Your service receives an `onrender.com` URL.
8. Share that URL with Android/iOS users.

The container includes FFmpeg and Node.js because yt-dlp may need FFmpeg for merging separate video/audio streams and a JavaScript runtime for some extractors.

## Important

Render's free web services can spin down after inactivity, so the first request after idle time can be slower.

The app uses temporary server-side files and schedules them for deletion after the response. For a larger public service, add authentication, stronger rate limiting, download quotas, queueing, storage limits, and abuse controls.

Only download content you are authorized to download or content whose platform/rightsholder permits downloading. This project does not attempt to bypass DRM, paywalls, authentication, or other access controls.
