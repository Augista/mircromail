import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
import requests
from config import settings

logger = logging.getLogger(__name__)


class SMTPProvider(ABC):
    """Abstract SMTP provider"""
    
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None
    ) -> bool:
        """Send email via provider"""
        pass


class SendGridProvider(SMTPProvider):
    """SendGrid email provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = "https://api.sendgrid.com/v3/mail/send"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
        from_email: str = None,
        from_name: str = None
    ) -> bool:
        """Send email via SendGrid"""
        try:
            from_email = from_email or settings.SMTP_FROM_EMAIL
            from_name = from_name or settings.SMTP_FROM_NAME
            
            # Prepare email data
            recipients = [{"email": to_email}]
            if cc:
                recipients.extend([{"email": c.strip()} for c in cc.split(',')])
            if bcc:
                recipients.extend([{"email": b.strip()} for b in bcc.split(',')])
            
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "cc": [{"email": c.strip()} for c in cc.split(',')] if cc else [],
                        "bcc": [{"email": b.strip()} for b in bcc.split(',')] if bcc else [],
                    }
                ],
                "from": {
                    "email": from_email,
                    "name": from_name
                },
                "subject": subject,
                "content": [
                    {
                        "type": "text/html",
                        "value": body
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.endpoint, json=payload, headers=headers)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent to {to_email} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"SendGrid send error: {str(e)}")
            return False


class MailgunProvider(SMTPProvider):
    """Mailgun email provider"""
    
    def __init__(self, api_key: str, domain: str = None):
        self.api_key = api_key
        self.domain = domain or "sandboxXXX.mailgun.org"
        self.endpoint = f"https://api.mailgun.net/v3/{self.domain}/messages"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
        from_email: str = None,
        from_name: str = None
    ) -> bool:
        """Send email via Mailgun"""
        try:
            from_email = from_email or settings.SMTP_FROM_EMAIL
            from_name = from_name or settings.SMTP_FROM_NAME
            
            data = {
                "from": f"{from_name} <{from_email}>",
                "to": to_email,
                "subject": subject,
                "html": body
            }
            
            if cc:
                data["cc"] = cc
            if bcc:
                data["bcc"] = bcc
            
            response = requests.post(
                self.endpoint,
                auth=("api", self.api_key),
                data=data
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Email sent to {to_email} via Mailgun")
                return True
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Mailgun send error: {str(e)}")
            return False


class SMTPProvider_Legacy(SMTPProvider):
    """Legacy SMTP provider for standard SMTP servers"""
    
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
        from_email: str = None,
        from_name: str = None
    ) -> bool:
        """Send email via SMTP"""
        try:
            from_email = from_email or settings.SMTP_FROM_EMAIL
            from_name = from_name or settings.SMTP_FROM_NAME
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = cc
            
            # Add body
            msg.attach(MIMEText(body, 'html'))
            
            # Prepare recipients
            recipients = [to_email]
            if cc:
                recipients.extend([c.strip() for c in cc.split(',')])
            if bcc:
                recipients.extend([b.strip() for b in bcc.split(',')])
            
            # Send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(from_email, recipients, msg.as_string())
            
            logger.info(f"Email sent to {to_email} via SMTP")
            return True
        except Exception as e:
            logger.error(f"SMTP send error: {str(e)}")
            return False


def get_provider() -> SMTPProvider:
    """Get configured SMTP provider"""
    provider_type = settings.SMTP_PROVIDER.lower()
    
    if provider_type == "sendgrid":
        return SendGridProvider(settings.SMTP_API_KEY)
    elif provider_type == "mailgun":
        return MailgunProvider(settings.SMTP_API_KEY)
    elif provider_type == "smtp":
        # For legacy SMTP - requires additional env vars
        return SMTPProvider_Legacy(
            host=os.getenv("SMTP_HOST", "localhost"),
            port=int(os.getenv("SMTP_PORT", 587)),
            user=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", "")
        )
    else:
        raise ValueError(f"Unsupported SMTP provider: {provider_type}")
