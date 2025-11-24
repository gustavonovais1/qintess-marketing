FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y xvfb x11vnc fluxbox novnc websockify x11-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src

COPY start.sh ./start.sh
RUN chmod +x ./start.sh

ENV HEADLESS=false
ENV DOWNLOADS_DIR=/app/downloads
VOLUME /app/downloads

EXPOSE 5900 6080
ENTRYPOINT ["/app/start.sh"]

ENV DEFAULT_COMPANY_HREF=/company/64618175/admin/
ENV DEFAULT_SEGMENTS=updates,visitors,followers,competitors

CMD ["--storage","/app/storage_state.json"]