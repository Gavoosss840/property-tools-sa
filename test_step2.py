# test_step2.py
import pandas as pd
from src.geocode import geocode_osm_batch

print("🚀 Script lancé !")

# 1️⃣ Charger le CSV
df = pd.read_csv("data/input.csv")
print(f"[INFO] {len(df)} lignes chargées depuis data/input.csv")

# 2️⃣ Afficher les colonnes et un aperçu
print("\n📊 Colonnes disponibles :")
print(df.columns.tolist())
print("\n📄 Aperçu des données :")
print(df.head())

# 3️⃣ Géocoder les adresses
print("\n🌍 Géocodage en cours... (peut prendre 1 seconde par adresse)")
df_geo = geocode_osm_batch(df, min_delay_seconds=1.0)

# 4️⃣ Afficher les résultats
print("\n✅ Géocodage terminé !")
print("\n📊 Colonnes après géocodage :")
print(df_geo.columns.tolist())
print("\n📍 Résultats avec coordonnées GPS :")
print(df_geo[["address", "city", "lat", "lon"]])

# 5️⃣ Sauvegarder le résultat
output_path = "data/outputs/geocoded_addresses.csv"
df_geo.to_csv(output_path, index=False)
print(f"\n💾 Résultats sauvegardés dans : {output_path}")