FROM python:3.11-slim

WORKDIR /app

# System deps for Playwright Chromium + SSL certificates
RUN apt-get update && apt-get install -y --no-install-recommends --fix-missing \
    ca-certificates wget gnupg \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    libdbus-1-3 libatspi2.0-0 libx11-6 libx11-xcb1 libxcb1 \
    libxext6 libxfixes3 libxi6 libxrender1 libxtst6 \
    libfontconfig1 fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

ENV PORT=8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --timeout-keep-alive 120"]
