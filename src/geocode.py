# ------------------------------
# src/geocode.py
# Convertit des adresses (texte) en coordonnées GPS (lat, lon)
# via OpenStreetMap/Nominatim (geopy).
# + Ajoute un CACHE local (CSV) pour éviter de re-géocoder la même adresse.
# ------------------------------

import time
from typing import Optional
from pathlib import Path

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Chemin du petit cache de géocodage (dans /data)
CACHE_PATH = Path("data/geocode_cache.csv")

# ------------------------------
# _load_cache / _save_cache
# - Cache en mémoire (dict) + sauvegarde dans un CSV.
# - Format dict: { "requete_complète": (lat, lon) }
# ------------------------------
def _load_cache() -> dict:
    if CACHE_PATH.exists():
        df = pd.read_csv(CACHE_PATH)
        return {row["q"]: (row["lat"], row["lon"]) for _, row in df.iterrows()}
    return {}

def _save_cache(cache: dict) -> None:
    if not cache:
        return
    rows = [{"q": k, "lat": v[0], "lon": v[1]} for k, v in cache.items() if v[0] is not None]
    pd.DataFrame(rows).to_csv(CACHE_PATH, index=False)

# ------------------------------
# build_query
# - Construit une chaîne d'adresse bien formée pour le géocodage.
# ------------------------------
def build_query(
    address: Optional[str],
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str],
    country: str = "US",
) -> str:
    parts = []
    if address:  parts.append(str(address))
    if city:     parts.append(str(city))
    if state:    parts.append(str(state))
    if zip_code: parts.append(str(zip_code))
    parts.append("USA" if country.upper() == "US" else country.upper())
    # Filtrer les 'nan' / vides
    return ", ".join([p for p in parts if p and p.lower() != "nan"])

# ------------------------------
# geocode_osm_batch
# - Ajoute 2 colonnes 'lat' et 'lon' à ton DataFrame.
# - Respecte un délai minimal (RateLimiter) → OSM est limité.
# - Utilise un cache local pour accélérer les relances.
# ------------------------------
def geocode_osm_batch(
    df: pd.DataFrame,
    min_delay_seconds: float = 1.0,
    country_code: str = "us",
) -> pd.DataFrame:
    geolocator = Nominatim(user_agent="property_tools_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=min_delay_seconds)

    cache = _load_cache()
    lats, lons = [], []

    for _, row in df.iterrows():
        # 1) Construire la requête complète
        q = build_query(
            address=row.get("address"),
            city=row.get("city"),
            state=row.get("state"),
            zip_code=row.get("zip"),
            country="US",
        )

        # 2) Utiliser le cache si possible
        if q in cache:
            lat, lon = cache[q]
        else:
            lat = lon = None
            try:
                # 3) Appel Nominatim (peut renvoyer None si ambigu)
                loc = geocode(q, country_codes=country_code, addressdetails=False, timeout=10)
                if loc:
                    lat, lon = loc.latitude, loc.longitude
            except Exception:
                lat = lon = None

            # 4) Mémoriser le résultat (même None pour éviter de spammer)
            cache[q] = (lat, lon)
            time.sleep(0.01)  # micro-pause (RateLimiter gère déjà le gros)

        # 5) Stocker dans les futures colonnes
        lats.append(lat)
        lons.append(lon)

    # 6) Ajouter les colonnes au DataFrame
    df = df.copy()
    df["lat"] = lats
    df["lon"] = lons

    # 7) Sauvegarder le cache
    _save_cache(cache)

    return df
