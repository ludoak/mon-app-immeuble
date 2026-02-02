import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import io

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="GH Expert Pro", layout="wide")

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
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT 2.0</h1>", unsafe_allow_html=True)

tab_diag, tab_avant_apres, tab_guide, tab_admin = st.tabs([
    "📟 DIAGNOSTIC IA", 
    "📸 AVANT / APRÈS", 
    "📋 GUIDE DES CHARGES", 
    "⚙️ GESTION"
])

# --- ONGLET 1 : DIAGNOSTIC ---
with tab_diag:
    if not df.empty:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            st.subheader("👥 RÉSIDENTS")
            st.dataframe(df, use_container_width=True, hide_index=True)
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            res = st.selectbox("📍 Résidence", df["Résidence"].unique(), key="diag_res")
            bat = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res]["Bâtiment"].unique(), key="diag_bat")
            app = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res) & (df["Bâtiment"] == bat)]["Appartement"].unique(), key="diag_app")
            
            img_file = st.camera_input("SCANNER LE DÉSORDRE")
            if img_file and st.button("🚀 ANALYSER"):
                try:
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    response = model.generate_content(["Analyse technique : Qui paie (GH, Locataire ou Entreprise) ?", Image.open(img_file)])
                    st.session_state.last_report = response.text
                    st.info(response.text)
                except Exception as e: st.error(f"Erreur : {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : AVANT / APRÈS (Nouveau !) ---
with tab_avant_apres:
    st.markdown("### 🛠️ Comparatif de Travaux")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**CONSTAT INITIAL (AVANT)**")
        photo_avant = st.camera_input("PHOTO AVANT", key="avant")
    with c2:
        st.markdown("**RÉSULTAT (APRÈS)**")
        photo_apres = st.camera_input("PHOTO APRÈS", key="apres")
    
    if photo_avant and photo_apres:
        st.success("✅ Comparatif prêt pour le rapport !")
        # Option pour générer un résumé de la prestation
        if st.button("📝 GÉNÉRER RAPPORT PDF (Simulé)"):
            st.write("🔄 Compilation des photos et du diagnostic en cours...")
            st.balloons()

# --- ONGLET 3 : GUIDE ---
with tab_guide:
    st.markdown("### 🔍 Matrice des Responsabilités")
    # (Le code de ton guide coloré reste ici)
    st.write("Consultez les codes couleurs pour valider le diagnostic.")

# --- ONGLET 4 : GESTION ---
with tab_admin:
    st.subheader("⚙️ Administration du Google Sheets")
    # (Le code d'ajout/suppression reste ici)
