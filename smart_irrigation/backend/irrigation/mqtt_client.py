import json
import logging
import os
import paho.mqtt.client as mqtt
from django.utils import timezone
from .models import UserPlot, SensorReading

logger = logging.getLogger(__name__)


class MQTTClient:
    """Client MQTT pour écouter les données des capteurs ESP32"""
    
    def __init__(self):
        self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.username = os.getenv('MQTT_USERNAME', '')
        self.password = os.getenv('MQTT_PASSWORD', '')
        self.topic = os.getenv('MQTT_TOPIC', 'farmboy/sensors/#')
        
        self.client = mqtt.Client(client_id="django_backend")
        
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback appelé lors de la connexion au broker"""
        if rc == 0:
            logger.info(f"✓ Connecté au broker MQTT {self.broker_host}:{self.broker_port}")
            client.subscribe(self.topic)
            logger.info(f"✓ Souscrit au topic: {self.topic}")
        else:
            logger.error(f"✗ Échec de connexion MQTT, code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback appelé lors de la déconnexion"""
        if rc != 0:
            logger.warning(f"⚠ Déconnexion inattendue du broker MQTT. Tentative de reconnexion...")
    
    def on_message(self, client, userdata, msg):
        """Callback appelé lors de la réception d'un message"""
        try:
            # Décoder le payload JSON
            payload = json.loads(msg.payload.decode('utf-8'))
            logger.info(f"📨 Message reçu sur {msg.topic}: {payload}")
            
            # Validation des données
            if 'plot_id' not in payload or 'soil_humidity' not in payload:
                logger.error(f"✗ Format de message invalide: {payload}")
                return
            
            plot_id = payload['plot_id']
            soil_humidity = float(payload['soil_humidity'])
            
            # Validation de l'humidité
            if not (0 <= soil_humidity <= 100):
                logger.error(f"✗ Valeur d'humidité invalide: {soil_humidity}%")
                return
            
            # Rechercher la parcelle
            try:
                plot = UserPlot.objects.get(plot_id=plot_id)
            except UserPlot.DoesNotExist:
                logger.error(f"✗ Parcelle introuvable: {plot_id}")
                return
            
            # Enregistrer la lecture
            reading = SensorReading.objects.create(
                plot=plot,
                soil_humidity=soil_humidity,
                timestamp=timezone.now()
            )
            
            logger.info(f"✓ Lecture enregistrée: {plot_id} - {soil_humidity}% [ID: {reading.id}]")
            
        except json.JSONDecodeError as e:
            logger.error(f"✗ Erreur de décodage JSON: {e}")
        except ValueError as e:
            logger.error(f"✗ Erreur de conversion: {e}")
        except Exception as e:
            logger.error(f"✗ Erreur lors du traitement du message: {e}")
    
    def connect(self):
        """Connecter au broker MQTT"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            logger.info(f"🔗 Tentative de connexion à {self.broker_host}:{self.broker_port}")
        except Exception as e:
            logger.error(f"✗ Erreur de connexion MQTT: {e}")
            raise
    
    def start(self):
        """Démarrer la boucle MQTT (non-bloquant)"""
        self.connect()
        self.client.loop_start()
        logger.info("✓ Boucle MQTT démarrée")
    
    def stop(self):
        """Arrêter le client MQTT"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("✓ Client MQTT arrêté")


# Instance globale du client MQTT
mqtt_client = None


def start_mqtt_client():
    """Fonction pour démarrer le client MQTT"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = MQTTClient()
        mqtt_client.start()
    return mqtt_client


def stop_mqtt_client():
    """Fonction pour arrêter le client MQTT"""
    global mqtt_client
    if mqtt_client is not None:
        mqtt_client.stop()
        mqtt_client = None
