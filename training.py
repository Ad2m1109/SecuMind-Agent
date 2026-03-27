import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os
import joblib

# -----------------------------
# PATH CONFIGURATION
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_PATH = os.path.join(BASE_DIR, "data", "alerts.csv")

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# ----------------------------
# 1. LOAD DATASET
# ----------------------------
df = pd.read_csv(DATA_PATH)


# ----------------------------
# 2. ENCODE CATEGORICAL DATA
# ----------------------------

le_attack = LabelEncoder()
df["attack_type"] = le_attack.fit_transform(df["attack_type"])

le_decision = LabelEncoder()
df["decision"] = le_decision.fit_transform(df["decision"])

# ----------------------------
# 3. SPLIT DATA
# ----------------------------

X = df.drop("decision", axis=1)
y = df["decision"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ----------------------------
# 4. TRAIN RANDOM FOREST
# ----------------------------

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# ----------------------------
# 5. EVALUATE
# ----------------------------

y_pred = rf_model.predict(X_test)
print(classification_report(y_test, y_pred))

# ----------------------------
# 6. TEST NEW ALERT
# ----------------------------

new_alert = pd.DataFrame([[
    le_attack.transform(["brute_force"])[0],
    25,
    0.85,
    0.7,
    1
]], columns=X.columns)

prediction = rf_model.predict(new_alert)
confidence = rf_model.predict_proba(new_alert).max()

decision_label = le_decision.inverse_transform(prediction)[0]

print("\nPrediction:", decision_label)
print("Confidence:", round(confidence, 2))






import joblib
import os

# -----------------------------
# PATH CONFIGURATION
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)


joblib.dump(rf_model, os.path.join(MODEL_DIR, "rf_model.pkl"))
joblib.dump(le_attack, os.path.join(MODEL_DIR, "attack_encoder.pkl"))
joblib.dump(le_decision, os.path.join(MODEL_DIR, "decision_encoder.pkl"))

print("Model and encoders saved!")
