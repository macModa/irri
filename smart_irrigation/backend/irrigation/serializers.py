from rest_framework import serializers
from .models import Plant, SoilType, UserPlot, SensorReading, WateringPlan


class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = ['id', 'name', 'water_need', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class SoilTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilType
        fields = ['id', 'name', 'water_retention', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserPlotSerializer(serializers.ModelSerializer):
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    soil_type_name = serializers.CharField(source='soil_type.name', read_only=True)
    
    class Meta:
        model = UserPlot
        fields = [
            'id', 'plot_id', 'plant', 'plant_name', 
            'soil_type', 'soil_type_name', 'latitude', 'longitude',
            'area_m2', 'user_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserPlotCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de parcelles depuis Flutter"""
    plant_name = serializers.CharField(write_only=True)
    soil_type_name = serializers.CharField(write_only=True)
    
    class Meta:
        model = UserPlot
        fields = [
            'plot_id', 'plant_name', 'soil_type_name',
            'latitude', 'longitude', 'area_m2', 'user_name'
        ]
    
    def validate_plant_name(self, value):
        """Valider que la plante existe"""
        if not Plant.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(f"Plante '{value}' introuvable")
        return value
    
    def validate_soil_type_name(self, value):
        """Valider que le type de sol existe"""
        if not SoilType.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError(f"Type de sol '{value}' introuvable")
        return value
    
    def create(self, validated_data):
        plant_name = validated_data.pop('plant_name')
        soil_type_name = validated_data.pop('soil_type_name')
        
        plant = Plant.objects.get(name__iexact=plant_name)
        soil_type = SoilType.objects.get(name__iexact=soil_type_name)
        
        validated_data['plant'] = plant
        validated_data['soil_type'] = soil_type
        
        return UserPlot.objects.create(**validated_data)


class SensorReadingSerializer(serializers.ModelSerializer):
    plot_id = serializers.CharField(source='plot.plot_id', read_only=True)
    
    class Meta:
        model = SensorReading
        fields = ['id', 'plot_id', 'soil_humidity', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class WateringPlanSerializer(serializers.ModelSerializer):
    plot_id = serializers.CharField(source='plot.plot_id', read_only=True)
    plant_name = serializers.CharField(source='plot.plant.name', read_only=True)
    
    class Meta:
        model = WateringPlan
        fields = [
            'id', 'plot_id', 'plant_name', 'week_start', 'plan',
            'avg_soil_humidity', 'total_rain_forecast', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']
