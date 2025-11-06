import os
import logging
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from .models import WeatherCache

logger = logging.getLogger(__name__)


class WeatherService:
    """Service pour récupérer les prévisions météo depuis OpenWeather API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        if not self.api_key:
            logger.warning("⚠ OPENWEATHER_API_KEY non configurée")
        
        self.base_url = "https://api.openweathermap.org/data/2.5/forecast"
        self.cache_duration_hours = 3  # Cache valide pendant 3 heures
    
    def get_forecast(self, latitude, longitude, use_cache=True):
        """
        Récupérer les prévisions météo pour une localisation
        
        Args:
            latitude (float): Latitude
            longitude (float): Longitude
            use_cache (bool): Utiliser le cache si disponible
            
        Returns:
            dict: Prévisions météo sur 7 jours avec pluie, température, humidité
        """
        # Vérifier le cache
        if use_cache:
            cached_data = self._get_from_cache(latitude, longitude)
            if cached_data:
                logger.info(f"✓ Données météo récupérées depuis le cache ({latitude},{longitude})")
                return cached_data
        
        # Récupérer depuis l'API
        if not self.api_key:
            logger.error("✗ Impossible de récupérer la météo: API key manquante")
            return self._get_default_forecast()
        
        try:
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': self.api_key,
                'units': 'metric',  # Celsius
                'cnt': 40  # 5 jours * 8 prévisions/jour (toutes les 3h)
            }
            
            logger.info(f"🌤 Récupération météo pour ({latitude},{longitude})")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            forecast = self._parse_forecast(data)
            
            # Sauvegarder dans le cache
            self._save_to_cache(latitude, longitude, forecast)
            
            logger.info(f"✓ Prévisions météo récupérées avec succès")
            return forecast
            
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Erreur API OpenWeather: {e}")
            return self._get_default_forecast()
        except Exception as e:
            logger.error(f"✗ Erreur lors du traitement de la météo: {e}")
            return self._get_default_forecast()
    
    def _parse_forecast(self, data):
        """Parser les données de l'API OpenWeather"""
        daily_forecast = {}
        
        for item in data.get('list', []):
            # Date de la prévision
            dt = datetime.fromtimestamp(item['dt'])
            date_key = dt.strftime('%Y-%m-%d')
            
            # Initialiser le jour si nécessaire
            if date_key not in daily_forecast:
                daily_forecast[date_key] = {
                    'rain_mm': 0,
                    'temp_c': [],
                    'humidity': []
                }
            
            # Pluie (en mm)
            rain = item.get('rain', {}).get('3h', 0)  # Pluie sur 3h
            daily_forecast[date_key]['rain_mm'] += rain
            
            # Température
            temp = item.get('main', {}).get('temp', 20)
            daily_forecast[date_key]['temp_c'].append(temp)
            
            # Humidité de l'air
            humidity = item.get('main', {}).get('humidity', 50)
            daily_forecast[date_key]['humidity'].append(humidity)
        
        # Calculer les moyennes
        for date_key in daily_forecast:
            temps = daily_forecast[date_key]['temp_c']
            humidities = daily_forecast[date_key]['humidity']
            
            daily_forecast[date_key]['temp_avg'] = sum(temps) / len(temps) if temps else 20
            daily_forecast[date_key]['temp_max'] = max(temps) if temps else 25
            daily_forecast[date_key]['humidity_avg'] = sum(humidities) / len(humidities) if humidities else 50
            
            # Nettoyer les listes temporaires
            del daily_forecast[date_key]['temp_c']
            del daily_forecast[date_key]['humidity']
        
        # Limiter aux 7 prochains jours
        sorted_dates = sorted(daily_forecast.keys())[:7]
        result = {date: daily_forecast[date] for date in sorted_dates}
        
        return result
    
    def _get_default_forecast(self):
        """Retourner une prévision par défaut en cas d'erreur"""
        logger.warning("⚠ Utilisation des prévisions météo par défaut")
        default_forecast = {}
        
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            default_forecast[date] = {
                'rain_mm': 2.0,  # Pluie modérée par défaut
                'temp_avg': 22.0,
                'temp_max': 28.0,
                'humidity_avg': 60.0
            }
        
        return default_forecast
    
    def _get_from_cache(self, latitude, longitude):
        """Récupérer depuis le cache MongoDB"""
        try:
            cache = WeatherCache.objects.get(
                latitude=round(latitude, 4),
                longitude=round(longitude, 4)
            )
            
            # Vérifier si le cache est encore valide
            time_diff = timezone.now() - cache.fetched_at
            if time_diff.total_seconds() / 3600 < self.cache_duration_hours:
                return cache.forecast_data
            else:
                logger.info("⏱ Cache météo expiré")
                cache.delete()
                
        except WeatherCache.DoesNotExist:
            pass
        
        return None
    
    def _save_to_cache(self, latitude, longitude, forecast_data):
        """Sauvegarder dans le cache MongoDB"""
        try:
            WeatherCache.objects.update_or_create(
                latitude=round(latitude, 4),
                longitude=round(longitude, 4),
                defaults={'forecast_data': forecast_data}
            )
            logger.info("✓ Données météo mises en cache")
        except Exception as e:
            logger.error(f"✗ Erreur lors de la sauvegarde du cache: {e}")


# Instance globale du service météo
weather_service = WeatherService()
