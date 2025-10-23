# test_hybrid.py
import pandas as pd
from src.geocode_hybrid import geocode_hybrid_batch

print("🚀 Test du géocodeur hybride (OSM + Google Maps)")

# Charger les adresses
df = pd.read_csv("data/input.csv")
print(f"\n📂 {len(df)} adresses à géocoder\n")

# Géocoder avec méthode hybride
df_geo = geocode_hybrid_batch(df)

# Afficher les résultats
print("\n✅ Résultats :")
print(df_geo[["address", "city", "lat", "lon", "geocode_method"]].to_string(index=False))

# Compter les succès
success = df_geo["lat"].notna().sum()
print(f"\n🎯 {success}/{len(df)} adresses géocodées avec succès !")

# Sauvegarder
df_geo.to_csv("data/outputs/geocoded_addresses.csv", index=False)
print("\n💾 Sauvegardé dans data/outputs/geocoded_addresses.csv")
