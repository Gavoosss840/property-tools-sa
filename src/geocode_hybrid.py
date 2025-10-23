# src/geocode_hybrid.py
# Géocodeur hybride : OSM d'abord, puis Google Maps si échec
import os
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import googlemaps
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from dotenv import load_dotenv

# Streamlit is optional here; only used for secrets in Cloud
try:
    import streamlit as st  # type: ignore
except Exception:
    st = None  # fallback when running outside Streamlit

# Charger les variables d'environnement
load_dotenv()

CACHE_PATH = Path("data/geocode_cache.csv")

def _load_cache() -> dict:
    """Charge le cache de géocodage depuis le CSV"""
    if CACHE_PATH.exists():
        df = pd.read_csv(CACHE_PATH)
        return {row["q"]: (row["lat"], row["lon"]) for _, row in df.iterrows()}
    return {}

def _save_cache(cache: dict) -> None:
    """Sauvegarde le cache dans le CSV"""
    if not cache:
        return
    rows = [{"q": k, "lat": v[0], "lon": v[1]} for k, v in cache.items() if v[0] is not None]
    pd.DataFrame(rows).to_csv(CACHE_PATH, index=False)

def build_query(
    address: Optional[str],
    city: Optional[str],
    state: Optional[str],
    zip_code: Optional[str],
) -> str:
    """Construit une adresse complète"""
    parts = []
    if address:  parts.append(str(address))
    if city:     parts.append(str(city))
    if state:    parts.append(str(state))
    if zip_code: parts.append(str(zip_code))
    parts.append("USA")
    return ", ".join([p for p in parts if p and p.lower() != "nan"])

def geocode_with_osm(query: str) -> Optional[Tuple[float, float]]:
    """Essaie de géocoder avec OpenStreetMap"""
    try:
        geolocator = Nominatim(user_agent="property_tools_geocoder")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)
        loc = geocode(query, country_codes="us", addressdetails=False, timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return None

def geocode_with_google(query: str, api_key: str) -> Optional[Tuple[float, float]]:
    """Essaie de géocoder avec Google Maps"""
    try:
        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.geocode(query)
        if result:
            loc = result[0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
    except Exception:
        pass
    return None

def _get_google_maps_api_key() -> Optional[str]:
    """Return API key from Streamlit secrets or environment.

    Order: st.secrets -> env var (after .env loaded).
    """
    # Prefer Streamlit secrets if available (Streamlit Cloud)
    try:
        if st and hasattr(st, "secrets") and "GOOGLE_MAPS_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_MAPS_API_KEY"]
    except Exception:
        pass
    # Fallback to environment / .env
    return os.getenv("GOOGLE_MAPS_API_KEY")


def geocode_hybrid_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Géocode un DataFrame avec méthode hybride :
    1. Vérifie le cache
    2. Essaie OSM
    3. Si échec, essaie Google Maps
    """
    cache = _load_cache()
    api_key = _get_google_maps_api_key()
    
    lats, lons, methods = [], [], []
    osm_count = google_count = cached_count = failed_count = 0

    for idx, row in df.iterrows():
        # Construire la requête
        q = build_query(
            address=row.get("address"),
            city=row.get("city"),
            state=row.get("state"),
            zip_code=row.get("zip"),
        )

        # Vérifier le cache
        if q in cache:
            lat, lon = cache[q]
            method = "cache"
            cached_count += 1
        else:
            # Essayer OSM d'abord
            print(f"[{idx+1}/{len(df)}] Géocodage OSM: {q[:50]}...")
            result = geocode_with_osm(q)
            
            if result:
                lat, lon = result
                method = "osm"
                osm_count += 1
            elif api_key:
                # Backup avec Google Maps
                print(f"  → OSM échoué, essai Google Maps...")
                result = geocode_with_google(q, api_key)
                if result:
                    lat, lon = result
                    method = "google"
                    google_count += 1
                else:
                    lat = lon = None
                    method = "failed"
                    failed_count += 1
            else:
                lat = lon = None
                method = "failed"
                failed_count += 1

            # Sauvegarder dans le cache
            cache[q] = (lat, lon)
            time.sleep(0.1)  # Petite pause

        lats.append(lat)
        lons.append(lon)
        methods.append(method)

    # Ajouter les colonnes
    df = df.copy()
    df["lat"] = lats
    df["lon"] = lons
    df["geocode_method"] = methods

    # Sauvegarder le cache
    _save_cache(cache)

    # Afficher les stats
    print(f"\n📊 Statistiques de géocodage :")
    print(f"   ✅ Cache: {cached_count}")
    print(f"   🌍 OpenStreetMap: {osm_count}")
    print(f"   🗺️  Google Maps: {google_count}")
    print(f"   ❌ Échecs: {failed_count}")

    return df
