import pandas as pd
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
ORIGINAL_DATA = os.path.join(DATA_DIR, "alerts.csv")
LOGGED_DATA = os.path.join(DATA_DIR, "processed_alerts.csv")

def retrain():
    # 1. Load Original Data
    df_orig = pd.read_csv(ORIGINAL_DATA)
    
    # 2. Load Logged Data if exists
    if os.path.exists(LOGGED_DATA):
        df_logs = pd.read_csv(LOGGED_DATA)
        # Keep only original features and decision
        features = ["attack_type", "failed_attempts", "severity_score", "ip_reputation", "previous_incidents", "decision"]
        df_logs = df_logs[features]
        
        # Combine
        df = pd.concat([df_orig, df_logs], ignore_index=True)
    else:
        df = df_orig

    # 3. Encode
    le_attack = LabelEncoder()
    df["attack_type"] = le_attack.fit_transform(df["attack_type"])
    
    le_decision = LabelEncoder()
    df["decision"] = le_decision.fit_transform(df["decision"])
    
    # 4. Train
    X = df.drop("decision", axis=1)
    y = df["decision"]
    
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X, y)
    
    # 5. Save
    joblib.dump(rf_model, os.path.join(MODEL_DIR, "rf_model.pkl"))
    joblib.dump(le_attack, os.path.join(MODEL_DIR, "attack_encoder.pkl"))
    joblib.dump(le_decision, os.path.join(MODEL_DIR, "decision_encoder.pkl"))
    
    return len(df)

if __name__ == "__main__":
    count = retrain()
    print(f"Retrained on {count} samples. Model updated!")
