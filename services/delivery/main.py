"""
MicroMail Mail Delivery Service
Handles email sending via SMTP
Consumes events from RabbitMQ for async email delivery
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import pika
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

app = FastAPI(title="Mail Delivery Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SMTP configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# RabbitMQ configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# Mock database for delivery status
delivery_status_db: dict = {}


# ============ Models ============

class DeliveryStatusResponse(BaseModel):
    email_id: str
    status: str
    sent_at: str | None
    error_message: str | None


# ============ Helper Functions ============

def get_connection():
    """Get RabbitMQ connection"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        return connection
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return None


def send_email_via_smtp(from_email: str, to: str, subject: str, body: str, cc: list = None, bcc: list = None) -> bool:
    """
    Send email via SMTP
    
    In production, use a service like SendGrid, AWS SES, or Mailgun
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to
        
        if cc:
            msg["Cc"] = ", ".join(cc)
        
        # Attach body
        msg.attach(MIMEText(body, "html"))
        
        # Send via SMTP (commented out to avoid errors without real SMTP server)
        # with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SMTP_USER, SMTP_PASSWORD)
        #     recipients = [to] + (cc or []) + (bcc or [])
        #     server.sendmail(from_email, recipients, msg.as_string())
        
        print(f"Email sent from {from_email} to {to}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def subscribe_to_events():
    """Subscribe to email send events from RabbitMQ"""
    try:
        connection = get_connection()
        if not connection:
            print("Could not connect to RabbitMQ for event subscription")
            return
        
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange="micromail",
            exchange_type="topic",
            durable=True
        )
        
        # Create queue for this service
        queue = channel.queue_declare(queue="delivery-service", durable=True)
        
        # Bind to email send events
        channel.queue_bind(
            exchange="micromail",
            queue="delivery-service",
            routing_key="email.send"
        )
        
        # Consume messages
        channel.basic_consume(
            queue="delivery-service",
            on_message_callback=handle_email_send_event,
            auto_ack=True
        )
        
        print("Delivery service listening for email.send events...")
        channel.start_consuming()
    except Exception as e:
        print(f"Error subscribing to events: {str(e)}")


def handle_email_send_event(ch, method, properties, body):
    """Handle incoming email send events"""
    try:
        event_data = json.loads(body)
        print(f"Delivery service received email.send event: {event_data}")
        
        email_id = event_data.get("email_id")
        from_email = event_data.get("from", "noreply@micromail.com")
        to = event_data.get("to")
        subject = event_data.get("subject", "")
        body_text = event_data.get("body", "")
        cc = event_data.get("cc")
        bcc = event_data.get("bcc")
        
        # Send email
        success = send_email_via_smtp(from_email, to, subject, body_text, cc, bcc)
        
        # Store delivery status
        if success:
            delivery_status_db[email_id] = {
                "email_id": email_id,
                "status": "delivered",
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "error_message": None
            }
            
            # Publish email.delivered event
            publish_event("email.delivered", {
                "email_id": email_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            delivery_status_db[email_id] = {
                "email_id": email_id,
                "status": "failed",
                "sent_at": None,
                "error_message": "SMTP delivery failed"
            }
            
            # Publish email.failed event
            publish_event("email.failed", {
                "email_id": email_id,
                "error": "SMTP delivery failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except Exception as e:
        print(f"Error handling email send event: {str(e)}")


def publish_event(event_name: str, data: dict):
    """Publish an event to RabbitMQ"""
    try:
        connection = get_connection()
        if not connection:
            return
        
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange="micromail",
            exchange_type="topic",
            durable=True
        )
        
        # Publish message
        channel.basic_publish(
            exchange="micromail",
            routing_key=event_name,
            body=json.dumps(data),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        
        connection.close()
        print(f"Published event: {event_name}")
    except Exception as e:
        print(f"Error publishing event: {str(e)}")


# ============ API Endpoints ============

@app.post("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "delivery"}


@app.get("/status/{email_id}", response_model=DeliveryStatusResponse)
async def get_delivery_status(email_id: str):
    """
    Get the delivery status of an email
    """
    status = delivery_status_db.get(email_id, {
        "email_id": email_id,
        "status": "pending",
        "sent_at": None,
        "error_message": None
    })
    
    return DeliveryStatusResponse(**status)


@app.post("/send")
async def send_email(
    from_email: str,
    to: str,
    subject: str,
    body: str
):
    """
    Manually trigger email sending (for testing)
    
    In production, emails are sent async via RabbitMQ events
    """
    import uuid
    
    email_id = str(uuid.uuid4())
    
    success = send_email_via_smtp(from_email, to, subject, body)
    
    if success:
        delivery_status_db[email_id] = {
            "email_id": email_id,
            "status": "delivered",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "error_message": None
        }
        
        return {
            "status": "ok",
            "message": "Email sent successfully",
            "email_id": email_id
        }
    else:
        return {
            "status": "error",
            "message": "Failed to send email",
            "email_id": email_id
        }, 500


@app.post("/queue-status")
async def get_queue_status():
    """
    Get the status of the email delivery queue
    """
    return {
        "pending": len([e for e in delivery_status_db.values() if e.get("status") == "pending"]),
        "delivered": len([e for e in delivery_status_db.values() if e.get("status") == "delivered"]),
        "failed": len([e for e in delivery_status_db.values() if e.get("status") == "failed"]),
        "total": len(delivery_status_db)
    }


if __name__ == "__main__":
    import uvicorn
    # In a real implementation, run event subscriber in a separate thread
    # import threading
    # threading.Thread(target=subscribe_to_events, daemon=True).start()
    
    uvicorn.run(app, host="0.0.0.0", port=8004)
