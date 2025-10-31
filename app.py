# app.py
# Interface web sécurisée pour Property Tools
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
        try:
            secrets_password = st.secrets["PASSWORD"]
        except Exception:
            secrets_password = None
        correct_password = secrets_password or os.getenv("PASSWORD", "")
        
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Si déjà authentifié
    if st.session_state.get("password_correct", False):
        return True

    # Afficher le formulaire de connexion
    st.markdown("<h1 style='text-align: center;'>🏠 Property Tools</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>San Antonio Address Analyzer</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔒 Login")
        st.text_input(
            "Password",
            type="password",
            on_change=password_entered,
            key="password",
            placeholder="Enter your password"
        )
        
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Incorrect password")
        
        st.info("💡 Contact administrator for access")
    
    return False

# Vérifier l'authentification
if not check_password():
    st.stop()

# ==========================================
# APPLICATION PRINCIPALE
# ==========================================

# En-tête avec bouton déconnexion
col1, col2 = st.columns([5, 1])
with col1:
    st.title("🏠 Property Tools - San Antonio")
    st.markdown("**Address analyzer by geographic zones**")
with col2:
    st.write("")
    if st.button("🚪 Logout", type="secondary"):
        st.session_state["password_correct"] = False
        st.rerun()

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("📋 How to use")
    st.markdown("""
    ### Steps:
    1. **📄 Upload** your Excel (.xlsx) or CSV
    2. **🚀 Click** "Run Pipeline"
    3. **💾 Download** CSVs by zone
    
    ### Available zones:
    - 🧭 **North** San Antonio
    - 🧭 **South** San Antonio
    - 🧭 **East** San Antonio
    - 🧭 **West** San Antonio
    """)
    
    st.markdown("---")
    
    st.header("ℹ️ Expected format")
    st.code("""
address,city,state,zip
123 MAIN ST,SAN ANTONIO,TX,78201
456 OAK AVE,SAN ANTONIO,TX,78220
    """)
    
    st.markdown("---")
    st.caption("🔒 Secure application")
    st.caption("© 2025 B. Horizon")

# Upload zone
uploaded_file = st.file_uploader(
    "📄 Upload your Excel (.xlsx) or CSV here",
    type=["xlsx", "csv"],
    help="Suggested columns: address, city, state, zip (common variants auto-detected)"
)


def render_pipeline_results(stats):
    """Display the latest pipeline outcome and download buttons."""
    st.success("✅ Pipeline completed successfully!")

    st.subheader("📊 Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total addresses", stats["total_addresses"])
    with col2:
        pct = (
            f"{stats['geocoded'] / stats['total_addresses'] * 100:.0f}%"
            if stats["total_addresses"] > 0
            else "0%"
        )
        st.metric("Geocoded", stats["geocoded"], delta=pct)
    with col3:
        st.metric("Out of zones", stats["unassigned"])

    st.subheader("🗺️ Distribution by zone")
    zone_cols = st.columns(4)
    zones_info = [
        ("north", "🧭 North", "North zone of San Antonio"),
        ("south", "🧭 South", "South zone of San Antonio"),
        ("east", "🧭 East", "East zone of San Antonio"),
        ("west", "🧭 West", "West zone of San Antonio"),
    ]
    for idx, (zone_key, zone_label, zone_desc) in enumerate(zones_info):
        with zone_cols[idx]:
            st.metric(zone_label, stats[zone_key], help=zone_desc)

    st.markdown("---")
    st.subheader("💾 Download results")
    download_cols = st.columns(4)
    for idx, (zone_key, _, _) in enumerate(zones_info):
        file_path = Path("data/outputs") / f"{zone_key}_san_antonio.csv"
        if file_path.exists() and stats[zone_key] > 0:
            download_cols[idx].download_button(
                label=f"📥 {zone_key.upper()} ({stats[zone_key]})",
                data=file_path.read_bytes(),
                file_name=f"{zone_key}_san_antonio.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            download_cols[idx].button(
                f"📥 {zone_key.upper()} (0)",
                disabled=True,
                use_container_width=True,
            )

    all_file = Path("data/outputs") / "all_addresses_geocoded.csv"
    if all_file.exists():
        st.download_button(
            label=f"📥 Download ALL addresses ({stats['geocoded']} total)",
            data=all_file.read_bytes(),
            file_name="all_addresses_geocoded.csv",
            mime="text/csv",
            use_container_width=True,
            type="secondary",
        )

if uploaded_file is not None:
    st.success(f"✅ File loaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    session = st.session_state

    file_signature = f"{uploaded_file.name}:{uploaded_file.size}"
    if session.get("last_file_signature") != file_signature:
        session["last_file_signature"] = file_signature
        session.pop("pipeline_stats", None)
        session.pop("pipeline_error", None)
    
    # Run button
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        run_button = st.button(
            "🚀 RUN PIPELINE",
            type="primary",
            use_container_width=True,
            key="run_pipeline_btn",
        )
    
    if run_button:
        status_container = st.container()
        
        with status_container:
            with st.spinner("🔄 Processing..."):
                # Save file temporarily
                _name = uploaded_file.name.lower()
                _is_xlsx = _name.endswith('.xlsx')
                _suffix = '.xlsx' if _is_xlsx else '.csv'
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=_suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                try:
                    stats = (
                        run_excel_pipeline(tmp_path)
                        if _is_xlsx
                        else run_csv_pipeline(tmp_path)
                    )
                    session["pipeline_stats"] = stats
                    session.pop("pipeline_error", None)
                except Exception as e:
                    st.error(f"❌ Error during processing: {str(e)}")
                    with st.expander("🔍 Error details"):
                        st.exception(e)
                    session["pipeline_error"] = str(e)
                    session.pop("pipeline_stats", None)
                
                finally:
                    # Clean temp file
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except:
                        pass

    stats_to_render = session.get("pipeline_stats")
    if stats_to_render:
        render_pipeline_results(stats_to_render)
    elif session.get("pipeline_error"):
        st.error(f"❌ Last pipeline run failed: {session['pipeline_error']}")

else:
    # Welcome message
    st.info("👆 **Start by uploading an Excel (.xlsx) or CSV file**")
    
    st.markdown("### 🎯 How it works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **1. File reading**
        - Reads addresses from Excel/CSV
        - Auto-detects column names
        
        **2. Smart geocoding**
        - OpenStreetMap (free)
        - Google Maps (backup)
        """)
    
    with col2:
        st.markdown("""
        **3. Geographic filtering**
        - Classification by zone
        - Separate CSV export per zone
        
        **4. Easy download**
        - One file per zone
        - Ready-to-use CSV format
        """)
