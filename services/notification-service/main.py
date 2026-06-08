from fastapi import FastAPI
from prometheus_client import make_asgi_app
import uvicorn

app = FastAPI(title="MicroMail Notification Service")

# Menambahkan endpoint metrics untuk Prometheus (Tugas Tracing)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification-service"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)