# ==============================
# AGENT API (RF + External LLM)
# ==============================

from fastapi import FastAPI
from pydantic import BaseModel
from passlib.hash import bcrypt
from login.database import get_connection
from rf_engine import predict_alert
from retrain import retrain
import subprocess
import smtplib
from email.message import EmailMessage
import requests
import pandas as pd
import os
import pymysql
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# 🔁 حط هنا ngrok URL متاع Colab
LLM_URL = os.getenv("LLM_URL", "https://7115-34-11-217-31.ngrok-free.app/generate")

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.85"))

# -----------------------------
# PATH CONFIGURATION
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# -----------------------------
# Request Schema
# -----------------------------

class AlertRequest(BaseModel):
    attack_type: str
    failed_attempts: int
    severity_score: float
    ip_reputation: float
    previous_incidents: int
    source_ip: str | None = None
    analyst_email: str | None = None


# -----------------------------
# Remediation + Escalation
# -----------------------------

ANALYST_EMAIL = os.getenv("ANALYST_EMAIL", "soc_analyst@example.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "no-reply@example.com")
SMTP_PASS = os.getenv("SMTP_PASS", "password")  # replace securely in prod


def execute_remediation(decision, alert):
    src_ip = alert.get("source_ip") or alert.get("ip") or "127.0.0.1"

    if decision == "block_ip":
        cmd = f"sudo ufw deny from {src_ip}"
    elif decision == "isolate":
        cmd = f"sudo iptables -A INPUT -s {src_ip} -j DROP && sudo iptables -A OUTPUT -d {src_ip} -j DROP"
    elif decision == "quarantine":
        cmd = f"echo 'quarantine {src_ip}'"
    else:
        return "no remediation command for this decision"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return f"executed: {cmd} | stdout: {result.stdout.strip()}"
    except Exception as e:
        return f"remediation failed: {e}"


def infer_action_from_text(text: str):
    t = (text or "").lower()
    if "block" in t or "drop" in t:
        return "block_ip"
    if "isolate" in t:
        return "isolate"
    if "quarantine" in t:
        return "quarantine"
    if "ignore" in t:
        return "ignore"
    return "escalate"


def send_email_to_analyst(alert_data, decision, explanation, analyst_email=None):
    recipient = analyst_email or ANALYST_EMAIL
    try:
        msg = EmailMessage()
        msg["Subject"] = f"[SOC] Escalation required: {decision}"
        msg["From"] = SMTP_USER
        msg["To"] = recipient

        body = (
            f"Alert: {alert_data}\n"
            f"Decision: {decision}\n"
            f"Explanation: {explanation}\n"
        )
        msg.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        return "email sent"
    except Exception as e:
        return f"email failed: {e}"


# -----------------------------
# Simple Auth Models
# -----------------------------

class User(BaseModel):
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str


# -----------------------------
# Logging Function (to database)
# -----------------------------

def log_alert(alert_data, decision, confidence, action, explanation):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO processed_alerts
            (attack_type, failed_attempts, severity_score, ip_reputation, previous_incidents,
             source_ip, decision, confidence, action, explanation, analyst_email)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            alert_data.get("attack_type"),
            alert_data.get("failed_attempts"),
            alert_data.get("severity_score"),
            alert_data.get("ip_reputation"),
            alert_data.get("previous_incidents"),
            alert_data.get("source_ip"),
            decision,
            confidence,
            action,
            explanation,
            alert_data.get("analyst_email")
        ))
        conn.commit()
    except Exception as e:
        print(f"Logging error: {e}")
    finally:
        cursor.close()
        conn.close()

# -----------------------------
# Process Alert Endpoint
# -----------------------------

@app.post("/process_alert")
async def process_alert(alert: AlertRequest):

    alert_dict = alert.dict()

    # 1️⃣ Random Forest Decision
    decision, confidence, reason = predict_alert(alert_dict)

    # 2️⃣ If high confidence → auto execute known remediation
    if confidence >= CONFIDENCE_THRESHOLD or alert_dict.get("test_mode", False):
        remediation = execute_remediation(decision, alert_dict)

        if decision in ["block_ip", "isolate", "quarantine"]:
            action = "executed"
            explanation = f"Random Forest automatically {decision} with {confidence*100:.1f}% confidence. Reason: {reason}. Remediation: {remediation}"

        elif decision == "ignore":
            action = "ignored"
            explanation = f"Random Forest decided to ignore with {confidence*100:.1f}% confidence. Reason: {reason}."

        else:
            action = "escalated"
            explanation = f"Random Forest decision {decision} unclear for automation; reason {reason}. Escalated."
            email_result = send_email_to_analyst(alert_dict, decision, explanation, alert_dict.get("analyst_email"))
            explanation += f" (email: {email_result})"

        log_alert(alert_dict, decision, confidence, action, explanation)

        return {
            "decision": decision,
            "confidence": confidence,
            "reason": reason,
            "action": action,
            "explanation": explanation
        }

    # 3️⃣ If low confidence or unknown → use LLM to get recommended action and fallback to analyst
    prompt = f"""
    You are a cybersecurity expert assistant.
    Review the following network alert and provide a detailed reasoning.

    Alert Data: {alert_dict}
    Random Forest Tentative Decision: {decision}
    Confidence Score: {confidence:.2f}
    Engine Note: {reason}

    Instruction:
    1. Analyze the threat level.
    2. Recommend a concrete remediation action (block_ip/isolate/quarantine/ignore/escalate).
    3. Provide a concise technical justification.
    """

    try:
        response = requests.post(
            LLM_URL,
            json={"prompt": prompt},
            timeout=10
        )

        if response.status_code == 200:
            explanation = response.json().get("response", "Consult technician for manual review.")
        else:
            explanation = "LLM unavailable. Escalating to analyst."

    except Exception as e:
        explanation = f"LLM error ({type(e).__name__}). Escalating to analyst."

    inferred = infer_action_from_text(explanation)

    if inferred in ["block_ip", "isolate", "quarantine"]:
        remediation = execute_remediation(inferred, alert_dict)
        action = "executed"
        explanation = f"LLM suggested {inferred}. {explanation} Remediation: {remediation}"
    elif inferred == "ignore":
        action = "ignored"
        explanation = f"LLM suggested ignore. {explanation}"
    else:
        action = "escalated"
        email_res = send_email_to_analyst(alert_dict, decision or inferred, explanation, alert_dict.get("analyst_email"))
        explanation = f"Escalated to analyst; email status: {email_res}. LLM details: {explanation}"

    log_alert(alert_dict, decision, confidence, action, explanation)

    return {
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
        "action": action,
        "explanation": explanation
    }

# -----------------------------
# Test Email Endpoint
# -----------------------------

@app.post("/test_email")
async def test_email():
    """Test endpoint to send a test email"""
    test_alert = {
        "attack_type": "test_malware",
        "failed_attempts": 1,
        "severity_score": 0.8,
        "ip_reputation": 0.6,
        "previous_incidents": 1
    }

    result = send_email_to_analyst(test_alert, "test_escalation", "This is a test email from the cybersecurity dashboard.")
    return {"email_result": result}

# -----------------------------

@app.get("/history")
async def get_history():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM processed_alerts ORDER BY processed_at DESC")
        history = cursor.fetchall()
        return history
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

# -----------------------------
# Get Alerts Endpoint (from database)
# -----------------------------

@app.get("/alerts")
async def get_alerts():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        alerts = cursor.fetchall()
        return alerts
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

# -----------------------------
# Retrain Model Endpoint
# -----------------------------

@app.post("/retrain")
async def retrain_model():
    try:
        count = retrain()
        return {"status": "success", "samples": count, "message": "Model retrained successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -----------------------------
# Simple Auth Endpoints (email/password, no JWT)
# -----------------------------

@app.post("/register")
def register(user: User):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (user.email,))
        if cursor.fetchone():
            return {"status": "user exists"}

        hashed = bcrypt.hash(user.password)

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (user.email, hashed)
        )

        conn.commit()
        return {"status": "success"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()


@app.post("/login")
def login(user: LoginUser):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE email=%s", (user.email,))
    db_user = cursor.fetchone()

    if not db_user:
        return {"status": "not found"}

    if not bcrypt.verify(user.password, db_user["password"]):
        return {"status": "wrong password"}

    return {
        "status": "success",
        "email": db_user["email"],
        "id": db_user["id"]
    }


@app.post("/forgot-password")
def forgot_password(data: dict):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE email=%s", (data.get("email"),))
    user = cursor.fetchone()

    if not user:
        return {"status": "email not found"}

    new_hashed = bcrypt.hash(data.get("new_password"))
    cursor.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (new_hashed, data.get("email"))
    )
    conn.commit()

    return {"status": "password updated"}


@app.post("/change-password-auth")
def change_password_auth(data: dict):
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM users WHERE email=%s", (data.get("email"),))
    db_user = cursor.fetchone()

    if not db_user:
        return {"status": "user not found"}

    if not bcrypt.verify(data.get("old_password"), db_user["password"]):
        return {"status": "wrong old password"}

    if bcrypt.verify(data.get("new_password"), db_user["password"]):
        return {"status": "same password"}

    new_hashed = bcrypt.hash(data.get("new_password"))
    cursor.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (new_hashed, data.get("email"))
    )
    conn.commit()

    return {"status": "password updated"}


@app.post("/delete-account")
def delete_account(data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE email=%s", (data.get("email"),))
    conn.commit()

    return {"status": "account deleted"}
