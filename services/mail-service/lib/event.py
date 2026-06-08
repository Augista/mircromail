import json
import pika
from datetime import datetime, UTC

from config import settings


def publish_mail_sent(mail):
    connection = pika.BlockingConnection(
        pika.URLParameters(settings.RABBITMQ_URL)
    )

    channel = connection.channel()
    channel.queue_declare(queue="mail_events", durable=True)

    event = {
        "type": "MAIL_SENT",
        "timestamp": datetime.now(UTC).isoformat(),
        "data": {
            "mail_id": mail.id,
            "sender": mail.sender,
            "recipient": mail.recipient,
            "subject": mail.subject
        }
    }

    channel.basic_publish(
        exchange="",
        routing_key="mail_events",
        body=json.dumps(event)
    )

    connection.close()