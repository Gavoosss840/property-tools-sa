# test_google_api.py
import os
from dotenv import load_dotenv
import googlemaps

load_dotenv()

api_key = os.getenv("GOOGLE_MAPS_API_KEY")
if not api_key:
    print("❌ Clé API non trouvée dans .env")
else:
    print(f"✅ Clé trouvée : {api_key[:10]}...")
    
    # Test rapide
    gmaps = googlemaps.Client(key=api_key)
    result = gmaps.geocode("235 Altgelt Ave, San Antonio, TX 78201")
    
    if result:
        lat = result[0]["geometry"]["location"]["lat"]
        lon = result[0]["geometry"]["location"]["lng"]
        print(f"✅ Google Maps fonctionne ! Coords : ({lat}, {lon})")
    else:
        print("❌ Pas de résultat")