from djongo import models
from django.utils import timezone


class Plant(models.Model):
    """Modèle représentant un type de plante"""
    _id = models.ObjectIdField()
    name = models.CharField(max_length=100, unique=True)
    water_need = models.FloatField(help_text="Besoin en eau quotidien moyen (litres)")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "plants"
    
    def __str__(self):
        return self.name


class SoilType(models.Model):
    """Modèle représentant un type de sol"""
    _id = models.ObjectIdField()
    name = models.CharField(max_length=100, unique=True)
    water_retention = models.FloatField(help_text="Capacité de rétention d'eau (0.0 à 1.0)")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "soil_types"
    
    def __str__(self):
        return self.name


class UserPlot(models.Model):
    """Modèle représentant une parcelle utilisateur"""
    _id = models.ObjectIdField()
    plot_id = models.CharField(max_length=50, unique=True, help_text="Identifiant unique de la parcelle")
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='plots')
    soil_type = models.ForeignKey(SoilType, on_delete=models.CASCADE, related_name='plots')
    latitude = models.FloatField()
    longitude = models.FloatField()
    area_m2 = models.FloatField(default=10.0, help_text="Surface de la parcelle en m²")
    user_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "user_plots"
    
    def __str__(self):
        return f"{self.plot_id} - {self.plant.name}"


class SensorReading(models.Model):
    """Modèle représentant une lecture de capteur"""
    _id = models.ObjectIdField()
    plot = models.ForeignKey(UserPlot, on_delete=models.CASCADE, related_name='readings')
    soil_humidity = models.FloatField(help_text="Humidité du sol en %")
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = "sensor_readings"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.plot.plot_id} - {self.soil_humidity}% @ {self.timestamp}"


class WateringPlan(models.Model):
    """Modèle représentant un plan d'arrosage hebdomadaire"""
    _id = models.ObjectIdField()
    plot = models.ForeignKey(UserPlot, on_delete=models.CASCADE, related_name='watering_plans')
    week_start = models.DateField(help_text="Date de début de la semaine")
    plan = models.JSONField(help_text="Plan d'arrosage par jour (JSON)")
    avg_soil_humidity = models.FloatField(null=True, blank=True)
    total_rain_forecast = models.FloatField(null=True, blank=True, help_text="Pluie totale prévue (mm)")
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "watering_plans"
        ordering = ['-generated_at']
        unique_together = ['plot', 'week_start']
    
    def __str__(self):
        return f"Plan {self.plot.plot_id} - Semaine {self.week_start}"


class WeatherCache(models.Model):
    """Cache pour les données météo"""
    _id = models.ObjectIdField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    forecast_data = models.JSONField()
    fetched_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "weather_cache"
        unique_together = ['latitude', 'longitude']
    
    def __str__(self):
        return f"Weather {self.latitude},{self.longitude}"
