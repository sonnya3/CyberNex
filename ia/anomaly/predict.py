"""
SENTINEL-X - Détection d'anomalies en temps réel
Utilise Isolation Forest pour prédire les incidents AVANT seuil critique.
"""
import requests
import time
import pickle
import numpy as np
from datetime import datetime, timezone

API_ALERTS = "http://localhost:3000/api/v1/alerts"
API_POST = "http://localhost:3000/api/v1/alerts"
MODEL_FILE = "model.pkl"
SCALER_FILE = "scaler.pkl"
DEVICE_ID = "IA-PREDICT"
INTERVAL = 2   # secondes

# Chargement
with open(MODEL_FILE, "rb") as f:
    model = pickle.load(f)
with open(SCALER_FILE, "rb") as f:
    scaler = pickle.load(f)

print("[INFO] Modèle chargé. Détection en cours...")

while True:
    try:
        r = requests.get(API_ALERTS, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if len(data) > 0:
                last = data[-1]
                features = np.array([[
                    last.get("temperature", 0),
                    last.get("gaz", 0),
                    last.get("humidity", 0)
                ]])
                features_scaled = scaler.transform(features)
                prediction = model.predict(features_scaled)[0]
                score = model.decision_function(features_scaled)[0]

                print(f"[DATA] T={last.get('temperature', '?')}°C "
                      f"G={last.get('gaz', '?')}ppm "
                      f"H={last.get('humidity', '?')}% "
                      f"→ Score={score:.3f} "
                      f"{'⚠️ ANOMALIE' if prediction == -1 else '✓ Normal'}")

                if prediction == -1:
                    payload = {
                        "device_id": DEVICE_ID,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "type": "ANOMALIE_PREDICTIVE",
                        "temperature": last.get("temperature"),
                        "gaz": last.get("gaz"),
                        "score": float(score),
                        "source": "ISOLATION_FOREST"
                    }
                    try:
                        r = requests.post(API_POST, json=payload, timeout=2)
                        if r.status_code == 201:
                            print("[ALERTE] Anomalie prédictive envoyée")
                    except Exception as e:
                        print(f"[ERREUR] {e}")
    except Exception as e:
        print(f"[ERREUR] {e}")
    time.sleep(INTERVAL)
