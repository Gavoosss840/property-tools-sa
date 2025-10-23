# app.py
# Interface web sÃ©curisÃ©e pour Property Tools
import streamlit as st
from pathlib import Path
import tempfile
import os
from dotenv import load_dotenv
from src.pipeline import run_excel_pipeline, run_csv_pipeline

# Charger les variables d'environnement
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Property Tools - San Antonio",
    page_icon="ðŸ ",
    layout="wide"
)

# ==========================================
# SYSTÃˆME D'AUTHENTIFICATION
# ==========================================
def check_password():
    """Retourne True si le mot de passe est correct"""
    
    def password_entered():
        """VÃ©rifie le mot de passe entrÃ©"""
        correct_password = st.secrets.get("PASSWORD", os.getenv("PASSWORD", ""))
        
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Ne pas garder le mot de passe en mÃ©moire
        else:
            st.session_state["password_correct"] = False

    # Si dÃ©jÃ  authentifiÃ©
    if st.session_state.get("password_correct", False):
        return True

    # Afficher le formulaire de connexion
    st.markdown("<h1 style='text-align: center;'>ðŸ  Property Tools</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>San Antonio Foreclosure Analyzer</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### ðŸ”’ Connexion")
        st.text_input(
            "Mot de passe",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Entrez votre mot de passe"
        )
        
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("âŒ Mot de passe incorrect")
        
        st.info("ðŸ’¡ Contactez l'administrateur pour obtenir l'accÃ¨s")
    
    return False

# VÃ©rifier l'authentification
if not check_password():
    st.stop()

# ==========================================
# APPLICATION PRINCIPALE (aprÃ¨s authentification)
# ==========================================

# En-tÃªte avec bouton dÃ©connexion
col1, col2 = st.columns([5, 1])
with col1:
    st.title("ðŸ  Property Tools - San Antonio")
    st.markdown("**Analyseur de foreclosures par zones gÃ©ographiques**")
with col2:
    st.write("")  # Espace
    if st.button("ðŸšª DÃ©connexion", type="secondary"):
        st.session_state["password_correct"] = False
        st.rerun()

st.markdown("---")

# Sidebar pour les infos
with st.sidebar:
    st.header("ðŸ“‹ Mode d'emploi")
    st.markdown("""
    ### Ã‰tapes :
    ### Steps :
    1. Upload your Excel (.xlsx) or CSV of addresses
    3. **ðŸ’¾ TÃ©lÃ©chargez** les CSVs par zone
    
    ### Zones disponibles :
    - ðŸ§­ **North** San Antonio
    - ðŸ§­ **South** San Antonio
    - ðŸ§­ **East** San Antonio
    - ðŸ§­ **West** San Antonio
    """)
    
    st.markdown("---")
    
    st.header("â„¹ï¸ Format attendu")
    st.header("Expected format (Excel or CSV)")
    st.code("""
address,city,state,zip
123 MAIN ST,SAN ANTONIO,TX,78201
456 OAK AVE,SAN ANTONIO,TX,78220
    """)
    st.markdown("---")
    st.caption("ðŸ”’ Application sÃ©curisÃ©e")
    st.caption("Â© 2025 B. Horizon")

# Zone principale d'upload
uploaded_file = st.file_uploader(
    "Upload your Excel (.xlsx) or CSV here",
    type=["xlsx","csv"],
    help="Colonnes suggerees: address, city, state, zip (variantes communes auto-detectees)"
)

if uploaded_file is not None:
    st.success(f"âœ… Fichier chargÃ© : **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    
    # Bouton Run Pipeline
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        run_button = st.button("ðŸš€ RUN PIPELINE", type="primary", use_container_width=True)
    
    if run_button:
        # CrÃ©er un container pour le contenu dynamique
        status_container = st.container()
        
        with status_container:
            with st.spinner("ðŸ”„ Traitement en cours..."):
                # Save uploaded file temporarily (Excel or CSV)
                _name = uploaded_file.name.lower()
                _is_xlsx = _name.endswith('.xlsx')
                _suffix = '.xlsx' if _is_xlsx else '.csv'
                with tempfile.NamedTemporaryFile(delete=False, suffix=_suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                try:
                    # Run pipeline based on file type
                    stats = run_excel_pipeline(tmp_path) if _is_xlsx else run_csv_pipeline(tmp_path)
                    st.success("âœ… Pipeline terminÃ© avec succÃ¨s !")
                    
                    # Statistiques globales
                    st.subheader("ðŸ“Š RÃ©sultats")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total adresses", stats["total_addresses"], help="Adresses lues depuis le fichier")
                    with col2:
                        st.metric("GÃ©ocodÃ©es", stats["geocoded"], 
                                 delta=f"{stats['geocoded']/stats['total_addresses']*100:.0f}%" if stats['total_addresses'] > 0 else "0%",
                                 help="Adresses converties en coordonnÃ©es GPS")
                    with col3:
                        st.metric("Hors zones", stats["unassigned"], help="Adresses en dehors des 4 zones dÃ©finies")
                    
                    # RÃ©partition par zone
                    st.subheader("ðŸ—ºï¸ RÃ©partition par zone")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    zones_info = {
                        "north": ("ðŸ§­ North", "Zone nord de San Antonio"),
                        "south": ("ðŸ§­ South", "Zone sud de San Antonio"),
                        "east": ("ðŸ§­ East", "Zone est de San Antonio"),
                        "west": ("ðŸ§­ West", "Zone ouest de San Antonio")
                    }
                    
                    for idx, (zone_key, (zone_label, zone_desc)) in enumerate(zones_info.items()):
                        with [col1, col2, col3, col4][idx]:
                            st.metric(zone_label, stats[zone_key], help=zone_desc)
                    
                    # Section tÃ©lÃ©chargement
                    st.markdown("---")
                    st.subheader("ðŸ’¾ TÃ©lÃ©charger les rÃ©sultats")
                    
                    output_dir = Path("data/outputs")
                    
                    # Boutons de tÃ©lÃ©chargement par zone
                    col1, col2, col3, col4 = st.columns(4)
                    zones = ["north", "south", "east", "west"]
                    
                    for idx, zone in enumerate(zones):
                        file_path = output_dir / f"{zone}_san_antonio.csv"
                        if file_path.exists() and stats[zone] > 0:
                            with open(file_path, "rb") as f:
                                [col1, col2, col3, col4][idx].download_button(
                                    label=f"ðŸ“¥ {zone.upper()} ({stats[zone]})",
                                    data=f,
                                    file_name=f"{zone}_san_antonio.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                        else:
                            [col1, col2, col3, col4][idx].button(
                                f"ðŸ“¥ {zone.upper()} (0)",
                                disabled=True,
                                use_container_width=True
                            )
                    
                    # TÃ©lÃ©charger toutes les adresses
                    st.markdown("")
                    all_file = output_dir / "all_addresses_geocoded.csv"
                    if all_file.exists():
                        with open(all_file, "rb") as f:
                            st.download_button(
                                label=f"ðŸ“¥ TÃ©lÃ©charger TOUTES les adresses ({stats['geocoded']} total)",
                                data=f,
                                file_name="all_addresses_geocoded.csv",
                                mime="text/csv",
                                use_container_width=True,
                                type="secondary"
                            )
                    
                except Exception as e:
                    st.error(f"âŒ Erreur lors du traitement : {str(e)}")
                    with st.expander("ðŸ” DÃ©tails de l'erreur"):
                        st.exception(e)
                
                finally:
                    # Nettoyer le fichier temporaire
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except:
                        pass
else:
    # Message d'accueil
    st.info("?? **Commencez par uploader un fichier Excel (.xlsx) d'adresses**")
    
    st.info("Upload a Excel (.xlsx) or CSV file of addresses to start")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1. Lecture du fichier**
        - Lit les adresses depuis Excel (.xlsx)
        
        
        **2. GÃ©ocodage intelligent**
        - OpenStreetMap (gratuit)
        - Google Maps (backup)
        """)
    
    with col2:
        st.markdown("""
        **3. Filtrage gÃ©ographique**
        - Classement par zone
        - Export CSV sÃ©parÃ© par zone
        
        **4. TÃ©lÃ©chargement facile**
        - Un fichier par zone
        - Format CSV prÃªt Ã  l'emploi
        """)


