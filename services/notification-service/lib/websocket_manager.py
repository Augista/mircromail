from fastapi import WebSocket
from typing import Dict

class ConnectionManager:
    def __init__(self):
        # Menyimpan koneksi aktif berdasarkan user_id: { "user_123": WebSocket }
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        # Menerima koneksi baru
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"[WS] User {user_id} terhubung.")

    def disconnect(self, user_id: str):
        # Menghapus koneksi saat user menutup tab/browser
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"[WS] User {user_id} terputus.")

    async def send_personal_message(self, message: str, user_id: str):
        # Mengirim pesan langsung ke user tertentu
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)
            print(f"[WS] Pesan real-time terkirim ke user {user_id}")
        else:
            print(f"[WS] User {user_id} sedang offline. Pesan diabaikan.")

# Buat instance global agar bisa dipanggil dari file mana saja
manager = ConnectionManager()