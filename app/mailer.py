import logging
import smtplib
from email.message import EmailMessage
from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_FROM

logger = logging.getLogger(__name__)

def send_reset_email(to: str, link: str) -> bool:
    if not all((SMTP_HOST, SMTP_USER, SMTP_PASSWORD, MAIL_FROM)):
        logger.warning("Password reset link for %s: %s", to, link)
        return False
    message = EmailMessage()
    message["Subject"] = "Reset your Saathi password"
    message["From"] = MAIL_FROM
    message["To"] = to
    message.set_content(f"Reset your Saathi password here: {link}\nThis link expires in 30 minutes.")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls(); smtp.login(SMTP_USER, SMTP_PASSWORD); smtp.send_message(message)
    return True
