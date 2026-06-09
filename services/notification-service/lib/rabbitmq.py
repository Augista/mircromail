import pika
import threading
import json
import asyncio
from config import settings
from lib.websocket_manager import manager
from database import SessionLocal
from models.notification import Notification

def process_message(ch, method, properties, body, loop):
    """
    Fungsi ini dieksekusi saat ada pesan masuk dari RabbitMQ
    """
    try:
        # 1. Parse JSON dari Mail Service
        payload = json.loads(body)
        print(f"[x] Menerima pesan dari RabbitMQ: {payload}")
        
        # 2. Cek apakah ini event pengiriman email
        event_type = payload.get("type")
        if event_type != "MAIL_SENT":
            return  # Abaikan event jika bukan tentang email terkirim
            
        # 3. Ekstrak data berdasarkan format buatan Tata
        data = payload.get("data", {})
        user_id = data.get("recipient")  # Email penerima menjadi target WebSocket
        title = data.get("subject", "Tidak ada subjek")
        sender = data.get("sender", "Seseorang")
        msg_body = f"Kamu mendapat email baru dari {sender}."
        
        if user_id:
            # 4. Simpan ke Database
            db = SessionLocal()
            new_notif = Notification(user_id=str(user_id), title=title, message=msg_body)
            db.add(new_notif)
            db.commit()
            db.refresh(new_notif)
            
            # 5. Format ulang data untuk dikirim ke frontend via WebSocket
            ws_message = {
                "id": new_notif.id,
                "user_id": user_id,
                "title": title,
                "message": msg_body,
                "is_read": False,
                "type": "NEW_EMAIL"
            }
            db.close()

            # 6. Kirim via WebSocket ke frontend
            asyncio.run_coroutine_threadsafe(
                manager.send_personal_message(json.dumps(ws_message), str(user_id)),
                loop
            )
            
    except Exception as e:
        print(f"[!] Error saat memproses pesan RabbitMQ: {e}")

def start_consumer(loop):
    try:
        parameters = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        queue_name = 'mail_events'
        channel.queue_declare(queue=queue_name, durable=True)

        channel.basic_consume(
            queue=queue_name, 
            on_message_callback=lambda ch, m, p, body: process_message(ch, m, p, body, loop), 
            auto_ack=True
        )

        print(f"[*] Berhasil terhubung ke RabbitMQ. Menunggu pesan di '{queue_name}'...")
        channel.start_consuming()
    except Exception as e:
        print(f"[!] Gagal terhubung ke RabbitMQ: {e}")

def run_rabbitmq_consumer(loop):
    thread = threading.Thread(target=start_consumer, args=(loop,), daemon=True)
    thread.start()