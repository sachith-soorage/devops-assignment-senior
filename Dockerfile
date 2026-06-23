# Slim, current Python base to keep image size and CVE surface small
FROM python:3.12-slim

# Prevents Python from writing pyc files
# Prevents Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Run as an unprivileged user (defense in depth)
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Serve with a production WSGI server. Single worker + threads keeps Prometheus
# metrics consistent (per-process); scale horizontally via Kubernetes replicas
# worker-tmp-dir on /tmp pairs with the read-only root filesystem in k8s.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", \
     "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "app:app"]
