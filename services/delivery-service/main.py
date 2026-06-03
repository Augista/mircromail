from fastapi import FastAPI
import pika
import json
import logging
import asyncio
import time
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from smtp_provider import get_provider

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MicroMail Delivery Service",
    description="Email delivery with SMTP integration and retry logic",
    version="1.0.0"
)

# Global state
email_provider = None
rabbitmq_connection = None
rabbitmq_channel = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Delivery Service"
    }


def setup_rabbitmq():
    """Setup RabbitMQ connection and queues"""
    global rabbitmq_connection, rabbitmq_channel
    
    try:
        rabbitmq_connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        rabbitmq_channel = rabbitmq_connection.channel()
        
        # Declare exchange
        rabbitmq_channel.exchange_declare(
            exchange='micromail-events',
            exchange_type='topic',
            durable=True
        )
        
        # Declare main queue
        rabbitmq_channel.queue_declare(
            queue='delivery-service-queue',
            durable=True
        )
        
        # Declare dead-letter queue for failed emails
        rabbitmq_channel.queue_declare(
            queue='delivery-dead-letter-queue',
            durable=True
        )
        
        # Bind main queue to email.send events
        rabbitmq_channel.queue_bind(
            exchange='micromail-events',
            queue='delivery-service-queue',
            routing_key='email.send'
        )
        
        logger.info("RabbitMQ setup completed")
    except Exception as e:
        logger.error(f"Failed to setup RabbitMQ: {str(e)}")
        raise


def publish_event(event_type: str, data: dict, user_id: str = None):
    """Publish event back to RabbitMQ"""
    try:
        if not rabbitmq_channel:
            return
        
        event = {
            'event_type': event_type,
            'event_id': str(uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'data': data
        }
        
        message = json.dumps(event, default=str)
        
        routing_key = event_type  # e.g., "email.delivered", "email.failed"
        
        rabbitmq_channel.basic_publish(
            exchange='micromail-events',
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(
                content_type='application/json',
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
        logger.info(f"Published {event_type} event")
    except Exception as e:
        logger.error(f"Failed to publish event: {str(e)}")


async def send_email_with_retry(
    to_email: str,
    subject: str,
    body: str,
    cc: str = None,
    bcc: str = None,
    from_email: str = None,
    from_name: str = None,
    max_retries: int = None
) -> bool:
    """Send email with exponential backoff retry logic"""
    max_retries = max_retries or settings.MAX_RETRIES
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Sending email to {to_email} (attempt {attempt + 1}/{max_retries + 1})")
            
            # Send email
            success = await email_provider.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                from_email=from_email,
                from_name=from_name
            )
            
            if success:
                logger.info(f"Email successfully sent to {to_email}")
                return True
            
        except Exception as e:
            logger.error(f"Error sending email (attempt {attempt + 1}): {str(e)}")
        
        # Retry with exponential backoff
        if attempt < max_retries:
            delay = settings.RETRY_DELAY_SECONDS * (2 ** attempt)  # Exponential backoff
            logger.info(f"Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    
    logger.error(f"Failed to send email to {to_email} after {max_retries + 1} attempts")
    return False


def process_email_event(ch, method, properties, body):
    """Process email.send event from RabbitMQ"""
    db = None
    try:
        event = json.loads(body)
        logger.info(f"Processing email event: {event.get('event_id')}")
        
        user_id = event.get('user_id')
        email_data = event.get('data', {})
        
        # Validate required fields
        required_fields = ['to_email', 'subject', 'body']
        if not all(field in email_data for field in required_fields):
            logger.error(f"Missing required fields in email event: {email_data}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        # Send email with retry
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            send_email_with_retry(
                to_email=email_data['to_email'],
                subject=email_data['subject'],
                body=email_data['body'],
                cc=email_data.get('cc'),
                bcc=email_data.get('bcc'),
                from_email=email_data.get('from_email'),
                from_name=email_data.get('from_name')
            )
        )
        
        if success:
            # Publish email.delivered event
            publish_event(
                event_type='email.delivered',
                user_id=user_id,
                data={
                    'draft_id': email_data.get('draft_id'),
                    'to_email': email_data['to_email'],
                    'subject': email_data['subject'],
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Email processed successfully for user {user_id}")
        else:
            # Publish email.failed event
            publish_event(
                event_type='email.failed',
                user_id=user_id,
                data={
                    'draft_id': email_data.get('draft_id'),
                    'to_email': email_data['to_email'],
                    'subject': email_data['subject'],
                    'error': 'Max retries exceeded',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Move to dead-letter queue
            rabbitmq_channel.basic_publish(
                exchange='',
                routing_key='delivery-dead-letter-queue',
                body=body,
                properties=pika.BasicProperties(
                    content_type='application/json',
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.error(f"Email moved to dead-letter queue for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error processing email event: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consumer():
    """Start consuming email.send events from RabbitMQ"""
    global email_provider
    
    try:
        # Initialize email provider
        email_provider = get_provider()
        logger.info(f"Email provider initialized: {settings.SMTP_PROVIDER}")
        
        # Setup RabbitMQ
        setup_rabbitmq()
        
        # Start consuming
        rabbitmq_channel.basic_qos(prefetch_count=1)
        rabbitmq_channel.basic_consume(
            queue='delivery-service-queue',
            on_message_callback=process_email_event
        )
        
        logger.info("Starting email delivery consumer...")
        rabbitmq_channel.start_consuming()
    
    except Exception as e:
        logger.error(f"Consumer error: {str(e)}")
        if rabbitmq_connection:
            rabbitmq_connection.close()


@app.on_event("startup")
async def startup_event():
    """Start RabbitMQ consumer on app startup"""
    import threading
    
    # Start RabbitMQ consumer in background thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("Delivery service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown"""
    global rabbitmq_connection
    
    if rabbitmq_connection:
        rabbitmq_connection.close()
    logger.info("Delivery service stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.DELIVERY_SERVICE_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
