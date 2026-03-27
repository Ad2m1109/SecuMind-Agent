#!/usr/bin/env python3
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ANALYST_EMAIL = os.getenv("ANALYST_EMAIL", "")

print("Testing SMTP configuration...")
print(f"SMTP Host: {SMTP_HOST}")
print(f"SMTP Port: {SMTP_PORT}")
print(f"SMTP User: {SMTP_USER}")
print(f"Analyst Email: {ANALYST_EMAIL}")
print(f"Password configured: {'Yes' if SMTP_PASS else 'No'}")

try:
    msg = EmailMessage()
    msg["Subject"] = "[TEST] Cybersecurity Dashboard Email Test"
    msg["From"] = SMTP_USER
    msg["To"] = ANALYST_EMAIL

    msg.set_content("This is a test email from your cybersecurity dashboard. If you receive this, email sending is working correctly!")

    print("Attempting to send test email...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

    print("✅ SUCCESS: Test email sent successfully!")
    print(f"Check your inbox at: {ANALYST_EMAIL}")

except Exception as e:
    print(f"❌ FAILED: {e}")
    print("Troubleshooting tips:")
    print("1. Check if SMTP credentials are correct")
    print("2. Enable 'Less secure app access' in Gmail settings")
    print("3. Or generate an App Password if 2FA is enabled")
    print("4. Verify firewall allows SMTP connections")