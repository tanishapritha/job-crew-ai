import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from crewai.tools import tool
import json
from config import settings

def send_email(to_email: str, subject: str, html_body: str) -> str:
    """Core function to send an email using SMTP settings."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to_email

        part2 = MIMEText(html_body, "html")
        msg.attach(part2)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())

        return "sent"
    except Exception as e:
        return f"failed: {str(e)}"

@tool("SendEmailTool")
def send_email_tool(input: str) -> str:
    """Sends an email. Input: JSON string with 'to', 'subject', 'body', 'html_body'."""
    try:
        data = json.loads(input)
        to_email = data['to']
        subject = data['subject']
        html_body = data.get('html_body', data.get('body', ''))
        return send_email(to_email, subject, html_body)
    except Exception as e:
        return f"failed: {str(e)}"
