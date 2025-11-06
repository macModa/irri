from django.contrib import admin
from .models import Plant, SoilType, UserPlot, SensorReading, WateringPlan, WeatherCache


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ['name', 'water_need', 'created_at']
    search_fields = ['name']


@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'water_retention', 'created_at']
    search_fields = ['name']


@admin.register(UserPlot)
class UserPlotAdmin(admin.ModelAdmin):
    list_display = ['plot_id', 'plant', 'soil_type', 'user_name', 'created_at']
    search_fields = ['plot_id', 'user_name']
    list_filter = ['plant', 'soil_type']


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['plot', 'soil_humidity', 'timestamp']
    list_filter = ['plot', 'timestamp']
    date_hierarchy = 'timestamp'


@admin.register(WateringPlan)
class WateringPlanAdmin(admin.ModelAdmin):
    list_display = ['plot', 'week_start', 'avg_soil_humidity', 'total_rain_forecast', 'generated_at']
    list_filter = ['week_start', 'generated_at']
    date_hierarchy = 'generated_at'


@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ['latitude', 'longitude', 'fetched_at']
    date_hierarchy = 'fetched_at'
