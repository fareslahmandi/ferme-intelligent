#include <DHT.h>
#include <WiFi.h>
#include <HTTPClient.h>

// Définition des broches
#define HUMIDITY_SENSOR_PIN 34  // AO du capteur d'humidité sol
#define DHTPIN 15               // GPIO du DHT11
#define DHTTYPE DHT11

// L298N - Pompe à eau (IN3, IN4)
#define IN3 16
#define IN4 17

// L298N - Ventilateur (IN1, IN2)
#define IN1 4
#define IN2 5

const int HUMIDITY_THRESHOLD = 2000;
const unsigned long FAN_RUN_DURATION = 30000;

DHT dht(DHTPIN, DHTTYPE);

// WiFi
const char* ssid = "Orange-DB5B";
const char* password = "skandar13280060";
const char* serverUrl = "http://192.168.1.139:8000/alert"; // IP de ton PC

unsigned long fanActivationTime = 0;
bool fanOn = false;
bool pumpOn = false;

void setup() {
  Serial.begin(115200);
  delay(2000);

  WiFi.begin(ssid, password);
  Serial.print("Connexion au WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ Connecté au WiFi");

  dht.begin();

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);

  Serial.println("🟢 Système démarré");
  Serial.println("==================");
}

void loop() {
  int humidityValue = analogRead(HUMIDITY_SENSOR_PIN);
  Serial.print("💧 Humidité sol : ");
  Serial.println(humidityValue);

  if (humidityValue > HUMIDITY_THRESHOLD) {
    Serial.println("🔴 Sol sec détecté, pompe activée");
    digitalWrite(IN3, HIGH);
    digitalWrite(IN4, LOW);
    if (!pumpOn) {
      pumpOn = true;
      envoyerDonnee("pompe", "on");
    }
  } else {
    Serial.println("🟢 Sol humide, pompe désactivée");
    digitalWrite(IN3, LOW);
    digitalWrite(IN4, LOW);
    if (pumpOn) {
      pumpOn = false;
      envoyerDonnee("pompe", "off");
    }
  }

  float rawTemp = dht.readTemperature();
  float correctedTemp = rawTemp ;  // Correction empirique
  float humidityAir = dht.readHumidity();

  if (isnan(correctedTemp) || isnan(humidityAir)) {
    Serial.println("Erreur lecture DHT11");
  } else {
    Serial.print("🌡 Température corrigée : ");
    Serial.print(correctedTemp);
    Serial.print(" °C | Humidité air: ");
    Serial.print(humidityAir);
    Serial.println(" %");

    if (!fanOn && correctedTemp > 27) {
      Serial.println("→ Ventilateur ACTIVÉ");
      digitalWrite(IN1, HIGH);
      digitalWrite(IN2, LOW);
      fanActivationTime = millis();
      fanOn = true;
      envoyerDonnee("ventilateur", "on");
    }

    if (fanOn && (millis() - fanActivationTime >= FAN_RUN_DURATION)) {
      Serial.println("→ Ventilateur ÉTEINT");
      digitalWrite(IN1, LOW);
      digitalWrite(IN2, LOW);
      fanOn = false;
      envoyerDonnee("ventilateur", "off");
    }
  }

  Serial.println("----------------------------------");
  delay(2000);
}

// --- Envoi HTTP vers Streamlit/FastAPI ---
void envoyerDonnee(String capteur, String valeur) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    String json = "{\"device\": \"ESP32-Garden\", \"sensor\": \"" + capteur + "\", \"value\": \"" + valeur + "\"}";
    int httpResponseCode = http.POST(json);

    Serial.print("📤 Envoi ");
    Serial.print(capteur);
    Serial.print(" = ");
    Serial.print(valeur);
    Serial.print(" | Code réponse : ");
    Serial.println(httpResponseCode);

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("📩 Réponse serveur : " + response);
    }

    http.end();
  } else {
    Serial.println("❌ WiFi non connecté");
  }
}
