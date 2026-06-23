import logging
import random

from flask import Flask, jsonify, redirect
from prometheus_flask_exporter import PrometheusMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = Flask(__name__)

# Exposes Prometheus metrics on /metrics (request counts, latency histograms, etc.).
metrics = PrometheusMetrics(app)
metrics.info("app_info", "Application info", version="1.0.0")


@app.route("/sergei", methods=["GET"])
def sergei_route():
    return "Sergei Fixed It!"


@app.route("/raditya", methods=["GET"])
def raditya_route():
    return "Raditya Is Batman!"


@app.route("/", methods=["GET"])
def root_route():
    return redirect(random.choice(["/raditya", "/sergei"]), code=302)


@app.route("/healthz", methods=["GET"])
@metrics.do_not_track()
def healthz():
    """Liveness/readiness probe target. Excluded from metrics to avoid noise."""
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    # Dev only. In containers we run via gunicorn (see Dockerfile).
    app.run(host="0.0.0.0", port=8000)
