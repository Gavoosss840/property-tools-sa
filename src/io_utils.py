import re
from typing import Dict, List

import pandas as pd

#-------------------------
# Détecter les fichiers à une colonne contenant plusieurs champs séparés
def _expand_combined_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Si le DataFrame n'a qu'une colonne avec des valeurs séparées par des virgules,
    la scinder en colonnes individuelles."""
    if df.shape[1] != 1:
        return df

    col_name = df.columns[0]
    series = df.iloc[:, 0]

    # Trouver un séparateur plausible
    separators = [",", ";", "|", "\t"]
    delimiter = next((sep for sep in separators if sep in str(col_name)), None)
    if delimiter is None:
        sample = (
            series.dropna()
            .astype(str)
            .head(10)
        )
        for sep in separators:
            if sample.str.contains(sep).any():
                delimiter = sep
                break
    if not delimiter:
        return df

    headers = [h.strip() for h in str(col_name).split(delimiter)]
    if len(headers) <= 1:
        return df

    expanded = series.astype(str).str.split(delimiter, expand=True)

    # Ajuster le nombre de colonnes pour correspondre aux en-têtes détectés
    if expanded.shape[1] < len(headers):
        for _ in range(len(headers) - expanded.shape[1]):
            expanded[expanded.shape[1]] = ""
    elif expanded.shape[1] > len(headers):
        expanded = expanded.iloc[:, :len(headers)]

    expanded.columns = headers
    expanded = expanded.apply(
        lambda col: col.astype(str).str.strip() if col.dtype == object else col
    )
    return expanded

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
    df = _expand_combined_columns(df)
    return normalize_columns(df)


def load_excel(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)
    df = _expand_combined_columns(df)
    return normalize_columns(df)


def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)
