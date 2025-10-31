# ------------------------------
# src/area_filters.py
# Filtres "carte" :
# - garder une ville
# - garder tout ce qui est au nord d'un certain parallèle (lat_threshold)
# - garder ce qui tombe DANS un polygone (point-in-polygon)
# ------------------------------

from typing import Optional, Iterable, Tuple, List
import pandas as pd
from shapely.geometry import Point, Polygon

# ------------------------------
# filter_city
# - Garde les lignes dont la colonne 'city' contient la chaîne donnée (ex: "San Antonio")
# - Utile si ton CSV couvre plusieurs villes ou si tu veux forcer la ville cible.
# ------------------------------
def filter_city(df: pd.DataFrame, city_name: Optional[str]) -> pd.DataFrame:
    """Filtre par nom de ville (case-insensitive)"""
    if not city_name or "city" not in df.columns:
        return df
    mask = df["city"].astype(str).str.contains(str(city_name), case=False, na=False)
    return df[mask].copy()

# ------------------------------
# require_latlon
# - Sécurité : on vérifie que df a bien 'lat' et 'lon' avant de faire de la géométrie.
# - Supprime aussi les lignes avec NaN dans lat/lon
# ------------------------------
def require_latlon(df: pd.DataFrame) -> pd.DataFrame:
    """Vérifie que lat/lon existent et supprime les NaN"""
    if "lat" not in df.columns or "lon" not in df.columns:
        raise ValueError("lat/lon are required. Geocode first or include lat/lon in the input.")
    # Supprimer les lignes sans coordonnées valides
    return df.dropna(subset=["lat", "lon"]).copy()

# ------------------------------
# filter_by_lat_threshold
# - Filtre simple et rapide: garde les points avec latitude >= seuil
# - Exemple: lat_threshold = 29.48 → "north side" approximatif
# ------------------------------
def filter_by_lat_threshold(df: pd.DataFrame, lat_threshold: float) -> pd.DataFrame:
    """Filtre par latitude minimale (utile pour Nord/Sud)"""
    df = require_latlon(df)
    return df[df["lat"] >= lat_threshold].copy()

# ------------------------------
# filter_by_polygon
# - Filtre précis: garde les points dont (lon, lat) tombe DANS un polygone
# - ⚠️ Ordre des coordonnées du polygone = (lon, lat) (et pas l'inverse)
# ------------------------------
def filter_by_polygon(df: pd.DataFrame, polygon_coords: Iterable[Tuple[float, float]]) -> pd.DataFrame:
    """
    Filtre les adresses à l'intérieur d'un polygone.
    
    Args:
        df: DataFrame avec colonnes 'lat' et 'lon'
        polygon_coords: Liste de tuples (longitude, latitude)
        
    Returns:
        DataFrame filtré avec seulement les points dans le polygone
    """
    df = require_latlon(df)
    poly = Polygon(polygon_coords)  # on construit le polygone Shapely
    # pour chaque ligne, on crée un Point(lon, lat) et on teste s'il est dans le polygone
    mask = df.apply(
        lambda r: poly.contains(Point(float(r["lon"]), float(r["lat"]))),
        axis=1,
    )
    return df[mask].copy()

# ------------------------------
# Helper: créer un polygone à partir de coordonnées (lat, lon)
# ------------------------------
def create_polygon_from_latlon(corners: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Convertit des coins (latitude, longitude) en format Shapely (longitude, latitude).
    Plus intuitif pour l'utilisateur !
    
    Args:
        corners: Liste de (latitude, longitude)
        
    Returns:
        Liste de (longitude, latitude) pour Shapely
        
    Exemple:
        corners = [(29.60, -98.78), (29.60, -98.20), (29.48, -98.20), (29.48, -98.78)]
        polygon_coords = create_polygon_from_latlon(corners)
        df_filtered = filter_by_polygon(df, polygon_coords)
    """
    return [(lon, lat) for lat, lon in corners]

# ------------------------------
# get_polygon_bounds
# - Retourne les limites d'un polygone (pour debug/visualisation)
# ------------------------------
def get_polygon_bounds(polygon_coords: Iterable[Tuple[float, float]]) -> dict:
    """Retourne les limites d'un polygone"""
    poly = Polygon(polygon_coords)
    bounds = poly.bounds  # (minx, miny, maxx, maxy) = (min_lon, min_lat, max_lon, max_lat)
    return {
        "min_lon": bounds[0],
        "min_lat": bounds[1],
        "max_lon": bounds[2],
        "max_lat": bounds[3],
    }

# ------------------------------
# POLYGONES PRÉ-DÉFINIS pour San Antonio
# ------------------------------

# Les rectangles suivants couvrent désormais l'ensemble de la zone métropolitaine
# de San Antonio, avec une séparation nord/sud autour de 29.48° de latitude et
# une séparation est/ouest autour de -98.45° de longitude.
LAT_SPLIT = 29.48
NORTH_LAT_MAX = 30.00
SOUTH_LAT_MIN = 28.80
WEST_LON_MIN = -100.00
EAST_LON_MAX = -97.00
EAST_SPLIT_LON = -98.45

NORTH_SA_RECT = [
    (WEST_LON_MIN, NORTH_LAT_MAX),
    (EAST_LON_MAX, NORTH_LAT_MAX),
    (EAST_LON_MAX, LAT_SPLIT),
    (WEST_LON_MIN, LAT_SPLIT),
    (WEST_LON_MIN, NORTH_LAT_MAX),
]

SOUTH_SA_RECT = [
    (WEST_LON_MIN, LAT_SPLIT),
    (EAST_LON_MAX, LAT_SPLIT),
    (EAST_LON_MAX, SOUTH_LAT_MIN),
    (WEST_LON_MIN, SOUTH_LAT_MIN),
    (WEST_LON_MIN, LAT_SPLIT),
]

EAST_SA_RECT = [
    (EAST_SPLIT_LON, NORTH_LAT_MAX),
    (EAST_LON_MAX, NORTH_LAT_MAX),
    (EAST_LON_MAX, SOUTH_LAT_MIN),
    (EAST_SPLIT_LON, SOUTH_LAT_MIN),
    (EAST_SPLIT_LON, NORTH_LAT_MAX),
]

WEST_SA_RECT = [
    (WEST_LON_MIN, NORTH_LAT_MAX),
    (EAST_SPLIT_LON, NORTH_LAT_MAX),
    (EAST_SPLIT_LON, SOUTH_LAT_MIN),
    (WEST_LON_MIN, SOUTH_LAT_MIN),
    (WEST_LON_MIN, NORTH_LAT_MAX),
]
