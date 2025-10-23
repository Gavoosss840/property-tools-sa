# ------------------------------
# map_points_vs_polygon.py
# Affiche ton polygone (north_polygon.json)
# + toutes les adresses géocodées (points)
# ------------------------------

from pathlib import Path
import json
import folium
import pandas as pd
from shapely.geometry import Point, Polygon

POLY_PATH = Path("data/north_polygon.json")
CSV_PATH = Path("data/outputs/geocoded.csv")

# Vérification des fichiers
if not POLY_PATH.exists():
    raise SystemExit("⚠️ data/north_polygon.json introuvable. Lance d'abord: poetry run python build_polygon.py")
if not CSV_PATH.exists():
    raise SystemExit("⚠️ data/outputs/geocoded.csv introuvable. Lance d'abord: poetry run python test_step2.py")

# Charger le polygone (lon, lat)
payload = json.loads(POLY_PATH.read_text(encoding="utf-8"))
poly_lonlat = [tuple(p) for p in payload["polygon"]]
poly = Polygon(poly_lonlat)

# Folium veut (lat, lon)
poly_latlon = [(lat, lon) for (lon, lat) in poly_lonlat]

# Charger le CSV géocodé
df = pd.read_csv(CSV_PATH)

# Calculer le centre de la carte
if len(df.dropna(subset=["lat","lon"])) > 0:
    avg_lat = df["lat"].dropna().mean()
    avg_lon = df["lon"].dropna().mean()
else:
    avg_lat = sum(p[0] for p in poly_latlon)/len(poly_latlon)
    avg_lon = sum(p[1] for p in poly_latlon)/len(poly_latlon)

# Créer la carte
m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10, control_scale=True)

# Dessiner le polygone
folium.Polygon(
    locations=poly_latlon,
    tooltip="Zone North (polygone)",
    color="blue",
    weight=2,
    fill=True,
    fill_opacity=0.2
).add_to(m)

# Ajouter les points
inside_count = 0
for _, r in df.iterrows():
    lat, lon = r.get("lat"), r.get("lon")
    if pd.isna(lat) or pd.isna(lon):
        continue
    pt = Point(float(lon), float(lat))
    inside = poly.contains(pt)
    color = "green" if inside else "red"
    if inside:
        inside_count += 1
    popup = folium.Popup(
        f"<b>{r.get('address', r.get('Address',''))}</b><br>"
        f"{r.get('city', r.get('City',''))}, {r.get('state', r.get('State',''))} {r.get('zip', r.get('Zip',''))}<br>"
        f"lat/lon: {lat:.5f}, {lon:.5f}<br>"
        f"Inside zone: {inside}",
        max_width=300
    )
    folium.CircleMarker(
        location=[lat, lon],
        radius=5,
        color=color,
        fill=True,
        fill_opacity=0.9,
        popup=popup
    ).add_to(m)

# Légende simple
folium.map.Marker(
    [avg_lat, avg_lon],
    icon=folium.DivIcon(
        html=f"""
        <div style="background:white;padding:6px 10px;border:1px solid #888;border-radius:6px">
          <b>Légende</b><br>
          🟢 Dans la zone<br>
          🔴 Hors zone<br>
          <b>Total in:</b> {inside_count}
        </div>
        """
    ),
).add_to(m)

OUT = Path("data/outputs/map_points_vs_polygon.html")
m.save(OUT)
print(f"✅ Carte sauvegardée -> {OUT}")
