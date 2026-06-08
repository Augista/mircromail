import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from prometheus_client import make_asgi_app, Counter
from config import settings
from lib.rabbitmq import run_rabbitmq_consumer
from lib.websocket_manager import manager
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db, engine, Base
from models.notification import Notification
from schemas.notification import NotificationResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Mengecek dan membuat tabel database...")
    Base.metadata.create_all(bind=engine)
    
    loop = asyncio.get_running_loop()
    print("Menyiapkan Notification Service...")
    run_rabbitmq_consumer(loop)
    yield
    print("Mematikan Notification Service...")

    # Menangkap event loop async dari FastAPI untuk dikirim ke RabbitMQ
    loop = asyncio.get_running_loop()
    print("Menyiapkan Notification Service...")
    run_rabbitmq_consumer(loop)
    yield
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

@app.get("/test-ws")
async def get_test_page():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Test WebSocket</title>
            <style>body { font-family: sans-serif; padding: 20px; }</style>
        </head>
        <body>
            <h2>Testing WebSocket MicroMail</h2>
            <button onclick="connect()">Sambungkan ke WebSocket</button>
            <ul id="messages" style="background: #f4f4f4; padding: 20px; border-radius: 8px;"></ul>
            <script>
                function connect() {
                    // Kita gunakan 127.0.0.1 agar lebih aman di Windows
                    var ws = new WebSocket("ws://127.0.0.1:8005/ws/user_123");
                    var messages = document.getElementById("messages");
                    
                    ws.onopen = function() {
                        var li = document.createElement("li");
                        li.style.color = "green";
                        li.appendChild(document.createTextNode("🟢 Status: Berhasil Terhubung ke Server!"));
                        messages.appendChild(li);
                    };
                    
                    ws.onmessage = function(event) {
                        var li = document.createElement("li");
                        li.style.color = "blue";
                        li.appendChild(document.createTextNode("🔔 Notifikasi Masuk: " + event.data));
                        messages.appendChild(li);
                    };

                    ws.onerror = function(error) {
                        var li = document.createElement("li");
                        li.style.color = "red";
                        li.appendChild(document.createTextNode("🔴 Error: Koneksi Gagal (Cek Terminal)"));
                        messages.appendChild(li);
                    };
                }
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# --- Endpoint WebSocket ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Tetap mendengarkan agar koneksi tidak terputus
            # Walaupun dari frontend MicroMail mungkin tidak mengirim apa-apa
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# --- REST API Endpoints ---

@app.get("/api/notifications/{user_id}", response_model=List[NotificationResponse])
async def get_notifications(user_id: str, db: Session = Depends(get_db)):
    """Mengambil seluruh riwayat notifikasi untuk user tertentu, diurutkan dari yang terbaru"""
    notifs = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    return notifs

@app.put("/api/notifications/{notification_id}/read")
async def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    """Menandai satu notifikasi sebagai 'sudah dibaca'"""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
        return {"status": "success", "message": "Notifikasi ditandai sudah dibaca"}
    raise HTTPException(status_code=404, detail="Notifikasi tidak ditemukan")