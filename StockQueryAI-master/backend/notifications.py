import os
import logging
from email.message import EmailMessage
import aiosmtplib

log = logging.getLogger(__name__)

async def send_low_stock_email(items, recipients=None):
    """Send an email alert for low stock items."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    
    # Use provided recipients or fallback to ALERT_EMAIL
    if not recipients:
        recipients = [os.getenv("ALERT_EMAIL")]
    
    # Filter out None values
    recipients = [r for r in recipients if r]

    if not all([smtp_host, smtp_user, smtp_pass]) or not recipients:
        log.warning("[NOTIFY] SMTP settings or recipients missing. Skipping email.")
        return

    msg = EmailMessage()
    msg["Subject"] = "LOW STOCK ALERT - StockQuery AI"
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)

    body = "The following items have reached critical stock levels:\n\n"
    for item in items:
        body += f"* {item['name']} (ID: {item['id']}) - Current Stock: {item['stock']}\n"
    
    body += "\nPlease restock these items soon.\n\n-- StockQuery AI Assistant"
    msg.set_content(body)

    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_pass,
            use_tls=False,
            start_tls=True if smtp_port == 587 else False
        )
        log.info(f"[NOTIFY] Low stock email sent to {', '.join(recipients)}")
    except Exception as e:
        log.error(f"[NOTIFY] Failed to send email: {e}")
        # FALLBACK: Log to console so user can see it works (No emojis here to avoid Windows errors)
        log.info("[VIRTUAL NOTIFICATION] Since SMTP failed, here is the alert content:")
        print("\n" + "="*50)
        print(f"TO: {', '.join(recipients)}")
        print(f"SUBJECT: {msg['Subject']}")
        print("-"*50)
        print(body)
        print("="*50 + "\n")
