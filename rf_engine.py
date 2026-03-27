# ==============================
# RF ENGINE - SAFE VERSION
# ==============================

import os
import joblib
import pandas as pd

# -----------------------------
# PATH CONFIGURATION
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

rf_model = joblib.load(os.path.join(MODEL_DIR, "rf_model.pkl"))
le_attack = joblib.load(os.path.join(MODEL_DIR, "attack_encoder.pkl"))
le_decision = joblib.load(os.path.join(MODEL_DIR, "decision_encoder.pkl"))


def predict_alert(alert_dict):

    try:
        # Handle unknown attack type
        if alert_dict["attack_type"] not in le_attack.classes_:
            return "escalate", 0.0, "unknown_attack_type"

        attack_encoded = le_attack.transform(
            [alert_dict["attack_type"]]
        )[0]

        data = pd.DataFrame([[
            attack_encoded,
            alert_dict["failed_attempts"],
            alert_dict["severity_score"],
            alert_dict["ip_reputation"],
            alert_dict["previous_incidents"]
        ]], columns=[
            "attack_type",
            "failed_attempts",
            "severity_score",
            "ip_reputation",
            "previous_incidents"
        ])

        prediction = rf_model.predict(data)
        probabilities = rf_model.predict_proba(data)
        confidence = probabilities.max()

        decision_label = le_decision.inverse_transform(prediction)[0]

        return decision_label, float(confidence), "ok"

    except Exception as e:
        return "escalate", 0.0, f"error: {str(e)}"