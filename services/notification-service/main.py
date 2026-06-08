from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import make_asgi_app, Counter
from config import settings
from rabbitmq import run_rabbitmq_consumer

# --- Lifespan Events (Dijalankan saat startup & shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Jalankan background thread untuk RabbitMQ
    print("Menyiapkan Notification Service...")
    run_rabbitmq_consumer()
    yield
    # Shutdown: (Bisa diisi logika untuk memutus koneksi dengan aman)
    print("Mematikan Notification Service...")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# --- Observability: Prometheus Metrics ---
REQUEST_COUNT = Counter("api_requests", "Total requests", ["method", "endpoint"])

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()
    return {"status": "healthy", "service": "notification-service"}