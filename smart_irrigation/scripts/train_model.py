"""
Script d'entraînement d'un modèle IA pour prédire le volume d'arrosage optimal

Ce script génère des données synthétiques basées sur des règles expertes,
puis entraîne un modèle RandomForest ou XGBoost pour prédire le volume d'eau
nécessaire en fonction de:
- Humidité du sol
- Pluie prévue
- Température
- Type de plante
- Type de sol
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import joblib
import os


def generate_training_data(n_samples=10000):
    """
    Générer des données d'entraînement synthétiques basées sur des règles expertes
    
    Returns:
        DataFrame avec features et target
    """
    print(f"📊 Génération de {n_samples} échantillons...")
    
    np.random.seed(42)
    
    # Features
    soil_humidity = np.random.uniform(0, 100, n_samples)  # 0-100%
    rain_mm = np.random.exponential(5, n_samples)  # Distribution exponentielle pour la pluie
    rain_mm = np.clip(rain_mm, 0, 50)  # Limiter à 50mm max
    temp_avg = np.random.normal(22, 7, n_samples)  # Température moyenne ~22°C
    temp_avg = np.clip(temp_avg, 5, 40)
    
    # Types encodés (simple hash)
    plant_types = np.random.randint(0, 100, n_samples)  # 100 types de plantes possibles
    soil_types = np.random.randint(0, 100, n_samples)   # 100 types de sol possibles
    
    # Besoin en eau de base selon le type de plante (corrélé avec plant_type)
    base_water_need = 1.0 + (plant_types / 100) * 4.0  # Entre 1.0 et 5.0 L
    
    # Rétention d'eau selon le type de sol
    soil_retention = soil_types / 100  # Entre 0 et 1
    
    # Calculer le volume cible avec des règles expertes
    volume = []
    
    for i in range(n_samples):
        v = base_water_need[i]
        factor = 1.0
        
        # Ajustement humidité du sol
        if soil_humidity[i] < 20:
            factor *= 1.5
        elif soil_humidity[i] < 30:
            factor *= 1.2
        elif soil_humidity[i] > 70:
            factor *= 0.5
        elif soil_humidity[i] > 50:
            factor *= 0.8
        
        # Ajustement pluie
        if rain_mm[i] > 15:
            factor *= 0.3
        elif rain_mm[i] > 5:
            factor *= 0.5
        elif rain_mm[i] > 1:
            factor *= 0.7
        
        # Ajustement type de sol
        if soil_retention[i] < 0.3:
            factor *= 1.2  # Sol drainant
        elif soil_retention[i] > 0.7:
            factor *= 0.9  # Sol retenant
        
        # Ajustement température
        if temp_avg[i] > 30:
            factor *= 1.3
        elif temp_avg[i] > 25:
            factor *= 1.15
        elif temp_avg[i] < 15:
            factor *= 0.8
        
        # Calculer volume final
        v = v * factor
        v = max(0.5, min(v, base_water_need[i] * 2))  # Limites
        
        # Ajouter du bruit
        v += np.random.normal(0, 0.1)
        volume.append(max(0.1, v))
    
    # Créer DataFrame
    df = pd.DataFrame({
        'soil_humidity': soil_humidity,
        'rain_mm': rain_mm,
        'temp_avg': temp_avg,
        'plant_type': plant_types,
        'soil_type': soil_types,
        'volume_l': volume
    })
    
    print("✓ Données générées")
    print(f"  - Humidité sol: {df['soil_humidity'].min():.1f}-{df['soil_humidity'].max():.1f}%")
    print(f"  - Pluie: {df['rain_mm'].min():.1f}-{df['rain_mm'].max():.1f} mm")
    print(f"  - Température: {df['temp_avg'].min():.1f}-{df['temp_avg'].max():.1f}°C")
    print(f"  - Volume cible: {df['volume_l'].min():.2f}-{df['volume_l'].max():.2f} L")
    print()
    
    return df


def train_random_forest(X_train, X_test, y_train, y_test):
    """Entraîner un modèle RandomForest"""
    print("🌲 Entraînement RandomForest...")
    
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Prédictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Métriques
    print("\n📈 Métriques RandomForest:")
    print(f"  Train R²: {r2_score(y_train, y_pred_train):.4f}")
    print(f"  Test R²: {r2_score(y_test, y_pred_test):.4f}")
    print(f"  Test MAE: {mean_absolute_error(y_test, y_pred_test):.4f} L")
    print(f"  Test RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_test)):.4f} L")
    
    # Importance des features
    print("\n🔍 Importance des features:")
    feature_names = ['soil_humidity', 'rain_mm', 'temp_avg', 'plant_type', 'soil_type']
    for name, importance in zip(feature_names, model.feature_importances_):
        print(f"  {name}: {importance:.4f}")
    
    return model


def train_xgboost(X_train, X_test, y_train, y_test):
    """Entraîner un modèle XGBoost"""
    print("\n🚀 Entraînement XGBoost...")
    
    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Prédictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Métriques
    print("\n📈 Métriques XGBoost:")
    print(f"  Train R²: {r2_score(y_train, y_pred_train):.4f}")
    print(f"  Test R²: {r2_score(y_test, y_pred_test):.4f}")
    print(f"  Test MAE: {mean_absolute_error(y_test, y_pred_test):.4f} L")
    print(f"  Test RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_test)):.4f} L")
    
    # Importance des features
    print("\n🔍 Importance des features:")
    feature_names = ['soil_humidity', 'rain_mm', 'temp_avg', 'plant_type', 'soil_type']
    for name, importance in zip(feature_names, model.feature_importances_):
        print(f"  {name}: {importance:.4f}")
    
    return model


def save_model(model, model_name='watering_model'):
    """Sauvegarder le modèle"""
    # Créer le dossier models s'il n'existe pas
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'backend', 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, f'{model_name}.pkl')
    joblib.dump(model, model_path)
    print(f"\n✓ Modèle sauvegardé: {model_path}")
    
    return model_path


def test_model_predictions(model):
    """Tester quelques prédictions du modèle"""
    print("\n🧪 Tests de prédiction:")
    
    test_cases = [
        {
            'name': 'Sol sec, pas de pluie, chaud',
            'features': [20, 0, 30, 50, 50],  # soil_humidity, rain, temp, plant, soil
        },
        {
            'name': 'Sol humide, forte pluie, frais',
            'features': [80, 20, 15, 50, 50],
        },
        {
            'name': 'Sol normal, pluie légère, normal',
            'features': [50, 3, 22, 50, 50],
        },
    ]
    
    for case in test_cases:
        features = np.array([case['features']])
        prediction = model.predict(features)[0]
        print(f"  {case['name']}")
        print(f"    Features: {case['features']}")
        print(f"    → Volume prédit: {prediction:.2f} L")


def main():
    print("=" * 60)
    print("🤖 Entraînement du modèle d'arrosage intelligent")
    print("=" * 60)
    print()
    
    # Générer les données
    df = generate_training_data(n_samples=10000)
    
    # Sauvegarder les données
    data_path = os.path.join(os.path.dirname(__file__), 'training_data.csv')
    df.to_csv(data_path, index=False)
    print(f"✓ Données sauvegardées: {data_path}\n")
    
    # Préparer les données
    X = df[['soil_humidity', 'rain_mm', 'temp_avg', 'plant_type', 'soil_type']].values
    y = df['volume_l'].values
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"📊 Taille du dataset:")
    print(f"  Train: {len(X_train)} échantillons")
    print(f"  Test: {len(X_test)} échantillons\n")
    
    # Entraîner RandomForest
    rf_model = train_random_forest(X_train, X_test, y_train, y_test)
    
    # Entraîner XGBoost
    xgb_model = train_xgboost(X_train, X_test, y_train, y_test)
    
    # Choisir le meilleur modèle (RandomForest par défaut)
    best_model = rf_model
    model_type = 'RandomForest'
    
    # Comparer les performances
    rf_score = r2_score(y_test, rf_model.predict(X_test))
    xgb_score = r2_score(y_test, xgb_model.predict(X_test))
    
    if xgb_score > rf_score:
        best_model = xgb_model
        model_type = 'XGBoost'
    
    print(f"\n🏆 Meilleur modèle: {model_type} (R² = {max(rf_score, xgb_score):.4f})")
    
    # Sauvegarder
    model_path = save_model(best_model, 'watering_model')
    
    # Tests
    test_model_predictions(best_model)
    
    print("\n" + "=" * 60)
    print("✅ Entraînement terminé avec succès!")
    print("=" * 60)
    print(f"\n💡 Pour utiliser le modèle:")
    print(f"   1. Activez USE_AI_MODEL=True dans le .env")
    print(f"   2. Vérifiez que AI_MODEL_PATH pointe vers: {model_path}")
    print()


if __name__ == '__main__':
    main()
