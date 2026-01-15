import torch
import cv2
import numpy as np
import requests
from datetime import datetime

# ESP32 Address
SERVER_URL = "http://192.168.37.204:80/fire"

# Streamlit app receiver
RECEIVER_URL = "http://localhost:80/alert"

# YOLOV5 Repo Path
YOLOV5_PATH = "C:/Users/21658/OneDrive/Desktop/yolov5"
MODEL_PATH = "./fire_detection_model.pt"

# Load the YOLOv5 model
model = torch.hub.load(YOLOV5_PATH, 'custom', path=MODEL_PATH, source='local')
model.conf = 0.2  # Confidence threshold

# Open webcam
cap = cv2.VideoCapture(0)
fire_detected = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert BGR to RGB
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Inference
    results = model(img_rgb)
    detections = results.xyxy[0]

    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        class_name = model.names[int(cls)]

        if class_name.lower() == "fire":
            if not fire_detected:
                print("🔥 Fire detected! Sending alerts...")

                # ---- ESP32 Alert ----
                try:
                    response = requests.get(SERVER_URL, timeout=2)
                    print("ESP32 response:", response.text)
                except Exception as e:
                    print("ESP32 error:", e)

                # ---- Streamlit Receiver Alert ----
                payload = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "device": "Cam01",
                    "sensor": "Fire Detection",
                    "value": "🔥 Fire detected!"
                }

                try:
                    response = requests.post(RECEIVER_URL, json=payload, timeout=2)
                    print("Receiver response:", response.text)
                except Exception as e:
                    print("Receiver error:", e)

                fire_detected = True
            break
    else:
        fire_detected = False

    # Display annotated frame
    annotated_frame = np.squeeze(results.render())
    annotated_frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
    cv2.imshow('YOLOv5 Fire Detection', annotated_frame_bgr)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()