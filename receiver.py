from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from datetime import datetime

app = FastAPI()

# Allow access from your ESP32 system or any IP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data structure for incoming alerts
class FireAlert(BaseModel):
    device: str
    sensor: str
    value: str

@app.post("/alert")
async def receive_fire_alert(alert: FireAlert):
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "device": alert.device,
        "sensor": alert.sensor,
        "value": alert.value
    }

    # Append to json file
    try:
        with open("esp_data.json", "r") as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    existing_data.append(data)

    with open("esp_data.json", "w") as f:
        json.dump(existing_data, f, indent=4)

    return {"message": "Alert received successfully!"}