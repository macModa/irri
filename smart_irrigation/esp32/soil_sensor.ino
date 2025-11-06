/*
 * ESP32 - Capteur d'humidité du sol avec MQTT
 * Lit un capteur analogique d'humidité et publie les données sur EMQX
 * 
 * Bibliothèques requises:
 * - WiFi (incluse avec ESP32)
 * - PubSubClient (MQTT)
 * - ArduinoJson
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ===== CONFIGURATION WiFi =====
const char* WIFI_SSID = "VotreSSID";          // Remplacer par votre SSID
const char* WIFI_PASSWORD = "VotreMotDePasse"; // Remplacer par votre mot de passe

// ===== CONFIGURATION MQTT (EMQX) =====
const char* MQTT_BROKER = "192.168.1.100";  // Adresse IP du broker EMQX
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "";              // Laisser vide si pas d'authentification
const char* MQTT_PASSWORD = "";
const char* MQTT_TOPIC = "farmboy/sensors/plot1";  // Topic MQTT

// ===== CONFIGURATION CAPTEUR =====
const int SOIL_SENSOR_PIN = 34;  // Pin ADC pour capteur d'humidité (GPIO34)
const char* PLOT_ID = "plot_001"; // Identifiant unique de la parcelle

// Valeurs de calibration du capteur (à ajuster selon votre capteur)
const int SOIL_DRY_VALUE = 3200;    // Valeur ADC quand le sol est sec
const int SOIL_WET_VALUE = 1300;    // Valeur ADC quand le sol est humide

// ===== TIMING =====
const unsigned long PUBLISH_INTERVAL = 60000;  // 60 secondes entre chaque lecture
unsigned long lastPublishTime = 0;

// ===== INSTANCES =====
WiFiClient espClient;
PubSubClient mqttClient(espClient);


// ===== FONCTIONS =====

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== ESP32 Capteur d'humidité du sol ===");
  Serial.println("Initialisation...\n");
  
  // Configuration du capteur
  pinMode(SOIL_SENSOR_PIN, INPUT);
  
  // Connexion WiFi
  connectWiFi();
  
  // Configuration MQTT
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
  
  Serial.println("✓ Initialisation terminée\n");
}


void loop() {
  // Maintenir la connexion WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠ WiFi déconnecté. Reconnexion...");
    connectWiFi();
  }
  
  // Maintenir la connexion MQTT
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  // Publier les données à intervalle régulier
  unsigned long currentTime = millis();
  if (currentTime - lastPublishTime >= PUBLISH_INTERVAL) {
    lastPublishTime = currentTime;
    publishSensorData();
  }
}


void connectWiFi() {
  Serial.print("Connexion WiFi à: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi connecté!");
    Serial.print("Adresse IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm\n");
  } else {
    Serial.println("\n✗ Échec connexion WiFi");
    Serial.println("Vérifiez vos identifiants et redémarrez l'ESP32\n");
  }
}


void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connexion MQTT au broker ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.print(MQTT_PORT);
    Serial.println("...");
    
    // Créer un ID client unique
    String clientId = "ESP32_";
    clientId += String(PLOT_ID);
    
    // Tentative de connexion
    bool connected;
    if (strlen(MQTT_USERNAME) > 0) {
      connected = mqttClient.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD);
    } else {
      connected = mqttClient.connect(clientId.c_str());
    }
    
    if (connected) {
      Serial.println("✓ MQTT connecté!");
      Serial.print("Topic de publication: ");
      Serial.println(MQTT_TOPIC);
      Serial.println();
    } else {
      Serial.print("✗ Échec connexion MQTT, code: ");
      Serial.println(mqttClient.state());
      Serial.println("Nouvelle tentative dans 5 secondes...\n");
      delay(5000);
    }
  }
}


void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Callback pour messages MQTT entrants (non utilisé ici)
  Serial.print("Message reçu [");
  Serial.print(topic);
  Serial.print("]: ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
}


float readSoilHumidity() {
  // Lire la valeur analogique (moyenne de 5 lectures)
  int sum = 0;
  for (int i = 0; i < 5; i++) {
    sum += analogRead(SOIL_SENSOR_PIN);
    delay(10);
  }
  int rawValue = sum / 5;
  
  // Convertir en pourcentage (0-100%)
  // Sol sec = 0%, Sol humide = 100%
  float humidity = map(rawValue, SOIL_DRY_VALUE, SOIL_WET_VALUE, 0, 100);
  
  // Limiter entre 0 et 100
  humidity = constrain(humidity, 0, 100);
  
  Serial.print("📊 Lecture capteur - Raw: ");
  Serial.print(rawValue);
  Serial.print(" | Humidité: ");
  Serial.print(humidity, 1);
  Serial.println("%");
  
  return humidity;
}


void publishSensorData() {
  Serial.println("\n--- Publication des données ---");
  
  // Lire l'humidité du sol
  float soilHumidity = readSoilHumidity();
  
  // Créer le payload JSON
  StaticJsonDocument<200> doc;
  doc["plot_id"] = PLOT_ID;
  doc["soil_humidity"] = round(soilHumidity * 10) / 10.0;  // Arrondir à 1 décimale
  doc["timestamp"] = millis() / 1000;  // Timestamp en secondes
  
  // Sérialiser en JSON
  char jsonBuffer[200];
  serializeJson(doc, jsonBuffer);
  
  // Publier sur MQTT
  Serial.print("📤 Publication sur topic: ");
  Serial.println(MQTT_TOPIC);
  Serial.print("Payload: ");
  Serial.println(jsonBuffer);
  
  if (mqttClient.publish(MQTT_TOPIC, jsonBuffer)) {
    Serial.println("✓ Message publié avec succès\n");
  } else {
    Serial.println("✗ Échec de publication\n");
  }
}


// ===== FONCTIONS OPTIONNELLES =====

void calibrateSensor() {
  /*
   * Fonction pour calibrer le capteur
   * À appeler dans setup() pour obtenir les valeurs min/max
   */
  Serial.println("=== Mode Calibration ===");
  Serial.println("1. Plongez le capteur dans l'eau");
  Serial.println("2. Notez la valeur WET");
  Serial.println("3. Séchez le capteur à l'air libre");
  Serial.println("4. Notez la valeur DRY");
  Serial.println();
  
  for (int i = 0; i < 10; i++) {
    int value = analogRead(SOIL_SENSOR_PIN);
    Serial.print("Valeur ADC: ");
    Serial.println(value);
    delay(2000);
  }
}
