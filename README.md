# Manna Downloader

Render-ready FastAPI video/audio downloader for content you are authorized to download or where the platform/rightsholder permits downloading. It does not bypass DRM, paywalls, authentication, or access controls.

## Render deployment

This project uses Docker. Render should detect `Dockerfile` automatically. The app listens on `0.0.0.0` and uses Render's `PORT` environment variable.

The container also starts the BgUtils YouTube PO Token HTTP provider locally. yt-dlp is configured to use the `mweb` YouTube client and the local provider.

## Temporary diagnostic endpoint (Render Free)

Render Free web services do not provide Dashboard Shell/SSH access, so this version includes a temporary, protected diagnostic endpoint.

1. In Render, open **Manna Downloader → Environment**.
2. Add an environment variable:
   - Key: `DIAGNOSTIC_KEY`
   - Value: choose a long random value, for example 32+ random characters.
3. Save/redeploy.
4. Send a POST request to `/api/diagnostic` with JSON such as:

```json
{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}
```

and an HTTP header:

```text
Authorization: Bearer YOUR_DIAGNOSTIC_KEY
```

The endpoint runs verbose yt-dlp **on the Render server itself** and returns a sanitized/truncated diagnostic log. This is useful for debugging YouTube extraction without Shell access.

After troubleshooting, remove `DIAGNOSTIC_KEY` from Render and redeploy. The endpoint then returns 404.

## Local Windows run

Run `run.bat`, then open `http://127.0.0.1:8000`.

## Notes

- Render Free web services have an ephemeral filesystem; temporary downloaded files are not permanent.
- Free services can spin down after inactivity and take time to wake up.
- Keep downloads temporary and use the service only for content you are authorized to download.
