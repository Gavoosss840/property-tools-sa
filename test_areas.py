# test_areas.py
import pandas as pd
from src.area_filters import (
    filter_north_san_antonio,
    filter_south_san_antonio,
    filter_east_san_antonio,
    filter_west_san_antonio,
    LAT_SPLIT,
    EAST_SPLIT_LON,
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
    "NORTH": filter_north_san_antonio,
    "SOUTH": filter_south_san_antonio,
    "EAST": filter_east_san_antonio,
    "WEST": filter_west_san_antonio,
}

results = {}

for zone_name, filter_fn in zones.items():
    df_zone = filter_fn(df)
    results[zone_name] = df_zone
    
    print(f"{'='*60}")
    print(f"🔲 Zone {zone_name} de San Antonio")
    if zone_name in ("NORTH", "SOUTH"):
        relation = ">=" if zone_name == "NORTH" else "<"
        print(f"   Règle lat : latitude {relation} {LAT_SPLIT}")
    else:
        relation = ">=" if zone_name == "EAST" else "<"
        print(f"   Règle lon : longitude {relation} {EAST_SPLIT_LON}")
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
