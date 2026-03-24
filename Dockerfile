FROM python:3.12-slim

RUN apt-get update && apt-get install -y libgomp1 libsm6 libxext6 libglib2.0-0 libgl1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the working venv with all dependencies
COPY .venv_cached /opt/venv

# Set environment
ENV PATH=/opt/venv/bin:$PATH
ENV PYTHONPATH=/opt/venv/lib/python3.12/site-packages
ENV PYTHONUNBUFFERED=1
ENV PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

# Copy application
COPY app /app/app
COPY .env.example /app/.env
RUN mkdir -p /app/outputs

EXPOSE 8000

# Use system python from base image (has all libraries)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
