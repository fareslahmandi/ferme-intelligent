import torch
import cv2
import numpy as np
import requests

# ESP32 Address
SERVER_URL = "http://192.168.37.204:80/fire"

# YOLOV5 Repo Path
YOLOV5_PATH = "C:/Users/21658/OneDrive/Desktop/yolov5"
MODEL_PATH = "./fire_detection_model.pt"

# Load the YOLOv5 model
model = torch.hub.load(YOLOV5_PATH, 'custom', path=MODEL_PATH, source='local')
model.conf = 0.2  # Set confidence threshold

# Open the webcam
cap = cv2.VideoCapture(0)
fire_detected = False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert BGR (OpenCV) to RGB (PyTorch expects RGB)
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Inference
    results = model(img_rgb)

    # Get predictions
    detections = results.xyxy[0]  # (x1, y1, x2, y2, conf, class)

    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        class_name = model.names[int(cls)]

        if class_name.lower() == "fire":
            if not fire_detected:
                print("🔥 Fire detected! Sending alert to server...")

                try:
                    response = requests.get(SERVER_URL)
                    print("Server response:", response.text)
                except Exception as e:
                    print("Error sending request:", e)
                fire_detected = True
            break
    else:
        fire_detected = False

    # Show detections
    annotated_frame = np.squeeze(results.render())  # RGB frame
    annotated_frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
    cv2.imshow('YOLOv5 Fire Detection', annotated_frame_bgr)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()