FROM node:20-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip ffmpeg git ca-certificates build-essential python3-dev libcairo2-dev libjpeg-dev libpango1.0-dev libgif-dev librsvg2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python3 -m pip install --break-system-packages --upgrade pip \
    && python3 -m pip install --break-system-packages -r requirements.txt

# Build the BgUtils PO Token provider used by yt-dlp for YouTube requests.
RUN git clone --depth 1 --branch 2.0.0 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /root/bgutil-ytdlp-pot-provider \
    && cd /root/bgutil-ytdlp-pot-provider/server \
    && npm ci \
    && npx tsc

COPY . .

RUN mkdir -p /app/downloads

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
