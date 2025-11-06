# 🏗️ Architecture du Système Smart Irrigation

## 📊 Vue d'ensemble

```
┌─────────────────┐
│                 │
│   ESP32 + DHT   │  ──┐
│   (Capteur sol) │    │
│                 │    │
└─────────────────┘    │
                       │
                       │ MQTT/EMQX
                       │ (Port 1883)
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                                              │
│          BACKEND DJANGO (Python)             │
│                                              │
│  ┌─────────────┐  ┌──────────────┐         │
│  │ MQTT Client │  │  Weather API │         │
│  │  Service    │  │   Service    │         │
│  └─────────────┘  └──────────────┘         │
│         │                  │                 │
│         └──────┬───────────┘                │
│                │                             │
│         ┌──────▼────────┐                   │
│         │  Watering     │                   │
│         │  Plan Service │                   │
│         │  (IA/Règles)  │                   │
│         └───────────────┘                   │
│                │                             │
│         ┌──────▼────────┐                   │
│         │   REST API    │                   │
│         │   (DRF)       │                   │
│         └───────────────┘                   │
│                                              │
└──────────────────┬───────────────────────────┘
                   │
                   │ MongoDB
                   │ (Port 27017)
                   │
         ┌─────────▼─────────┐
         │                   │
         │     MONGODB       │
         │   (Base NoSQL)    │
         │                   │
         └───────────────────┘
                   │
                   │ HTTP/REST
                   │ (Port 8000)
                   │
         ┌─────────▼─────────┐
         │                   │
         │  FLUTTER APP      │
         │  (Mobile/Web)     │
         │                   │
         └───────────────────┘
```

## 🔄 Flux de données

### 1. Capture des données (ESP32 → Backend)

```
ESP32 (Capteur sol)
    │
    │ Lecture analogique → Conversion %
    │
    ▼
JSON: {plot_id, soil_humidity}
    │
    │ Publish MQTT
    │ Topic: farmboy/sensors/plotX
    │
    ▼
Broker EMQX (Port 1883)
    │
    │ Subscribe
    │
    ▼
Django MQTT Client (mqtt_client.py)
    │
    │ Validation & Parse JSON
    │
    ▼
MongoDB (SensorReading)
```

### 2. Génération du plan d'arrosage

```
Flutter App / API Request
    │
    │ GET /api/generate_plan/plot_001/
    │
    ▼
Django View (views.py)
    │
    ▼
WateringPlanService (watering_plan_service.py)
    │
    ├──► Récupère humidité moyenne (MongoDB)
    │    SELECT AVG(soil_humidity) FROM readings WHERE plot_id=...
    │
    ├──► Appelle Weather Service
    │    │
    │    └──► OpenWeather API
    │         GET forecast?lat=X&lon=Y
    │         └──► Cache MongoDB (3h)
    │
    ├──► Calcul intelligent
    │    │
    │    ├──► Mode Règles expertes
    │    │    • Base: besoin plante
    │    │    • Ajuste: humidité, pluie, sol, temp
    │    │    • Facteur multiplicatif
    │    │
    │    └──► Mode IA (optionnel)
    │         • Load model.pkl
    │         • Predict([humidity, rain, temp, ...])
    │
    ▼
Plan JSON (7 jours)
{
  "day_1": {volume_l, duration_min, rain_mm, temp},
  "day_2": {...},
  ...
}
    │
    ├──► Sauvegarde MongoDB (WateringPlan)
    │
    ▼
Response JSON → Flutter App
```

### 3. Interface utilisateur (Flutter)

```
Flutter App Startup
    │
    ├──► GET /api/plants/
    │    └──► Liste des plantes disponibles
    │
    ├──► GET /api/soil-types/
    │    └──► Liste des types de sol
    │
    ▼
Utilisateur saisit:
• plot_id
• plant (dropdown)
• soil_type (dropdown)
• GPS location (auto)
    │
    ▼
POST /api/plots/
{
  plot_id, plant_name, soil_type_name,
  latitude, longitude, area_m2
}
    │
    ▼
Django crée UserPlot
    │
    ▼
GET /api/generate_plan/plot_001/
    │
    ▼
Affichage plan hebdomadaire
```

## 🗄️ Modèle de données MongoDB

### Collections

```
plants
├── _id: ObjectId
├── name: String (unique)
├── water_need: Float (litres/jour)
├── description: String
└── created_at: DateTime

soil_types
├── _id: ObjectId
├── name: String (unique)
├── water_retention: Float (0.0-1.0)
├── description: String
└── created_at: DateTime

user_plots
├── _id: ObjectId
├── plot_id: String (unique)
├── plant: Reference → plants
├── soil_type: Reference → soil_types
├── latitude: Float
├── longitude: Float
├── area_m2: Float
├── user_name: String
└── created_at: DateTime

sensor_readings
├── _id: ObjectId
├── plot: Reference → user_plots
├── soil_humidity: Float (%)
└── timestamp: DateTime

watering_plans
├── _id: ObjectId
├── plot: Reference → user_plots
├── week_start: Date
├── plan: JSON {day_1: {...}, ...}
├── avg_soil_humidity: Float
├── total_rain_forecast: Float
└── generated_at: DateTime

weather_cache
├── _id: ObjectId
├── latitude: Float
├── longitude: Float
├── forecast_data: JSON
└── fetched_at: DateTime
```

## 🧩 Modules Backend

### models.py
- **Rôle** : Définition des schémas de données
- **ORM** : Djongo (Django + MongoDB)
- **Relations** : ForeignKey entre collections

### mqtt_client.py
- **Rôle** : Écoute du broker MQTT
- **Bibliothèque** : paho-mqtt
- **Thread** : Loop asynchrone (loop_start)
- **Callback** : on_message → validation → save

### weather_service.py
- **Rôle** : Récupération prévisions météo
- **API** : OpenWeather Forecast API
- **Cache** : 3 heures dans MongoDB
- **Parse** : Agrégation par jour (rain, temp, humidity)

### watering_plan_service.py
- **Rôle** : Génération plans intelligents
- **Modes** :
  - Règles expertes (par défaut)
  - IA (RandomForest/XGBoost si activé)
- **Inputs** : soil_humidity, rain_forecast, temp, plant, soil
- **Output** : Plan 7 jours avec volume et durée

### views.py & serializers.py
- **Rôle** : API REST
- **Framework** : Django REST Framework
- **Endpoints** : CRUD + generate_plan
- **Validation** : Serializers avec validation métier

## 🤖 Module IA (Optionnel)

### train_model.py
```
Génération données synthétiques (10K samples)
    │
    ▼
Features: [soil_humidity, rain_mm, temp, plant_type, soil_type]
Target: [volume_l]
    │
    ├──► RandomForest (100 estimators)
    │    Train R² ≈ 0.95
    │    Test R² ≈ 0.93
    │
    └──► XGBoost (100 rounds)
         Train R² ≈ 0.97
         Test R² ≈ 0.95
    │
    ▼
Meilleur modèle → Sauvegarde (joblib)
backend/models/watering_model.pkl
```

### Activation
```bash
# .env
USE_AI_MODEL=True
AI_MODEL_PATH=./models/watering_model.pkl
```

## 📡 Communication MQTT

### Topics
```
farmboy/sensors/#              (Subscribe)
  └─ farmboy/sensors/plot1     (ESP32 → Backend)
  └─ farmboy/sensors/plot2
  └─ ...
```

### Payload JSON
```json
{
  "plot_id": "plot_001",
  "soil_humidity": 45.5,
  "timestamp": 1234567890  // optionnel
}
```

### QoS & Retained
- QoS 0 : At most once (suffisant pour données temps réel)
- Retained : Non (lectures continues)

## 🔐 Sécurité

### Production Checklist
- [ ] Django SECRET_KEY aléatoire
- [ ] DEBUG=False
- [ ] HTTPS (certificat SSL)
- [ ] MQTT authentification (username/password)
- [ ] MongoDB authentification
- [ ] Rate limiting API
- [ ] CORS configuré correctement
- [ ] Validation stricte des entrées
- [ ] Logs centralisés

## ⚡ Performance

### Optimisations
- **Cache météo** : 3h pour éviter surcharge API
- **Index MongoDB** : plot_id, timestamp
- **Pagination** : REST API (50 items/page)
- **MQTT loop** : Non-bloquant (thread)
- **Calcul plan** : Asynchrone possible (Celery)

### Scaling
```
Load Balancer
    │
    ├─► Django Instance 1 ─┐
    ├─► Django Instance 2 ─┼─► MongoDB Replica Set
    └─► Django Instance 3 ─┘
            │
            └──► EMQX Cluster
```

## 🧪 Testing

### Backend
```bash
# Tests unitaires
python manage.py test

# Coverage
coverage run --source='.' manage.py test
coverage report
```

### ESP32
```cpp
// Serial Monitor pour debug
Serial.println("Humidité: " + String(humidity) + "%");
```

### Flutter
```bash
flutter test
```

## 📈 Monitoring

### Métriques clés
- Nombre de lectures MQTT/min
- Latence API (ms)
- Plans générés/jour
- Taux d'erreur météo
- Occupation MongoDB

### Logs
```
backend/logs/django.log
- INFO: Lectures capteurs
- DEBUG: Calculs plans
- ERROR: Erreurs API/MQTT
```

---

**Architecture conçue pour être scalable, maintenable et extensible.**
