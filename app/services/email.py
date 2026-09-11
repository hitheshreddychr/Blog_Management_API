import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)


def send_notification_email(
    to_email: str,
    subject: str,
    body: str,
) -> None:
    """
    Send an email notification to a blog post owner.
    """

    if not SMTP_HOST:
        print("Email notification skipped: SMTP_HOST is not configured.")
        return

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(
            "Email notification skipped: "
            "SMTP credentials are not configured."
        )
        return

    if not SMTP_FROM:
        print("Email notification skipped: SMTP_FROM is not configured.")
        return

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = to_email

    message.set_content(body)

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT,
        timeout=10,
    ) as server:
        server.starttls()
        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD,
        )
        server.send_message(message)