# src/pdf_extractor.py
# Extraction spécialisée pour les PDFs de foreclosure du Bexar County
import re
from pathlib import Path
from typing import List, Dict
import pandas as pd
import pdfplumber

def extract_addresses_from_pdf(pdf_path: str) -> List[Dict[str, str]]:
    """
    Extrait les adresses de la colonne 'Property Address' 
    des PDFs de foreclosure du Bexar County.
    
    Format attendu dans le PDF :
    "219 DELAWARE ST, SAN ANTONIO, TEXAS, 78210"
    "1419 CROW CT, SAN ANTONIO, TEXAS, 78245"
    etc.
    """
    addresses = []
    
    # Pattern pour extraire une adresse complète
    # Capture : (street address), (city), TEXAS, (zip)
    address_pattern = re.compile(
        r'([0-9]+\s+[A-Z\s\.\-]+?),'  # Numéro + rue (majuscules)
        r'\s*([A-Z\s]+),'              # Ville (majuscules)
        r'\s*(?:TEXAS|TX),'            # État (TEXAS ou TX)
        r'\s*(\d{5})',                 # Code postal
        re.IGNORECASE
    )
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                continue
            
            # Chercher toutes les adresses
            matches = address_pattern.findall(text)
            
            for match in matches:
                street, city, zip_code = match
                
                # Nettoyer les espaces multiples
                street = re.sub(r'\s+', ' ', street.strip())
                city = re.sub(r'\s+', ' ', city.strip())
                
                # Filtrer les faux positifs (lignes d'en-tête, etc.)
                if is_valid_address(street, city, zip_code):
                    addresses.append({
                        "address": street,
                        "city": city,
                        "state": "TX",
                        "zip": zip_code.strip()
                    })
    
    return addresses

def is_valid_address(street: str, city: str, zip_code: str) -> bool:
    """
    Valide qu'une adresse extraite est bien une vraie adresse.
    Filtre les faux positifs.
    """
    # Doit avoir un numéro au début
    if not re.match(r'^\d+', street):
        return False
    
    # La rue doit faire au moins 5 caractères
    if len(street) < 5:
        return False
    
    # Ville doit faire au moins 3 caractères
    if len(city) < 3:
        return False
    
    # Exclure les villes qui sont des mots-clés du document
    excluded_cities = ['AREA', 'COUNTY', 'COURTHOUSE', 'WEST SIDE', 'COMMISSIONERS', 'LOCATED', 'OUTSIDE']
    if any(excluded in city.upper() for excluded in excluded_cities):
        return False
    
    # Le zip doit être valide (78xxx pour San Antonio area)
    if not zip_code.startswith('78'):
        return False
    
    return True

def clean_and_deduplicate(addresses: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Nettoie et déduplique les adresses.
    """
    if not addresses:
        return pd.DataFrame(columns=["address", "city", "state", "zip"])
    
    df = pd.DataFrame(addresses)
    
    # Nettoyer les espaces
    for col in df.columns:
        df[col] = df[col].str.strip()
    
    # Supprimer les doublons
    df = df.drop_duplicates(subset=["address", "zip"])
    
    # Trier par ville puis adresse
    df = df.sort_values(["city", "address"]).reset_index(drop=True)
    
    return df

def process_pdf_to_csv(
    pdf_path: str, 
    output_csv: str = "data/input.csv"
) -> int:
    """
    Pipeline complet : PDF foreclosure → CSV
    
    Returns:
        Nombre d'adresses extraites
    """
    print(f"📄 Lecture du PDF : {pdf_path}")
    
    # Extraction
    addresses = extract_addresses_from_pdf(pdf_path)
    
    if not addresses:
        print("❌ Aucune adresse trouvée dans le PDF")
        print("   Vérifiez que le PDF contient des adresses au format attendu")
        return 0
    
    print(f"✅ {len(addresses)} adresses brutes extraites")
    
    # Nettoyage et déduplication
    df = clean_and_deduplicate(addresses)
    
    print(f"✅ {len(df)} adresses uniques après nettoyage")
    
    # Sauvegarder
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"💾 Sauvegardé dans : {output_csv}")
    
    # Afficher un aperçu
    print("\n📋 Aperçu des adresses extraites :")
    print(df.head(10).to_string(index=False))
    if len(df) > 10:
        print(f"   ... et {len(df) - 10} autres adresses")
    
    return len(df)
