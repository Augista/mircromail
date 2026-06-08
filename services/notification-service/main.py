from fastapi import FastAPI
from prometheus_client import make_asgi_app, Counter
from config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# --- Observability: Prometheus Metrics ---
# Hapus "_total" pada nama metrik, Prometheus akan menambahkannya secara otomatis
REQUEST_COUNT = Counter("api_requests", "Total requests", ["method", "endpoint"])

# Menambahkan endpoint /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    # Menambah hitungan metrik setiap kali endpoint ini dipanggil
    REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()
    return {"status": "healthy", "service": "notification-service"}