#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "Galaxy";
const char* password = "123456780";

WebServer server(80);
const int buzzerPin = 4; // Choisis une broche disponible pour le buzzer

void handleFireAlert() {              
  digitalWrite(buzzerPin, HIGH);            // Activer le buzzer
  delay(1000);
  digitalWrite(buzzerPin, LOW);
  Serial.println("Fire detected! Buzzer ON");
  server.send(200, "text/plain", "Fire detected, Buzzer ON");
}

void setup() {
  Serial.begin(115200);
  pinMode(buzzerPin, OUTPUT);               // Définir la broche du buzzer en sortie
  digitalWrite(buzzerPin, LOW);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected.");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/fire", handleFireAlert);
  server.begin();
  Serial.println(" ESP32 HTTP server started");
}

void loop() {
  server.handleClient();
}
