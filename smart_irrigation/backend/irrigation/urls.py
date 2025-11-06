from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'plants', views.PlantViewSet, basename='plant')
router.register(r'soil-types', views.SoilTypeViewSet, basename='soiltype')
router.register(r'plots', views.UserPlotViewSet, basename='plot')
router.register(r'readings', views.SensorReadingViewSet, basename='reading')

urlpatterns = [
    path('', include(router.urls)),
    path('generate_plan/<str:plot_id>/', views.generate_watering_plan, name='generate_plan'),
    path('health/', views.health_check, name='health_check'),
]
