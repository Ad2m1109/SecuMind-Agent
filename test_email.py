#!/usr/bin/env python3
import requests
import json

# Test email sending with an alert that should trigger RF escalation
url = "http://localhost:8000/process_alert"
headers = {"Content-Type": "application/json"}

# Alert that should trigger RF "escalate" decision with high confidence
payload = {
    "attack_type": "malware",
    "failed_attempts": 1,
    "severity_score": 0.6,
    "ip_reputation": 0.5,
    "previous_incidents": 1,
    "source_ip": "192.168.1.101",
    "test_mode": True  # Force RF path to avoid LLM timeout
}

print("Sending malware alert designed to trigger RF escalation...")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    # Check if email was sent
    if "email" in str(result).lower():
        print("✅ Email sending was triggered!")
    else:
        print("❌ Email was not triggered")

except Exception as e:
    print(f"Error: {e}")