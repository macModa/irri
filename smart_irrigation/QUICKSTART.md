# 🚀 Guide de démarrage rapide - Smart Irrigation

Ce guide vous permet de lancer le projet en moins de 10 minutes.

## ⚡ Installation Express

### 1. Services (Docker recommandé)

```bash
# MongoDB
docker run -d -p 27017:27017 --name mongodb mongo:latest

# EMQX (broker MQTT)
docker run -d --name emqx \
  -p 1883:1883 \
  -p 18083:18083 \
  emqx/emqx:latest
```

### 2. Backend Django

```bash
cd backend

# Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation
pip install -r requirements.txt

# Configuration
cp .env.example .env
nano .env  # Éditer avec votre clé OpenWeather

# Base de données
python manage.py migrate

# Données de test
python init_data.py

# Lancer
python manage.py runserver
```

### 3. Test rapide

```bash
# Vérifier que l'API fonctionne
curl http://localhost:8000/api/health/

# Lister les plantes
curl http://localhost:8000/api/plants/

# Générer un plan pour la parcelle d'exemple
curl http://localhost:8000/api/generate_plan/plot_001/
```

## 🧪 Tester sans ESP32

Script Python pour simuler un capteur :

```python
# test_mqtt.py
import paho.mqtt.client as mqtt
import json
import time
import random

client = mqtt.Client()
client.connect("localhost", 1883)

while True:
    humidity = random.uniform(20, 80)
    data = {
        "plot_id": "plot_001",
        "soil_humidity": round(humidity, 1)
    }
    client.publish("farmboy/sensors/plot1", json.dumps(data))
    print(f"📤 Publié: {data}")
    time.sleep(10)
```

Lancer avec : `python test_mqtt.py`

## 📱 Application Flutter (optionnel)

```bash
cd flutter_app

# Éditer main.dart ligne 31
# Remplacer par l'IP de votre serveur
final String apiBaseUrl = 'http://192.168.1.X:8000/api';

flutter pub get
flutter run
```

## 🔍 Vérifications

### EMQX Dashboard
- URL : http://localhost:18083
- Login : admin / public

### Django Admin
- URL : http://localhost:8000/admin/
- Créer un user : `python manage.py createsuperuser`

### API Browsable
- URL : http://localhost:8000/api/

## 🎯 Prochaines étapes

1. **Clé OpenWeather** : Inscrivez-vous sur https://openweathermap.org/api
2. **ESP32** : Flashez le code Arduino sur votre ESP32
3. **Flutter** : Testez l'application mobile

## 🐛 Problèmes courants

**MongoDB ne démarre pas**
```bash
docker logs mongodb
docker restart mongodb
```

**MQTT ne reçoit pas**
```bash
# Tester avec mosquitto
mosquitto_sub -h localhost -t "farmboy/sensors/#" -v
```

**Port 8000 déjà utilisé**
```bash
python manage.py runserver 8001
```

## 📚 Documentation complète

Voir `README.md` pour la documentation complète.
