# PDF Bench - container for Render / Railway / Fly.io
FROM python:3.11-slim

WORKDIR /app

# Install Python deps first (better layer caching)
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# App code
COPY server ./server
COPY web ./web

# Render/Railway inject $PORT; default to 8000 for local `docker run`
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --timeout-keep-alive 120"]
