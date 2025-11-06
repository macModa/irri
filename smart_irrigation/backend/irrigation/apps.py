from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class IrrigationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'irrigation'
    
    def ready(self):
        """Démarrer le client MQTT au lancement de l'application"""
        # Éviter les doubles imports lors du reload
        import sys
        if 'runserver' not in sys.argv:
            return
        
        # Démarrer le client MQTT
        try:
            from .mqtt_client import start_mqtt_client
            start_mqtt_client()
            logger.info("✓ Client MQTT démarré automatiquement")
        except Exception as e:
            logger.error(f"✗ Erreur démarrage client MQTT: {e}")
