import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Plant, SoilType, UserPlot, SensorReading, WateringPlan
from .serializers import (
    PlantSerializer, SoilTypeSerializer, UserPlotSerializer,
    UserPlotCreateSerializer, SensorReadingSerializer, WateringPlanSerializer
)
from .watering_plan_service import watering_plan_service

logger = logging.getLogger(__name__)


class PlantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour lister les plantes disponibles"""
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer


class SoilTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour lister les types de sol disponibles"""
    queryset = SoilType.objects.all()
    serializer_class = SoilTypeSerializer


class UserPlotViewSet(viewsets.ModelViewSet):
    """API endpoint pour gérer les parcelles utilisateur"""
    queryset = UserPlot.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserPlotCreateSerializer
        return UserPlotSerializer
    
    def create(self, request, *args, **kwargs):
        """Créer une nouvelle parcelle"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plot = serializer.save()
        
        # Retourner avec le serializer de lecture
        output_serializer = UserPlotSerializer(plot)
        
        logger.info(f"✓ Parcelle créée: {plot.plot_id}")
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def readings(self, request, pk=None):
        """Récupérer les dernières lectures de capteur pour une parcelle"""
        plot = self.get_object()
        limit = int(request.query_params.get('limit', 50))
        
        readings = SensorReading.objects.filter(plot=plot)[:limit]
        serializer = SensorReadingSerializer(readings, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def current_plan(self, request, pk=None):
        """Récupérer le plan d'arrosage actuel pour une parcelle"""
        plot = self.get_object()
        
        try:
            plan = WateringPlan.objects.filter(plot=plot).first()
            if plan:
                serializer = WateringPlanSerializer(plan)
                return Response(serializer.data)
            else:
                return Response(
                    {'message': 'Aucun plan disponible'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"✗ Erreur récupération plan: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SensorReadingViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint pour consulter les lectures de capteurs"""
    queryset = SensorReading.objects.all()
    serializer_class = SensorReadingSerializer
    
    def get_queryset(self):
        queryset = SensorReading.objects.all()
        
        # Filtrer par plot_id si fourni
        plot_id = self.request.query_params.get('plot_id', None)
        if plot_id:
            queryset = queryset.filter(plot__plot_id=plot_id)
        
        return queryset


@api_view(['GET', 'POST'])
def generate_watering_plan(request, plot_id):
    """
    Générer un plan d'arrosage hebdomadaire pour une parcelle
    
    GET /api/generate_plan/<plot_id>/ - Générer et retourner le plan
    """
    try:
        # Vérifier que la parcelle existe
        plot = get_object_or_404(UserPlot, plot_id=plot_id)
        
        logger.info(f"📋 Demande de génération de plan pour: {plot_id}")
        
        # Générer le plan
        plan_data = watering_plan_service.generate_plan(plot_id)
        
        return Response(plan_data, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"✗ Erreur validation: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"✗ Erreur génération plan: {e}")
        return Response(
            {'error': 'Erreur lors de la génération du plan'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """Endpoint de santé pour vérifier que l'API fonctionne"""
    return Response({
        'status': 'healthy',
        'service': 'Smart Irrigation Backend',
        'version': '1.0.0'
    })
