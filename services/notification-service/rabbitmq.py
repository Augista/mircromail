import pika
import threading
import json
from config import settings

def process_message(ch, method, properties, body):
    """
    Fungsi ini akan dieksekusi otomatis setiap kali ada pesan masuk ke RabbitMQ
    """
    try:
        # Mengubah pesan dari bytes (format RabbitMQ) menjadi dictionary Python
        message = json.loads(body)
        print(f"[x] Menerima event notifikasi: {message}")
        
        # TODO: Di Fase 4 nanti, kita akan kirim pesan ini ke frontend via WebSocket
        
    except Exception as e:
        print(f"[!] Error saat memproses pesan: {e}")

def start_consumer():
    """
    Fungsi untuk membuat koneksi dan mendengarkan antrean RabbitMQ
    """
    try:
        # Membuat koneksi ke RabbitMQ
        parameters = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Mendeklarasikan antrean (queue) bernama 'mail_events'
        # durable=True memastikan antrean tidak hilang walau RabbitMQ di-restart
        queue_name = 'mail_events'
        channel.queue_declare(queue=queue_name, durable=True)

        # Mengaitkan fungsi process_message dengan antrean
        channel.basic_consume(
            queue=queue_name, 
            on_message_callback=process_message, 
            auto_ack=True
        )

        print(f"[*] Berhasil terhubung ke RabbitMQ. Menunggu pesan di '{queue_name}'...")
        channel.start_consuming()
    except Exception as e:
        print(f"[!] Gagal terhubung ke RabbitMQ: {e}")

def run_rabbitmq_consumer():
    """
    Menjalankan consumer di thread terpisah agar tidak memblokir FastAPI
    """
    thread = threading.Thread(target=start_consumer, daemon=True)
    thread.start()