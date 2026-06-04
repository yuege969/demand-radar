FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libgbm1 libasound2 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libpango-1.0-0 libcairo2 libcups2 libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir .[dev]
RUN pip install playwright && playwright install --with-deps chromium

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
