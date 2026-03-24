FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3.9 python3-pip libgomp1 libsm6 libxext6 libglib2.0-0 build-essential \
    libxrender-dev libxkbcommon-x11-0 libdbus-1-3 \
    && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.9 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY .env.example /app/.env
RUN mkdir -p /app/outputs

EXPOSE 8000
ENV PYTHONUNBUFFERED=1
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

CMD ["python3.8", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
