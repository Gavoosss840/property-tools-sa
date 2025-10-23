# app.py
# Interface web sécurisée pour Property Tools
import streamlit as st
from pathlib import Path
import tempfile
import os
from dotenv import load_dotenv
from src.pipeline import run_full_pipeline

# Charger les variables d'environnement
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Property Tools - San Antonio",
    page_icon="🏠",
    layout="wide"
)

# ==========================================
# SYSTÈME D'AUTHENTIFICATION
# ==========================================
def check_password():
    """Retourne True si le mot de passe est correct"""
    
    def password_entered():
        """Vérifie le mot de passe entré"""
        correct_password = st.secrets.get("PASSWORD", os.getenv("PASSWORD", ""))
        
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Ne pas garder le mot de passe en mémoire
        else:
            st.session_state["password_correct"] = False

    # Si déjà authentifié
    if st.session_state.get("password_correct", False):
        return True

    # Afficher le formulaire de connexion
    st.markdown("<h1 style='text-align: center;'>🏠 Property Tools</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>San Antonio Foreclosure Analyzer</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔒 Connexion")
        st.text_input(
            "Mot de passe",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Entrez votre mot de passe"
        )
        
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Mot de passe incorrect")
        
        st.info("💡 Contactez l'administrateur pour obtenir l'accès")
    
    return False

# Vérifier l'authentification
if not check_password():
    st.stop()

# ==========================================
# APPLICATION PRINCIPALE (après authentification)
# ==========================================

# En-tête avec bouton déconnexion
col1, col2 = st.columns([5, 1])
with col1:
    st.title("🏠 Property Tools - San Antonio")
    st.markdown("**Analyseur de foreclosures par zones géographiques**")
with col2:
    st.write("")  # Espace
    if st.button("🚪 Déconnexion", type="secondary"):
        st.session_state["password_correct"] = False
        st.rerun()

st.markdown("---")

# Sidebar pour les infos
with st.sidebar:
    st.header("📋 Mode d'emploi")
    st.markdown("""
    ### Étapes :
    1. **📄 Upload** votre PDF de foreclosure
    2. **🚀 Cliquez** sur "Run Pipeline"
    3. **💾 Téléchargez** les CSVs par zone
    
    ### Zones disponibles :
    - 🧭 **North** San Antonio
    - 🧭 **South** San Antonio
    - 🧭 **East** San Antonio
    - 🧭 **West** San Antonio
    """)
    
    st.markdown("---")
    
    st.header("ℹ️ Format attendu")
    st.code("""
Property Address
123 MAIN ST, SAN ANTONIO, TX 78201
456 OAK AVE, SAN ANTONIO, TX 78220
    """)
    
    st.markdown("---")
    st.caption("🔒 Application sécurisée")
    st.caption("© 2025 B. Horizon")

# Zone principale d'upload
uploaded_file = st.file_uploader(
    "📄 Déposez votre PDF de foreclosure ici",
    type=["pdf"],
    help="Format : PDF du Bexar County avec adresses de propriétés"
)

if uploaded_file is not None:
    st.success(f"✅ Fichier chargé : **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    
    # Bouton Run Pipeline
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        run_button = st.button("🚀 RUN PIPELINE", type="primary", use_container_width=True)
    
    if run_button:
        # Créer un container pour le contenu dynamique
        status_container = st.container()
        
        with status_container:
            with st.spinner("🔄 Traitement en cours..."):
                # Sauvegarder le PDF temporairement
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    # Lancer le pipeline
                    stats = run_full_pipeline(tmp_path)
                    
                    # Afficher les résultats
                    st.success("✅ Pipeline terminé avec succès !")
                    
                    # Statistiques globales
                    st.subheader("📊 Résultats")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total adresses", stats["total_addresses"], help="Adresses extraites du PDF")
                    with col2:
                        st.metric("Géocodées", stats["geocoded"], 
                                 delta=f"{stats['geocoded']/stats['total_addresses']*100:.0f}%" if stats['total_addresses'] > 0 else "0%",
                                 help="Adresses converties en coordonnées GPS")
                    with col3:
                        st.metric("Hors zones", stats["unassigned"], help="Adresses en dehors des 4 zones définies")
                    
                    # Répartition par zone
                    st.subheader("🗺️ Répartition par zone")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    zones_info = {
                        "north": ("🧭 North", "Zone nord de San Antonio"),
                        "south": ("🧭 South", "Zone sud de San Antonio"),
                        "east": ("🧭 East", "Zone est de San Antonio"),
                        "west": ("🧭 West", "Zone ouest de San Antonio")
                    }
                    
                    for idx, (zone_key, (zone_label, zone_desc)) in enumerate(zones_info.items()):
                        with [col1, col2, col3, col4][idx]:
                            st.metric(zone_label, stats[zone_key], help=zone_desc)
                    
                    # Section téléchargement
                    st.markdown("---")
                    st.subheader("💾 Télécharger les résultats")
                    
                    output_dir = Path("data/outputs")
                    
                    # Boutons de téléchargement par zone
                    col1, col2, col3, col4 = st.columns(4)
                    zones = ["north", "south", "east", "west"]
                    
                    for idx, zone in enumerate(zones):
                        file_path = output_dir / f"{zone}_san_antonio.csv"
                        if file_path.exists() and stats[zone] > 0:
                            with open(file_path, "rb") as f:
                                [col1, col2, col3, col4][idx].download_button(
                                    label=f"📥 {zone.upper()} ({stats[zone]})",
                                    data=f,
                                    file_name=f"{zone}_san_antonio.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                        else:
                            [col1, col2, col3, col4][idx].button(
                                f"📥 {zone.upper()} (0)",
                                disabled=True,
                                use_container_width=True
                            )
                    
                    # Télécharger toutes les adresses
                    st.markdown("")
                    all_file = output_dir / "all_addresses_geocoded.csv"
                    if all_file.exists():
                        with open(all_file, "rb") as f:
                            st.download_button(
                                label=f"📥 Télécharger TOUTES les adresses ({stats['geocoded']} total)",
                                data=f,
                                file_name="all_addresses_geocoded.csv",
                                mime="text/csv",
                                use_container_width=True,
                                type="secondary"
                            )
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors du traitement : {str(e)}")
                    with st.expander("🔍 Détails de l'erreur"):
                        st.exception(e)
                
                finally:
                    # Nettoyer le fichier temporaire
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except:
                        pass

else:
    # Message d'accueil
    st.info("👆 **Commencez par uploader un PDF de foreclosure**")
    
    st.markdown("### 🎯 Comment ça marche ?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1. Extraction automatique**
        - Lit les adresses du PDF
        - Nettoie et déduplique les données
        
        **2. Géocodage intelligent**
        - OpenStreetMap (gratuit)
        - Google Maps (backup)
        """)
    
    with col2:
        st.markdown("""
        **3. Filtrage géographique**
        - Classement par zone
        - Export CSV séparé par zone
        
        **4. Téléchargement facile**
        - Un fichier par zone
        - Format CSV prêt à l'emploi
        """)