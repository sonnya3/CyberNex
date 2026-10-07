"""
SENTINEL-X - Reconnaissance faciale avec face_recognition
Detecte les visages connus (base) et inconnus (intrus).
Utilise le detecteur CNN + tolerance 0.6 pour plus de stabilite.
"""

import cv2
import face_recognition
import os
import numpy as np
import requests
import time
from datetime import datetime, timezone

VIDEO_SOURCE = 0
API_URL = "http://localhost:3000/api/v1/alerts"
DEVICE_ID = "ESP32-CAM-FACE"
KNOWN_FACES_DIR = "known_faces"
ALERT_COOLDOWN = 5
TOLERANCE = 0.6

known_face_encodings = []
known_face_names = []

print("[INFO] Chargement des visages connus...")
for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        image_path = os.path.join(KNOWN_FACES_DIR, filename)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image, model="cnn")
        if len(encodings) > 0:
            known_face_encodings.append(encodings[0])
            known_face_names.append(os.path.splitext(filename)[0])
            print(f"[OK] Visage charge : {os.path.splitext(filename)[0]}")
        else:
            print(f"[WARN] Aucun visage detecte dans {filename}")

print(f"[INFO] {len(known_face_names)} personne(s) connue(s)")

if len(known_face_encodings) == 0:
    print("[ERREUR] Aucun visage de reference charge. Verifie known_faces/")
    exit(1)

cap = cv2.VideoCapture(VIDEO_SOURCE)
if not cap.isOpened():
    print("[ERREUR] Impossible d'ouvrir la webcam")
    exit(1)

last_alert_time = 0
frame_count = 0
last_results = []

print("[INFO] Detection faciale en cours (appuie sur 'q' pour quitter)")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    display = frame.copy()

    if frame_count % 5 == 0:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame, model="cnn")
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        last_results = []

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(
                known_face_encodings, face_encoding, tolerance=TOLERANCE
            )
            name = "INTRUS"
            color = (0, 0, 255)
            distance = 1.0

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                distance = face_distances[best_match_index]
                if matches[best_match_index] or distance < TOLERANCE:
                    name = known_face_names[best_match_index]
                    color = (0, 255, 0)

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            last_results.append((top, right, bottom, left, name, color, distance))

    for (top, right, bottom, left, name, color, dist) in last_results:
        cv2.rectangle(display, (left, top), (right, bottom), color, 2)
        cv2.rectangle(display, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        label = f"{name} ({dist:.2f})" if name != "INTRUS" else name
        cv2.putText(display, label, (left + 6, bottom - 6),
                    cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

    connus = sum(1 for r in last_results if r[4] != "INTRUS")
    intrus = sum(1 for r in last_results if r[4] == "INTRUS")
    status = f"Connus: {connus} | Intrus: {intrus}"
    color_status = (0, 255, 0) if intrus == 0 else (0, 0, 255)
    cv2.putText(display, f"SENTINEL-X FACE | {status}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_status, 2)

    now = time.time()
    if intrus > 0 and (now - last_alert_time) > ALERT_COOLDOWN:
        payload = {
            "device_id": DEVICE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "INTRUSION_FACIALE",
            "intrus_count": intrus,
            "source": "FACE_RECOGNITION"
        }
        try:
            r = requests.post(API_URL, json=payload, timeout=2)
            if r.status_code == 201:
                print(f"[ALERTE] {intrus} visage(s) inconnu(s) detecte(s)")
        except Exception as e:
            print(f"[ERREUR] Envoi API : {e}")
        last_alert_time = now

    cv2.imshow("SENTINEL-X - Reconnaissance Faciale", display)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("[INFO] Arret")
