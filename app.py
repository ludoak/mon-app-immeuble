import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime

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
    .stButton>button { background: linear-gradient(90deg, #ff00ff, #00f2ff); color: white; font-weight: bold; border-radius: 20px; border: none; width: 100%; }
    .delete-btn>button { background: linear-gradient(90deg, #ff4b4b, #ff0000) !important; }
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

tab_diag, tab_avant_apres, tab_admin = st.tabs([
    "📟 DIAGNOSTIC IA", 
    "📸 AVANT / APRÈS", 
    "⚙️ GESTION & SUPPRESSION"
])

# --- ONGLET 1 : DIAGNOSTIC (APPAREIL PHOTO 1) ---
with tab_diag:
    if not df.empty:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            st.subheader("👥 CHOIX LOCATAIRE")
            res = st.selectbox("📍 Résidence", df["Résidence"].unique())
            bat = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res]["Bâtiment"].unique())
            app = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res) & (df["Bâtiment"] == bat)]["Appartement"].unique())
            nom_loc = df[(df["Résidence"] == res) & (df["Bâtiment"] == bat) & (df["Appartement"] == app)]["Nom"].iloc[0]
            st.warning(f"Occupant actuel : {nom_loc}")
            
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            # L'appareil photo pour le diagnostic
            img_diag = st.camera_input("📸 SCANNER LE PROBLÈME")
            
            if img_diag and st.button("🚀 LANCER L'ANALYSE"):
                try:
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    response = model.generate_content(["Expert GH. Charge Bailleur, Locataire ou Entreprise ?", Image.open(img_diag)])
                    st.session_state.last_report = response.text
                    st.success(response.text)
                except Exception as e: st.error(f"Erreur : {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : AVANT / APRÈS (APPAREILS PHOTO 2 & 3) ---
with tab_avant_apres:
    st.markdown("### 🛠️ Suivi de chantier")
    c1, c2 = st.columns(2)
    with c1:
        st.camera_input("📷 PHOTO AVANT", key="cam_avant")
    with c2:
        st.camera_input("📷 PHOTO APRÈS", key="cam_apres")

# --- ONGLET 3 : GESTION (AJOUTER ET SUPPRIMER) ---
with tab_admin:
    st.subheader("➕ Ajouter un résident")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        r_in = c1.text_input("Résidence")
        b_in = c1.text_input("Bâtiment")
        a_in = c2.text_input("Appartement")
        n_in = c2.text_input("Nom")
        if st.form_submit_button("💾 ENREGISTRER"):
            new_row = pd.DataFrame([{"Résidence": r_in, "Bâtiment": b_in, "Appartement": a_in, "Nom": n_in}])
            conn.update(data=pd.concat([df, new_row], ignore_index=True))
            st.rerun()

    st.divider()
    
    st.subheader("🗑️ Supprimer un résident")
    if not df.empty:
        # On affiche la liste pour choisir qui supprimer
        liste_noms = df["Nom"].tolist()
        nom_a_supprimer = st.selectbox("Sélectionner le nom à effacer", liste_noms)
        
        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
        if st.button(f"❌ SUPPRIMER DÉFINITIVEMENT {nom_a_supprimer}"):
            df_mis_a_jour = df[df["Nom"] != nom_a_supprimer]
            conn.update(data=df_mis_a_jour)
            st.error(f"{nom_a_supprimer} a été retiré du Google Sheets.")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
