# ------------------------------
# src/polygon_tools.py
# Objectif :
# 1️⃣ Lire une liste de "checkpoints" (intersections ou routes clés) depuis un fichier texte.
# 2️⃣ Géocoder chaque checkpoint → latitude + longitude avec Nominatim (OpenStreetMap).
# 3️⃣ Construire un polygone (liste ordonnée de coordonnées (lon, lat)).
# 4️⃣ Sauvegarder ce polygone dans un fichier JSON pour l’utiliser ensuite comme filtre.
# ------------------------------

from pathlib import Path
import json
from typing import List, Tuple, Optional, Dict

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import re

# ------------------------------
# Fichiers utilisés
# ------------------------------
CHECKPOINTS_PATH = Path("data/north_checkpoints.txt")  # où tu mets ta liste de routes
POLYGON_JSON_PATH = Path("data/north_polygon.json")    # fichier de sortie (résultat du polygone)


# ------------------------------
# Étape 1 — Lire la liste des checkpoints
# ------------------------------
def read_checkpoints(path: Optional[Path] = None) -> List[str]:
    """
    Lit chaque ligne non vide du fichier texte des checkpoints.
    Chaque ligne correspond à une route, intersection ou point GPS que tu veux inclure dans le contour.
    """
    if path is None:
        path = CHECKPOINTS_PATH

    if not path.exists():
        raise FileNotFoundError(f"{path} non trouvé. Crée ce fichier et mets 1 point/ligne.")

    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s:
            lines.append(s)

    if len(lines) < 3:
        raise ValueError("Il faut au moins 3 points pour construire un polygone.")

    return lines


# ------------------------------
# Étape 2 — Géocoder un checkpoint
# ------------------------------
def _normalize_highway_tokens(text: str) -> str:
    """
    Normalize common highway notations for OSM/Nominatim.
    - Convert "TX-46" -> "TX 46", "US-281" -> "US 281", "I-10" -> "I 10"
    - Replace '/' (concurrency) with ' and '
    - Replace '&' with ' and '
    """
    s = text.replace("/", " and ")
    s = s.replace("&", " and ")
    s = re.sub(r"\b([A-Z]{1,3})-(\d+)\b", r"\1 \2", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _try_structured_intersection(q: str, geocode) -> Optional[Tuple[float, float]]:
    """
    Attempt structured geocoding for intersection-like queries.
    Expects formats like: "RoadA & RoadB, City, ST".
    """
    parts = [p.strip() for p in q.split(",")]
    if len(parts) < 2:
        return None

    roads = parts[0]
    city = parts[-2] if len(parts) >= 2 else None
    state = parts[-1] if len(parts) >= 1 else None

    if not any(sep in roads for sep in ("&", "/", " and ")):
        return None

    street = _normalize_highway_tokens(roads)
    query: Dict[str, str] = {
        "street": street,
        "city": city or "",
        "state": state or "",
        "country": "USA",
    }
    try:
        loc = geocode(query, country_codes="us", addressdetails=False, timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    try:
        norm_q = ", ".join([p for p in [street, city, state] if p])
        loc = geocode(norm_q, country_codes="us", addressdetails=False, timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception:
        pass
    return None


def geocode_point(q: str, geocode) -> Optional[Tuple[float, float]]:
    """
    Géocode un point texte (adresse ou intersection).
    Retourne (lat, lon) ou None si échec.
    """
    try:
        loc = geocode(q, country_codes="us", addressdetails=False, timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except Exception as e:
        print(f"[ERREUR] Géocode échoué pour '{q}': {e}")
    return None


def geocode_point2(q: str, geocode) -> Optional[Tuple[float, float]]:
    """
    Improved geocoder with intersection handling and normalization.
    """
    parts = [p.strip() for p in q.split(",")]
    city_hint = parts[-2] if len(parts) >= 2 else ""
    state_hint = parts[-1] if len(parts) >= 1 else ""

    # Try to resolve a context point for the city/state to reject far results
    ctx = None
    if city_hint and state_hint:
        try:
            ctx_loc = geocode(f"{city_hint}, {state_hint}", country_codes="us", addressdetails=False, timeout=10)
            if ctx_loc:
                ctx = (ctx_loc.latitude, ctx_loc.longitude)
        except Exception:
            ctx = None

    def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        from math import radians, sin, cos, asin, sqrt
        lat1, lon1 = a
        lat2, lon2 = b
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return 2*6371*asin(sqrt(h))

    def _ok(loc_addr: str, lat: Optional[float] = None, lon: Optional[float] = None) -> bool:
        addr_low = (loc_addr or "").lower()
        if city_hint and city_hint.lower() not in addr_low:
            return False
        if state_hint:
            st = state_hint.lower()
            if st == "tx":
                if ("texas" not in addr_low) and (" tx" not in addr_low):
                    return False
            else:
                if st not in addr_low:
                    return False
        if ctx and lat is not None and lon is not None:
            # reject if too far from city center (> 80 km)
            if _haversine_km(ctx, (lat, lon)) > 80:
                return False
        return True
    # 1) Try the raw query first
    try:
        loc = geocode(q, country_codes="us", addressdetails=False, timeout=10)
        if loc and _ok(getattr(loc, "address", ""), getattr(loc, "latitude", None), getattr(loc, "longitude", None)):
            return (loc.latitude, loc.longitude)
    except Exception as e:
        print(f"[ERREUR] Géocode échoué pour '{q}': {e}")

    # 2) Try a structured intersection parse if applicable
    res = _try_structured_intersection(q, geocode)
    if res:
        return res

    # 3) Try a normalized free-form variant
    try:
        norm_q = _normalize_highway_tokens(q)
        if norm_q != q:
            loc = geocode(norm_q, country_codes="us", addressdetails=False, timeout=10)
            if loc and _ok(getattr(loc, "address", ""), getattr(loc, "latitude", None), getattr(loc, "longitude", None)):
                return (loc.latitude, loc.longitude)
    except Exception:
        pass

    # 4) Try common phrasing variants for intersections
    try:
        parts = [p.strip() for p in q.split(",")]
        roads = parts[0]
        city_hint = parts[-2] if len(parts) >= 2 else ""
        state_hint = parts[-1] if len(parts) >= 1 else ""
        tail = ", ".join(parts[1:]) if len(parts) > 1 else ""
        norm_roads = _normalize_highway_tokens(roads)
        tokens = re.split(r"\s+and\s+", norm_roads)
        pairs = []
        if len(tokens) >= 2:
            pairs.append((tokens[0], tokens[1]))
        if len(tokens) == 3:
            pairs.extend([(tokens[0], tokens[2]), (tokens[1], tokens[2])])

        def _tx_to_sh(s: str) -> str:
            return re.sub(r"\bTX (\d+)\b", r"SH \1", s)

        def _ok(loc_addr: str) -> bool:
            addr_low = (loc_addr or "").lower()
            if city_hint and city_hint.lower() not in addr_low:
                return False
            if state_hint:
                st = state_hint.lower()
                if st == "tx":
                    if ("texas" not in addr_low) and (" tx" not in addr_low):
                        return False
                else:
                    if st not in addr_low:
                        return False
            return True

        for a, b in pairs:
            for join in (" & ", " at ", " and "):
                variant = f"{a}{join}{b}"
                q_try = f"{variant}, {tail}" if tail else variant
                loc = geocode(q_try, country_codes="us", addressdetails=False, timeout=10)
                if loc and _ok(getattr(loc, "address", ""), getattr(loc, "latitude", None), getattr(loc, "longitude", None)):
                    return (loc.latitude, loc.longitude)
                # Try TX -> SH alias in Texas
                a2, b2 = _tx_to_sh(a), _tx_to_sh(b)
                if (a2, b2) != (a, b):
                    variant2 = f"{a2}{join}{b2}"
                    q_try2 = f"{variant2}, {tail}" if tail else variant2
                    loc = geocode(q_try2, country_codes="us", addressdetails=False, timeout=10)
                    if loc and _ok(getattr(loc, "address", ""), getattr(loc, "latitude", None), getattr(loc, "longitude", None)):
                        return (loc.latitude, loc.longitude)
    except Exception:
        pass

    return None


# ------------------------------
# Étape 3 — Construire le polygone complet
# ------------------------------
def build_polygon_from_checkpoints(checkpoints: List[str]) -> List[Tuple[float, float]]:
    """
    Pour chaque checkpoint, géocode et crée une liste [(lon, lat), ...] utilisable par Shapely.
    ⚠️ L’ordre des points compte : mets-les dans l’ordre du contour (horaire ou anti-horaire).
    """
    geolocator = Nominatim(user_agent="property_tools_polygon")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

    coords: List[Tuple[float, float]] = []

    for q in checkpoints:
        res = geocode_point2(q, geocode)
        if res is None:
            print(f"[WARN] Échec géocode pour : {q}")
            continue

        lat, lon = res
        coords.append((lon, lat))  # ⚠️ On inverse (lon, lat) pour compatibilité Shapely

    if len(coords) < 3:
        raise ValueError("Pas assez de points géocodés pour faire un polygone.")

    # Fermer le polygone (revenir au point de départ si besoin)
    if coords[0] != coords[-1]:
        coords.append(coords[0])

    print(f"[OK] Polygone créé avec {len(coords)} points.")
    return coords


# ------------------------------
# Étape 4 — Sauvegarder et recharger
# ------------------------------
def save_polygon(coords: List[Tuple[float, float]], path: Path = POLYGON_JSON_PATH):
    """
    Sauvegarde le polygone dans un fichier JSON simple : {"polygon": [[lon, lat], ...]}
    """
    payload = {"polygon": coords}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[OK] Polygone sauvegardé dans {path}")

def load_polygon(path: Path = POLYGON_JSON_PATH) -> List[Tuple[float, float]]:
    """
    Recharge un polygone depuis le JSON.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [tuple(p) for p in payload["polygon"]]
