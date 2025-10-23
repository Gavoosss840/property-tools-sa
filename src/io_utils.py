import re
import pandas as pd
from typing import Dict, List

#---------------------
#dictionnaire pour les csv
COLUMN_ALIASES: Dict [str,list[str]] = {
    "adress":["address","street","street_address","addr","adresse","adress","address1","line1"],
    "city":    ["city","ville","town","municipality"],
    "state":   ["state","st","etat","province","region"],
    "zip":     ["zip","zipcode","postal","postal_code","zip_code","code postal","code_postal"],
}

#---------------------
#Nettoyage mot par mot en format lisible pour le code -> "Street adress" devient "streetadress"
# Comme une brosse à dents pour 1 dent
def _norm_token(s: str) -> str:
    s=s.strip().lower() #enlève les espaces et les majuscules
    return re.sub(r"[^a-z0-9]+","",s) #supprimer ce qui n'est pas lettre ou chiffre
#------------------------

#-------------------------
#nettoie toutes les colonnes en utilisant norm token
# + compare le nom nettoyer avec l'alias pour renommer la colonne
#Utilise la brosse a dents pour toutes les dents
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {} # constuire 
    used = set() #eviter le double mappage vers le même nom
    norm_aliases = {k: {_norm_token(a) for a in v} for k, v in COLUMN_ALIASES.items()}
    for col in df.columns: #faire toutes les colonnes
        n = _norm_token(col) #brosse à dents pour un nom "normal"
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
