import requests
import random
import time
import json

URL = "http://127.0.0.1:8000/process_alert"

ATTACK_TYPES = ["brute_force", "malware", "scan", "privilege_escalation"]

def simulate_alert():
    attack = random.choice(ATTACK_TYPES)
    
    # Generate realistic data
    if attack == "brute_force":
        attempts = random.randint(5, 50)
        severity = 0.4 if attempts < 10 else 0.9
    elif attack == "malware":
        attempts = 1
        severity = random.uniform(0.6, 0.98)
    else:
        attempts = random.randint(1, 10)
        severity = random.uniform(0.2, 0.6)

    payload = {
        "attack_type": attack,
        "failed_attempts": attempts,
        "severity_score": round(severity, 2),
        "ip_reputation": round(random.uniform(0.1, 0.9), 2),
        "previous_incidents": random.randint(0, 3)
    }

    try:
        print(f"📡 Sending simulated {attack} alert...")
        response = requests.post(URL, json=payload, timeout=5)
        print(f"✅ Response: {response.json().get('decision')} | {response.json().get('action')}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 SIEM Simulator Started. Sending 10 random alerts...")
    for _ in range(10):
        simulate_alert()
        time.sleep(2)
    print("🏁 Simulation complete.")
