import pika
import threading
import json
import asyncio
from config import settings
from websocket_manager import manager
from database import SessionLocal
from models import Notification

def process_message(ch, method, properties, body, loop):
    try:
        message_data = json.loads(body)
        print(f"[x] Menerima pesan dari RabbitMQ: {message_data}")
        
        user_id = message_data.get("user_id")
        title = message_data.get("title", "Notifikasi Baru")
        msg_body = message_data.get("body", "")
        
        if user_id:
            db = SessionLocal()
            new_notif = Notification(user_id=str(user_id), title=title, message=msg_body)
            db.add(new_notif)
            db.commit()
            db.refresh(new_notif)
            
            message_data["id"] = new_notif.id
            db.close()

            asyncio.run_coroutine_threadsafe(
                manager.send_personal_message(json.dumps(message_data), str(user_id)),
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