import os
import logging
from datetime import datetime, timedelta
from django.db.models import Avg
from .models import UserPlot, SensorReading, WateringPlan
from .weather_service import weather_service

logger = logging.getLogger(__name__)

# Importer les modules IA si disponibles
USE_AI_MODEL = os.getenv('USE_AI_MODEL', 'False').lower() == 'true'

if USE_AI_MODEL:
    try:
        import joblib
        import numpy as np
        AI_MODEL_PATH = os.getenv('AI_MODEL_PATH', './models/watering_model.pkl')
        logger.info(f"🤖 Mode IA activé - Chargement du modèle depuis {AI_MODEL_PATH}")
    except ImportError:
        USE_AI_MODEL = False
        logger.warning("⚠ Modules IA non disponibles, utilisation des règles")


class WateringPlanService:
    """Service pour générer des plans d'arrosage intelligents"""
    
    def __init__(self):
        self.use_ai = USE_AI_MODEL
        self.model = None
        
        if self.use_ai:
            self._load_ai_model()
    
    def _load_ai_model(self):
        """Charger le modèle IA pré-entraîné"""
        try:
            self.model = joblib.load(AI_MODEL_PATH)
            logger.info("✓ Modèle IA chargé avec succès")
        except Exception as e:
            logger.error(f"✗ Impossible de charger le modèle IA: {e}")
            self.use_ai = False
    
    def generate_plan(self, plot_id):
        """
        Générer un plan d'arrosage hebdomadaire pour une parcelle
        
        Args:
            plot_id (str): Identifiant de la parcelle
            
        Returns:
            dict: Plan d'arrosage avec structure JSON
        """
        try:
            # Récupérer la parcelle
            plot = UserPlot.objects.get(plot_id=plot_id)
            logger.info(f"🌱 Génération du plan pour: {plot_id} ({plot.plant.name})")
            
            # Récupérer l'humidité moyenne récente
            avg_soil_humidity = self._get_recent_soil_humidity(plot)
            
            # Récupérer les prévisions météo
            weather_forecast = weather_service.get_forecast(plot.latitude, plot.longitude)
            
            # Calculer la pluie totale prévue
            total_rain = sum(day['rain_mm'] for day in weather_forecast.values())
            
            # Générer le plan jour par jour
            week_start = datetime.now().date()
            daily_plan = {}
            
            for i in range(1, 8):
                date = (week_start + timedelta(days=i-1)).strftime('%Y-%m-%d')
                
                if date in weather_forecast:
                    day_weather = weather_forecast[date]
                else:
                    # Si pas de données météo pour ce jour, utiliser des valeurs par défaut
                    day_weather = {
                        'rain_mm': 2.0,
                        'temp_avg': 22.0,
                        'humidity_avg': 60.0
                    }
                
                # Calculer le volume d'arrosage
                if self.use_ai and self.model:
                    volume, duration = self._calculate_with_ai(
                        plot, avg_soil_humidity, day_weather
                    )
                else:
                    volume, duration = self._calculate_with_rules(
                        plot, avg_soil_humidity, day_weather
                    )
                
                daily_plan[f'day_{i}'] = {
                    'date': date,
                    'volume_l': round(volume, 2),
                    'duration_min': round(duration, 1),
                    'rain_forecast_mm': round(day_weather['rain_mm'], 1),
                    'temp_avg': round(day_weather['temp_avg'], 1)
                }
            
            # Sauvegarder le plan
            watering_plan = WateringPlan.objects.update_or_create(
                plot=plot,
                week_start=week_start,
                defaults={
                    'plan': daily_plan,
                    'avg_soil_humidity': avg_soil_humidity,
                    'total_rain_forecast': total_rain
                }
            )[0]
            
            logger.info(f"✓ Plan d'arrosage généré: {plot_id} - Semaine {week_start}")
            
            return {
                'plot_id': plot_id,
                'plant_name': plot.plant.name,
                'week_start': str(week_start),
                'plan': daily_plan,
                'avg_soil_humidity': round(avg_soil_humidity, 1) if avg_soil_humidity else None,
                'total_rain_forecast': round(total_rain, 1),
                'generated_at': watering_plan.generated_at.isoformat()
            }
            
        except UserPlot.DoesNotExist:
            logger.error(f"✗ Parcelle introuvable: {plot_id}")
            raise ValueError(f"Parcelle {plot_id} introuvable")
        except Exception as e:
            logger.error(f"✗ Erreur lors de la génération du plan: {e}")
            raise
    
    def _get_recent_soil_humidity(self, plot, hours=24):
        """Récupérer l'humidité moyenne des dernières heures"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        readings = SensorReading.objects.filter(
            plot=plot,
            timestamp__gte=cutoff_time
        )
        
        if readings.exists():
            avg_humidity = readings.aggregate(Avg('soil_humidity'))['soil_humidity__avg']
            logger.info(f"📊 Humidité moyenne (24h): {avg_humidity:.1f}%")
            return avg_humidity
        else:
            logger.warning(f"⚠ Aucune lecture récente pour {plot.plot_id}")
            return None
    
    def _calculate_with_rules(self, plot, soil_humidity, day_weather):
        """
        Calculer le volume d'arrosage avec des règles expertes
        
        Logique:
        - Base: besoin en eau de la plante
        - Ajuster selon humidité du sol
        - Ajuster selon pluie prévue
        - Ajuster selon type de sol (rétention d'eau)
        - Ajuster selon température
        """
        # Volume de base (besoin de la plante)
        base_volume = plot.plant.water_need
        
        # Facteur multiplicateur
        factor = 1.0
        
        # 1. Ajustement selon l'humidité du sol
        if soil_humidity is not None:
            if soil_humidity < 20:
                factor *= 1.5  # Sol très sec
                logger.debug("🔥 Sol très sec → +50%")
            elif soil_humidity < 30:
                factor *= 1.2  # Sol sec
                logger.debug("💧 Sol sec → +20%")
            elif soil_humidity > 70:
                factor *= 0.5  # Sol humide
                logger.debug("💦 Sol humide → -50%")
            elif soil_humidity > 50:
                factor *= 0.8  # Sol légèrement humide
                logger.debug("💧 Sol légèrement humide → -20%")
        
        # 2. Ajustement selon la pluie prévue
        rain_mm = day_weather.get('rain_mm', 0)
        if rain_mm > 15:
            factor *= 0.3  # Forte pluie
            logger.debug("🌧 Forte pluie → -70%")
        elif rain_mm > 5:
            factor *= 0.5  # Pluie modérée
            logger.debug("🌦 Pluie modérée → -50%")
        elif rain_mm > 1:
            factor *= 0.7  # Légère pluie
            logger.debug("🌦 Légère pluie → -30%")
        
        # 3. Ajustement selon le type de sol
        soil_retention = plot.soil_type.water_retention
        if soil_retention < 0.3:
            factor *= 1.2  # Sol drainant (sable)
            logger.debug("🏖 Sol drainant → +20%")
        elif soil_retention > 0.7:
            factor *= 0.9  # Sol retenant (argile)
            logger.debug("🧱 Sol retenant → -10%")
        
        # 4. Ajustement selon la température
        temp = day_weather.get('temp_avg', 22)
        if temp > 30:
            factor *= 1.3  # Très chaud
            logger.debug("🌡 Très chaud → +30%")
        elif temp > 25:
            factor *= 1.15  # Chaud
            logger.debug("🌡 Chaud → +15%")
        elif temp < 15:
            factor *= 0.8  # Frais
            logger.debug("🌡 Frais → -20%")
        
        # Calculer le volume final
        volume = base_volume * factor
        
        # S'assurer d'un minimum et maximum
        volume = max(0.5, min(volume, base_volume * 2))
        
        # Durée d'arrosage (supposer débit de 0.5 L/min)
        flow_rate = 0.5  # L/min
        duration = volume / flow_rate
        
        logger.debug(f"💧 Volume calculé: {volume:.2f}L (facteur: {factor:.2f})")
        
        return volume, duration
    
    def _calculate_with_ai(self, plot, soil_humidity, day_weather):
        """
        Calculer avec le modèle IA (si disponible)
        
        Features: [soil_humidity, rain_mm, temp_avg, plant_type_encoded, soil_type_encoded]
        """
        try:
            # Préparer les features
            features = np.array([[
                soil_humidity if soil_humidity is not None else 50,
                day_weather.get('rain_mm', 0),
                day_weather.get('temp_avg', 22),
                hash(plot.plant.name) % 100,  # Simple encoding
                hash(plot.soil_type.name) % 100
            ]])
            
            # Prédiction
            volume = self.model.predict(features)[0]
            
            # Durée
            flow_rate = 0.5
            duration = volume / flow_rate
            
            logger.debug(f"🤖 Volume prédit par IA: {volume:.2f}L")
            
            return volume, duration
            
        except Exception as e:
            logger.error(f"✗ Erreur prédiction IA: {e}, utilisation des règles")
            return self._calculate_with_rules(plot, soil_humidity, day_weather)


# Instance globale du service
watering_plan_service = WateringPlanService()
