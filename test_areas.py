# test_areas.py
import pandas as pd
from src.area_filters import (
    filter_by_polygon,
    get_polygon_bounds,
    NORTH_SA_RECT,
    SOUTH_SA_RECT,
    EAST_SA_RECT,
    WEST_SA_RECT
)

print("🗺️  Test des filtres géographiques - San Antonio\n")

# Charger les adresses géocodées
df = pd.read_csv("data/outputs/geocoded_addresses.csv")
print(f"📂 {len(df)} adresses chargées")
print(f"✅ {df['lat'].notna().sum()} avec coordonnées GPS\n")

# Afficher toutes les adresses avec leurs coordonnées
print("📍 Toutes les adresses :")
print(df[["address", "city", "lat", "lon"]].to_string(index=False))
print()

# Tester chaque zone
zones = {
    "NORTH": NORTH_SA_RECT,
    "SOUTH": SOUTH_SA_RECT,
    "EAST": EAST_SA_RECT,
    "WEST": WEST_SA_RECT,
}

results = {}

for zone_name, polygon in zones.items():
    bounds = get_polygon_bounds(polygon)
    df_zone = filter_by_polygon(df, polygon)
    results[zone_name] = df_zone
    
    print(f"{'='*60}")
    print(f"🔲 Zone {zone_name} de San Antonio")
    print(f"   Lat: {bounds['min_lat']:.4f} → {bounds['max_lat']:.4f}")
    print(f"   Lon: {bounds['min_lon']:.4f} → {bounds['max_lon']:.4f}")
    print(f"   📊 {len(df_zone)}/{len(df)} adresses dans cette zone")
    
    if len(df_zone) > 0:
        print(f"\n   ✅ Adresses trouvées :")
        for _, row in df_zone.iterrows():
            print(f"      • {row['address']}, {row['city']} ({row['lat']:.4f}, {row['lon']:.4f})")
        
        # Sauvegarder
        output_path = f"data/outputs/{zone_name.lower()}_san_antonio.csv"
        df_zone.to_csv(output_path, index=False)
        print(f"\n   💾 Sauvegardé : {output_path}")
    else:
        print(f"   ❌ Aucune adresse dans cette zone")
    
    print()

# Résumé final
print(f"{'='*60}")
print("📊 RÉSUMÉ FINAL :")
for zone_name, df_zone in results.items():
    print(f"   {zone_name:6s} : {len(df_zone)} adresses")