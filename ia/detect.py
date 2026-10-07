"""
SENTINEL-X - Detection d'intrusion par IA de vision
Utilise YOLOv8n pour detecter les personnes dans un flux video.
Publie une alerte au backend SENTINEL-X en cas d'intrusion.
"""

import cv2
import requests
import time
from datetime import datetime
from ultralytics import YOLO

# --- Configuration ---
VIDEO_SOURCE = 0                          # 0 = webcam par defaut
API_URL = "http://localhost:3000/api/v1/alerts"
DEVICE_ID = "ESP32-CAM-IA"
CONFIDENCE_THRESHOLD = 0.5
ALERT_COOLDOWN = 5                        # secondes entre 2 alertes

# --- Chargement du modele ---
print("[INFO] Chargement du modele YOLOv8n...")
model = YOLO("yolov8n.pt")
print("[OK] Modele charge")

# --- Ouverture de la source video ---
print(f"[INFO] Ouverture de la source : {VIDEO_SOURCE}")
cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():
    print("[ERREUR] Impossible d'ouvrir la source video")
    exit(1)

# --- Etat ---
last_alert_time = 0
frame_count = 0
fps_start = time.time()

print("[INFO] Detection en cours (appuie sur 'q' pour quitter)")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("[INFO] Fin de la video")
        break

    frame_count += 1

    # Redimensionnement (optimisation <100ms/trame)
    frame = cv2.resize(frame, (640, 480))

    # Inference YOLO
    results = model(frame, verbose=False)

    intrusion_detected = False
    person_count = 0

    # Parcours des detections
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            if model.names[cls] == "person" and conf > CONFIDENCE_THRESHOLD:
                person_count += 1
                intrusion_detected = True
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Rectangle rouge
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                # Label
                cv2.putText(frame, f"INTRUS {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Affichage FPS + statut
    elapsed = time.time() - fps_start
    fps = frame_count / elapsed if elapsed > 0 else 0
    status = f"INTRUS: {person_count}" if intrusion_detected else "Zone securisee"
    color = (0, 0, 255) if intrusion_detected else (0, 255, 0)
    cv2.putText(frame, f"SENTINEL-X IA | FPS: {fps:.1f}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, status, (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # Envoi d'alerte au backend
    now = time.time()
    if intrusion_detected and (now - last_alert_time) > ALERT_COOLDOWN:
        payload = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": "INTRUSION_IA",
            "person_count": person_count,
            "source": "YOLO_VISION"
        }
        try:
            r = requests.post(API_URL, json=payload, timeout=2)
            if r.status_code == 201:
                print(f"[ALERTE] {person_count} personne(s) detectee(s)")
            else:
                print(f"[WARN] API a repondu : {r.status_code}")
        except Exception as e:
            print(f"[ERREUR] Envoi API : {e}")
        last_alert_time = now

    # Affichage
    cv2.imshow("SENTINEL-X - Detection IA", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("[INFO] Detection arretee")
