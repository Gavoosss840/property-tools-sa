import re
from typing import Dict, List

import pandas as pd

#---------------------
# Dictionnaire d'alias de colonnes (CSV/Excel)
# Canonicalise vers les noms attendus par le pipeline/app
# -> 'address', 'city', 'state', 'zip'
COLUMN_ALIASES: Dict[str, List[str]] = {
    "address": [
        "address",
        "street",
        "street_address",
        "addr",
        "adresse",
        "adress",
        "address1",
        "line1",
    ],
    "city": ["city", "ville", "town", "municipality"],
    "state": ["state", "st", "etat", "province", "region"],
    "zip": [
        "zip",
        "zipcode",
        "postal",
        "postal_code",
        "zip_code",
        "code postal",
        "code_postal",
    ],
}


#---------------------
# Nettoyage mot par mot en format lisible pour le code
# -> "Street adress" devient "streetadress"
def _norm_token(s: str) -> str:
    s = s.strip().lower()
    return re.sub(r"[^a-z0-9]+", "", s)


#-------------------------
# Renomme les colonnes pour correspondre aux canoniques
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping: Dict[str, str] = {}
    used = set()  # éviter le double mappage vers le même nom
    norm_aliases = {k: {_norm_token(a) for a in v} for k, v in COLUMN_ALIASES.items()}
    for col in df.columns:
        n = _norm_token(col)
        for target, aliases in norm_aliases.items():
            if n == target or n in aliases:
                if target not in used:
                    mapping[col] = target
                    used.add(target)
                break
    if mapping:
        df = df.rename(columns=mapping)
    return df


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return normalize_columns(df)


def load_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    return normalize_columns(df)


def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)

