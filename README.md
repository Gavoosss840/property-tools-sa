% README content is below
Property Tools – San Antonio (Streamlit)

Analyze uploaded CSVs of addresses, geocode (OSM first, Google as fallback), and split results into San Antonio zones (North/South/East/West). Built with Streamlit.

Quick Start (Local)
- Python 3.10–3.12
- Create venv (optional):
  - Windows: `python -m venv .venv && .\\.venv\\Scripts\\Activate.ps1`
- Install deps: `pip install -r requirements.txt`
- Set secrets locally in a `.env` file (not committed):
  - `PASSWORD=choose_app_password`
  - `GOOGLE_MAPS_API_KEY=your_google_maps_key`
- Run: `streamlit run app.py`

App Secrets
The app reads secrets in this order:
1) Streamlit Cloud secrets (st.secrets)
2) Environment variables / `.env`

Required keys:
- `PASSWORD` – for simple app authentication
- `GOOGLE_MAPS_API_KEY` – only used if OSM fails (optional but recommended)

Data and Outputs
- Upload a CSV of addresses in the UI (columns like `address, city, state, zip`; common variants are auto-detected).
- Outputs are written to `data/outputs/` (ignored by Git):
  - `north_san_antonio.csv`, `south_san_antonio.csv`, `east_san_antonio.csv`, `west_san_antonio.csv`
  - `all_addresses_geocoded.csv`
- A cache file `data/geocode_cache.csv` is used to speed up repeated runs (ignored by Git).

Deploy on Streamlit Community Cloud
1. Sign in at https://share.streamlit.io (or via streamlit.io → Sign in).
2. New app → pick repo: `Gavoosss840/property-tools-sa`, branch: `main`, file: `app.py`.
3. Open the app settings → “Secrets” and add:
   PASSWORD = "your_password"
   GOOGLE_MAPS_API_KEY = "your_google_maps_api_key"
4. Deploy. The build uses `requirements.txt` automatically.

Troubleshooting
- If Google rate limits or fails, OSM-only results appear; Google fallback requires `GOOGLE_MAPS_API_KEY`.
- Streamlit Cloud has ephemeral storage; outputs are available for the session but not persisted across rebuilds.
- If you see dependency errors on Cloud, ensure `requirements.txt` is up-to-date locally and pushed.

License
Private project. All rights reserved.

