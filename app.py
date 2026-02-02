import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="GH Expert - Intégral", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.2);
    }
    .neon-title { color: #ff00ff; text-align: center; text-shadow: 0 0 15px #ff00ff; font-family: monospace; }
    .stButton>button { background: linear-gradient(90deg, #ff00ff, #00f2ff); color: white; font-weight: bold; border-radius: 20px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNEXIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)
def load_data():
    try: return conn.read(ttl="1s")
    except: return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df = load_data()

if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT PRO</h1>", unsafe_allow_html=True)

tab_diag, tab_guide, tab_admin = st.tabs(["📟 DIAGNOSTIC", "📋 GUIDE DES CHARGES", "⚙️ GESTION"])

# --- ONGLET 1 : DIAGNOSTIC ---
with tab_diag:
    if not df.empty:
        col_list, col_scan = st.columns([1, 1.5])
        with col_list:
            st.subheader("👥 RÉSIDENTS")
            st.dataframe(df, use_container_width=True, hide_index=True)
        with col_scan:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            res_sel = st.selectbox("📍 Résidence", df["Résidence"].unique())
            bat_sel = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res_sel]["Bâtiment"].unique())
            appt_sel = st.selectbox("門 Appartement", df[(df["Résidence"] == res_sel) & (df["Bâtiment"] == bat_sel)]["Appartement"].unique())
            
            photo = st.camera_input("SCAN")
            if photo and st.button("🚀 ANALYSER"):
                try:
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    img = Image.open(photo)
                    response = model.generate_content(["Analyse technique bâtiment. Qui paie : Bailleur, Locataire ou Prestataire ?", img])
                    st.info(response.text)
                except Exception as e: st.error(f"Erreur : {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : LE GUIDE DES COULEURS (Nouveau !) ---
with tab_guide:
    st.subheader("🔍 Répartition des Responsabilités")
    
    # Création du tableau de référence
    guide_data = {
        "Équipement": ["Robinetterie", "Chaudière", "Menuiserie", "Électricité", "Gros œuvre", "Interphone"],
        "Responsable": ["LOCATAIRE", "PRESTATAIRE (Contrat)", "LOCATAIRE", "LOCATAIRE", "BAILLEUR (GH)", "BAILLEUR (GH)"],
        "Détails": ["Joints, mousseurs", "Entretien annuel", "Graissage, poignées", "Prises, ampoules", "Structure, façade", "Panne réseau"]
    }
    df_guide = pd.DataFrame(guide_data)

    def color_responsable(val):
        color = '#2ecc71' if val == 'LOCATAIRE' else '#3498db' if val == 'BAILLEUR (GH)' else '#e67e22'
        return f'background-color: {color}; color: white; font-weight: bold'

    st.table(df_guide.style.applymap(color_responsable, subset=['Responsable']))
    
    st.markdown("""
    <div style="display: flex; gap: 20px; justify-content: center; margin-top: 20px;">
        <span style="background:#2ecc71; padding:10px; border-radius:10px;">🟢 Locataire</span>
        <span style="background:#3498db; padding:10px; border-radius:10px;">🔵 Gironde Habitat</span>
        <span style="background:#e67e22; padding:10px; border-radius:10px;">🟠 Prestataire / Entreprise</span>
    </div>
    """, unsafe_allow_html=True)

# --- ONGLET 3 : GESTION ---
with tab_admin:
    st.subheader("⚙️ Configuration de la base")
    # ... (Le code d'ajout/suppression reste ici)
