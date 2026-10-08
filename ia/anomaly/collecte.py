"""
SENTINEL-X - Collecte des données capteurs
Récupère l'historique via l'API et sauvegarde en CSV.
"""
import requests
import pandas as pd
import time

API_URL = "http://localhost:3000/api/v1/data"
DATA_FILE = "data.csv"
COLLECT_DURATION = 60   # secondes
SAMPLE_INTERVAL = 2      # secondes entre chaque échantillon

def collecter():
    print(f"[INFO] Collecte des données pendant {COLLECT_DURATION}s...")
    rows = []
    start = time.time()
    while (time.time() - start) < COLLECT_DURATION:
        try:
            r = requests.get(API_URL, timeout=2)
            if r.status_code == 200:
                data = r.json()
                if len(data) > 0:
                    last = data[-1]
                    rows.append(last)
                    print(f"[DATA] {last.get('temperature', '?')}°C | "
                          f"{last.get('gaz', '?')} ppm | "
                          f"presence={last.get('presence', '?')}")
        except Exception as e:
            print(f"[ERREUR] {e}")
        time.sleep(SAMPLE_INTERVAL)
    df = pd.DataFrame(rows)
    df.to_csv(DATA_FILE, index=False)
    print(f"[OK] {len(rows)} échantillons sauvegardés dans {DATA_FILE}")

if __name__ == "__main__":
    collecter()
