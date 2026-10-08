"""
SENTINEL-X - Entraînement du modèle Isolation Forest
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os

DATA_FILE = "data.csv"
MODEL_FILE = "model.pkl"
SCALER_FILE = "scaler.pkl"
CONTAMINATION = 0.1   # 10% d'anomalies supposées

def entrainer():
    if not os.path.exists(DATA_FILE):
        print(f"[ERREUR] {DATA_FILE} introuvable. Lance d'abord collecte.py")
        return

    print("[INFO] Chargement des données...")
    df = pd.read_csv(DATA_FILE)

    # Colonnes nécessaires
    colonnes = ["temperature", "gaz", "humidity"]
    for col in colonnes:
        if col not in df.columns:
            print(f"[ERREUR] Colonne manquante : {col}")
            return

    # Nettoyage
    X = df[colonnes].dropna().values
    print(f"[INFO] {len(X)} échantillons valides")

    if len(X) < 20:
        print(f"[ERREUR] Pas assez de données ({len(X)} < 20)")
        return

    # Normalisation
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Entraînement
    print("[INFO] Entraînement du modèle Isolation Forest...")
    model = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION,
        random_state=42
    )
    model.fit(X_scaled)

    # Sauvegarde
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)
    with open(SCALER_FILE, "wb") as f:
        pickle.dump(scaler, f)

    print(f"[OK] Modèle sauvegardé dans {MODEL_FILE}")

    # Statistiques
    scores = model.decision_function(X_scaled)
    anomalies = model.predict(X_scaled)
    n_anomalies = sum(1 for a in anomalies if a == -1)
    print(f"[STATS] Anomalies détectées : {n_anomalies}/{len(X)}")

if __name__ == "__main__":
    entrainer()
