#!/usr/bin/env python
"""
Script pour initialiser les données de test dans la base de données
Usage: python init_data.py
"""

import os
import sys
import django

# Configuration Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from irrigation.models import Plant, SoilType, UserPlot


def init_plants():
    """Initialiser les plantes"""
    plants_data = [
        {"name": "Tomate", "water_need": 2.5, "description": "Légume d'été, besoin en eau moyen"},
        {"name": "Salade", "water_need": 1.5, "description": "Légume feuille, besoin en eau faible"},
        {"name": "Courgette", "water_need": 3.0, "description": "Cucurbitacée, besoin en eau élevé"},
        {"name": "Poivron", "water_need": 2.0, "description": "Légume fruit, besoin en eau moyen"},
        {"name": "Aubergine", "water_need": 2.8, "description": "Légume fruit, besoin en eau élevé"},
        {"name": "Concombre", "water_need": 3.5, "description": "Cucurbitacée, besoin en eau très élevé"},
        {"name": "Haricot", "water_need": 2.2, "description": "Légumineuse, besoin en eau moyen"},
        {"name": "Carotte", "water_need": 1.8, "description": "Légume racine, besoin en eau faible"},
    ]
    
    print("📦 Création des plantes...")
    for data in plants_data:
        plant, created = Plant.objects.get_or_create(
            name=data["name"],
            defaults={
                "water_need": data["water_need"],
                "description": data["description"]
            }
        )
        status = "✓ Créée" if created else "→ Existe déjà"
        print(f"  {status}: {plant.name} ({plant.water_need}L/jour)")


def init_soil_types():
    """Initialiser les types de sol"""
    soil_types_data = [
        {"name": "Argileux", "water_retention": 0.8, "description": "Sol lourd retenant bien l'eau"},
        {"name": "Sableux", "water_retention": 0.3, "description": "Sol drainant rapidement"},
        {"name": "Limoneux", "water_retention": 0.5, "description": "Sol équilibré"},
        {"name": "Humifère", "water_retention": 0.7, "description": "Sol riche en humus"},
        {"name": "Calcaire", "water_retention": 0.4, "description": "Sol léger et drainant"},
    ]
    
    print("\n📦 Création des types de sol...")
    for data in soil_types_data:
        soil_type, created = SoilType.objects.get_or_create(
            name=data["name"],
            defaults={
                "water_retention": data["water_retention"],
                "description": data["description"]
            }
        )
        status = "✓ Créé" if created else "→ Existe déjà"
        print(f"  {status}: {soil_type.name} (rétention: {soil_type.water_retention})")


def init_sample_plot():
    """Créer une parcelle d'exemple"""
    print("\n📦 Création d'une parcelle d'exemple...")
    
    try:
        plant = Plant.objects.get(name="Tomate")
        soil_type = SoilType.objects.get(name="Limoneux")
        
        plot, created = UserPlot.objects.get_or_create(
            plot_id="plot_001",
            defaults={
                "plant": plant,
                "soil_type": soil_type,
                "latitude": 48.8566,
                "longitude": 2.3522,
                "area_m2": 10.0,
                "user_name": "Utilisateur Demo"
            }
        )
        
        status = "✓ Créée" if created else "→ Existe déjà"
        print(f"  {status}: {plot.plot_id} - {plot.plant.name}")
        
    except Exception as e:
        print(f"  ✗ Erreur: {e}")


def main():
    print("=" * 60)
    print("🚀 Initialisation des données de test")
    print("=" * 60)
    print()
    
    init_plants()
    init_soil_types()
    init_sample_plot()
    
    print("\n" + "=" * 60)
    print("✅ Initialisation terminée avec succès!")
    print("=" * 60)
    print("\n💡 Vous pouvez maintenant:")
    print("  1. Lancer le serveur: python manage.py runserver")
    print("  2. Accéder à l'API: http://localhost:8000/api/")
    print("  3. Tester avec l'ESP32 ou Flutter")
    print()


if __name__ == "__main__":
    main()
