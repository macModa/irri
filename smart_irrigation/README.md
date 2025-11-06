# 🌱 Smart Irrigation - Système d'Arrosage Intelligent Connecté

Projet complet de gestion d'arrosage intelligent avec ESP32, Django, MongoDB, MQTT (EMQX) et Flutter.

## 🎯 Fonctionnalités

- **ESP32** : Lecture d'humidité du sol et publication MQTT
- **Backend Django** : API REST, service MQTT, météo et génération de plans d'arrosage
- **MongoDB** : Base de données NoSQL pour toutes les données
- **EMQX** : Broker MQTT pour communication temps réel
- **OpenWeather** : Intégration météo pour prévisions
- **IA optionnelle** : Modèle ML (RandomForest/XGBoost) pour prédiction
- **Application Flutter** : Interface mobile pour configuration et suivi

## 📁 Structure du Projet

```
smart_irrigation/
├── backend/                    # Backend Django
│   ├── backend/
│   │   ├── settings.py        # Configuration Django
│   │   └── urls.py            # URLs principales
│   ├── irrigation/
│   │   ├── models.py          # Modèles de données
│   │   ├── mqtt_client.py     # Client MQTT
│   │   ├── weather_service.py # Service météo
│   │   ├── watering_plan_service.py  # Génération plans
│   │   ├── views.py           # API REST
│   │   ├── urls.py            # URLs de l'app
│   │   └── serializers.py     # Serializers REST
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── esp32/
│   └── soil_sensor.ino        # Code Arduino ESP32
├── flutter_app/
│   ├── main.dart              # Application Flutter
│   └── pubspec.yaml           # Dépendances Flutter
├── scripts/
│   └── train_model.py         # Entraînement IA
└── README.md
```

## 🚀 Installation

### 1. Prérequis

- Python 3.8+
- MongoDB 4.4+
- EMQX (broker MQTT)
- Flutter SDK
- Arduino IDE (pour ESP32)
- Clé API OpenWeather

### 2. Backend Django

```bash
cd backend

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos paramètres
```

#### Configuration `.env`

```bash
# Django
SECRET_KEY=votre-secret-key-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB
MONGO_DB_NAME=smart_irrigation
MONGO_HOST=localhost
MONGO_PORT=27017

# MQTT (EMQX)
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_TOPIC=farmboy/sensors/#

# OpenWeather API
OPENWEATHER_API_KEY=votre-cle-api-openweather

# IA (optionnel)
USE_AI_MODEL=False
AI_MODEL_PATH=./models/watering_model.pkl
```

#### Démarrer MongoDB

```bash
# Avec Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Ou installer MongoDB localement
sudo systemctl start mongod
```

#### Démarrer EMQX

```bash
# Avec Docker
docker run -d --name emqx \
  -p 1883:1883 \
  -p 8083:8083 \
  -p 8883:8883 \
  -p 8084:8084 \
  -p 18083:18083 \
  emqx/emqx:latest

# Dashboard EMQX: http://localhost:18083
# Login: admin / public
```

#### Initialiser la base de données

```bash
python manage.py migrate

# Créer un superuser (optionnel)
python manage.py createsuperuser

# Ajouter des données de test
python manage.py shell
```

Dans le shell Python :

```python
from irrigation.models import Plant, SoilType

# Créer des plantes
Plant.objects.create(name="Tomate", water_need=2.5, description="Légume d'été")
Plant.objects.create(name="Salade", water_need=1.5, description="Légume feuille")
Plant.objects.create(name="Courgette", water_need=3.0, description="Cucurbitacée")

# Créer des types de sol
SoilType.objects.create(name="Argileux", water_retention=0.8, description="Sol lourd retenant l'eau")
SoilType.objects.create(name="Sableux", water_retention=0.3, description="Sol drainant")
SoilType.objects.create(name="Limoneux", water_retention=0.5, description="Sol équilibré")
```

#### Lancer le serveur

```bash
python manage.py runserver

# L'API est disponible sur http://localhost:8000/api/
```

### 3. ESP32

1. Ouvrir `esp32/soil_sensor.ino` dans Arduino IDE
2. Installer les bibliothèques requises :
   - **PubSubClient** (MQTT)
   - **ArduinoJson**
3. Configurer dans le code :
   - `WIFI_SSID` et `WIFI_PASSWORD`
   - `MQTT_BROKER` (IP du serveur EMQX)
   - `PLOT_ID` (identifiant unique)
   - Calibrer `SOIL_DRY_VALUE` et `SOIL_WET_VALUE`
4. Téléverser sur l'ESP32

#### Calibration du capteur

```cpp
// Dans setup(), ajouter :
calibrateSensor();

// Plonger le capteur dans l'eau → noter la valeur WET
// Sécher le capteur → noter la valeur DRY
// Mettre à jour les constantes
```

### 4. Application Flutter

```bash
cd flutter_app

# Installer les dépendances
flutter pub get

# Configurer l'URL de l'API dans main.dart
final String apiBaseUrl = 'http://VOTRE_IP:8000/api';

# Lancer l'application
flutter run
```

#### Permissions Android

Dans `android/app/src/main/AndroidManifest.xml` :

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

### 5. Entraînement IA (Optionnel)

```bash
cd scripts

# Installer les dépendances supplémentaires
pip install scikit-learn xgboost pandas numpy joblib

# Entraîner le modèle
python train_model.py

# Le modèle sera sauvegardé dans backend/models/watering_model.pkl
```

Activer l'IA dans `.env` :

```bash
USE_AI_MODEL=True
AI_MODEL_PATH=./models/watering_model.pkl
```

## 📡 API Endpoints

### Plantes

```bash
GET  /api/plants/           # Liste des plantes
GET  /api/plants/{id}/      # Détail d'une plante
```

### Types de Sol

```bash
GET  /api/soil-types/       # Liste des types de sol
GET  /api/soil-types/{id}/  # Détail d'un type
```

### Parcelles

```bash
GET     /api/plots/         # Liste des parcelles
POST    /api/plots/         # Créer une parcelle
GET     /api/plots/{id}/    # Détail d'une parcelle
PUT     /api/plots/{id}/    # Modifier une parcelle
DELETE  /api/plots/{id}/    # Supprimer une parcelle
GET     /api/plots/{id}/readings/     # Lectures capteur
GET     /api/plots/{id}/current_plan/ # Plan actuel
```

### Génération de Plan

```bash
GET  /api/generate_plan/{plot_id}/  # Générer un plan d'arrosage
```

### Lectures Capteurs

```bash
GET  /api/readings/?plot_id={id}  # Lectures filtrées par parcelle
```

## 🔧 Exemples d'utilisation

### Créer une parcelle (cURL)

```bash
curl -X POST http://localhost:8000/api/plots/ \
  -H "Content-Type: application/json" \
  -d '{
    "plot_id": "plot_001",
    "plant_name": "Tomate",
    "soil_type_name": "Limoneux",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "area_m2": 10.0,
    "user_name": "Jean Dupont"
  }'
```

### Générer un plan d'arrosage

```bash
curl http://localhost:8000/api/generate_plan/plot_001/
```

**Réponse JSON :**

```json
{
  "plot_id": "plot_001",
  "plant_name": "Tomate",
  "week_start": "2025-11-06",
  "plan": {
    "day_1": {
      "date": "2025-11-06",
      "volume_l": 2.5,
      "duration_min": 5.0,
      "rain_forecast_mm": 0.0,
      "temp_avg": 22.0
    },
    "day_2": { ... },
    ...
  },
  "avg_soil_humidity": 45.2,
  "total_rain_forecast": 12.5,
  "generated_at": "2025-11-06T17:09:21Z"
}
```

### Simuler un capteur ESP32 (Python)

```python
import paho.mqtt.client as mqtt
import json
import time

client = mqtt.Client()
client.connect("localhost", 1883)

while True:
    data = {
        "plot_id": "plot_001",
        "soil_humidity": 45.5
    }
    client.publish("farmboy/sensors/plot1", json.dumps(data))
    print(f"Publié: {data}")
    time.sleep(60)
```

## 📊 Logique de Calcul d'Arrosage

Le système utilise des règles expertes pour calculer le volume d'arrosage :

1. **Base** : Besoin en eau de la plante (ex: 2.5L pour tomate)
2. **Ajustement humidité du sol** :
   - < 20% : +50%
   - < 30% : +20%
   - \> 70% : -50%
   - \> 50% : -20%
3. **Ajustement pluie** :
   - \> 15mm : -70%
   - \> 5mm : -50%
   - \> 1mm : -30%
4. **Ajustement sol** :
   - Drainant (< 0.3) : +20%
   - Retenant (> 0.7) : -10%
5. **Ajustement température** :
   - \> 30°C : +30%
   - \> 25°C : +15%
   - < 15°C : -20%

## 🔒 Sécurité

- ⚠️ **Production** : Changer `SECRET_KEY` et `DEBUG=False`
- Utiliser HTTPS pour l'API
- Activer l'authentification MQTT
- Sécuriser MongoDB avec authentification
- Valider toutes les entrées utilisateur

## 🐛 Dépannage

### MQTT ne reçoit pas de données

1. Vérifier que EMQX est démarré : `docker ps`
2. Tester avec un client MQTT : `mosquitto_sub -t "farmboy/sensors/#"`
3. Vérifier les logs Django
4. Vérifier la configuration ESP32

### Erreur MongoDB

```bash
# Vérifier que MongoDB est démarré
sudo systemctl status mongod

# Vérifier la connexion
mongo --eval "db.adminCommand('ping')"
```

### Erreur OpenWeather API

- Vérifier que la clé API est valide
- Tester l'API : `curl "https://api.openweathermap.org/data/2.5/forecast?lat=48.8566&lon=2.3522&appid=VOTRE_CLE"`

## 📝 TODO / Améliorations

- [ ] Authentification JWT pour l'API
- [ ] Webhooks pour notifications
- [ ] Graphiques historiques dans Flutter
- [ ] Contrôle d'électrovanne depuis l'app
- [ ] Mode offline Flutter
- [ ] Tests unitaires et d'intégration
- [ ] Docker Compose pour déploiement
- [ ] Dashboard web React/Vue

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

MIT License - Voir LICENSE pour plus de détails

## 👨‍💻 Auteur

Projet créé pour démonstration d'un système IoT complet avec IA.

---

**🌟 N'oubliez pas de donner une étoile si ce projet vous a été utile !**
