# Senior Platform Engineer Assignment — Flask on Kubernetes

A simple Flask app, containerized and ready to run on local Kubernetes
(Minikube or Docker Desktop), with CI and basic observability.

> Scope note: this is intentionally minimal and time-boxed (~2h), not a
> production platform. See [Trade-offs](#trade-offs) for what I deliberately
> left out and why.

## The app

| Route       | Behavior                                          |
|-------------|---------------------------------------------------|
| `GET /`     | 302 redirect to `/sergei` or `/raditya` at random |
| `GET /sergei`   | `Sergei Fixed It!`                            |
| `GET /raditya`  | `Raditya Is Batman!`                          |
| `GET /healthz`  | `{"status":"ok"}` — liveness/readiness probe  |
| `GET /metrics`  | Prometheus metrics                            |

Served by **gunicorn** (not the Flask dev server) in a slim, non-root container.

## Prerequisites

- Docker
- A local cluster: Minikube **or** Docker Desktop Kubernetes
- `kubectl`

## Build

```bash
# Docker Desktop: builds straight into the cluster's image store.
docker build -t flask-app:local .

# Minikube: build inside Minikube's Docker daemon so the image is visible.
eval $(minikube docker-env)
docker build -t flask-app:local .
```

## Deploy

```bash
kubectl apply -f k8s/
kubectl rollout status deployment/flask-app
```

## Test locally

```bash
kubectl port-forward svc/flask-app 8080:80

# In another terminal:
curl -i  http://localhost:8080/          # 302 to /sergei or /raditya
curl     http://localhost:8080/sergei
curl     http://localhost:8080/healthz   # {"status":"ok"}
curl     http://localhost:8080/metrics   # Prometheus metrics
```

### Run without Kubernetes (quick sanity check)

```bash
pip install -r requirements.txt
gunicorn --bind 127.0.0.1:8000 app:app
```

## Clean up

```bash
kubectl delete -f k8s/
```

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on push/PR:
lint (flake8) → smoke test (`/healthz`, `/metrics`) → `docker build` →
Trivy image scan (HIGH/CRITICAL CVEs).

## Observability

- **Metrics:** `prometheus-flask-exporter` exposes `/metrics` (request rate,
  latency histograms, status codes). Pods carry `prometheus.io/*` annotations
  for scrape discovery.
- **Logs:** app + gunicorn access logs go to stdout (the container/K8s norm).
- **Health:** `/healthz` backs both probes.

## Security improvements (bonus)

- Non-root user (UID 10001) in the image **and** `runAsNonRoot` in the pod.
- `readOnlyRootFilesystem`, `allowPrivilegeEscalation: false`, all Linux
  capabilities dropped, `seccompProfile: RuntimeDefault`.
- Slim base image + pinned dependencies; Trivy CVE scan in CI.
- Resource requests/limits to bound blast radius of a misbehaving pod.

## Trade-offs

What I left out on purpose, given the time box:

- **Single gunicorn worker per pod** to keep Prometheus metrics consistent
  (per-process). Scaling is handled by K8s replicas; a multi-worker setup would
  need Prometheus multiprocess mode.
- **No Ingress** — `kubectl port-forward` is the simplest path that works
  identically on Minikube and Docker Desktop.
- **No Helm/Kustomize** — plain manifests are easier to read for a small app;
  I'd reach for Helm once there are environments/values to template.
- **Trivy is non-blocking** (`exit-code: 0`) for the demo; in a real pipeline
  I'd gate merges on it and add a base-image update cadence.
- **No HPA / NetworkPolicy / TLS** — out of scope for a local single-service demo.
