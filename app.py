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

# --- ONGLET 1 : DIAGNOSTIC (PHOTO OU FICHIER) ---
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
            mode = st.radio("Méthode d'image :", ["Prendre une Photo", "Importer un Fichier (PC)"], horizontal=True)
            
            img_diag = None
            if mode == "Prendre une Photo":
                img_diag = st.camera_input("📸 SCANNER")
            else:
                img_diag = st.file_uploader("📂 CHOISIR UNE IMAGE", type=["jpg", "jpeg", "png"])
            
            if img_diag and st.button("🚀 LANCER L'ANALYSE"):
                try:
                    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    model = genai.GenerativeModel(next((m for m in models if "flash" in m), models[0]))
                    response = model.generate_content(["Expert GH. Charge Bailleur, Locataire ou Entreprise ?", Image.open(img_diag)])
                    st.success(response.text)
                except Exception as e: st.error(f"Erreur : {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : AVANT / APRÈS ---
with tab_avant_apres:
    st.markdown("### 🛠️ Suivi de chantier")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**ÉTAT INITIAL (AVANT)**")
        source_av = st.radio("Source Avant :", ["Caméra", "Fichier"], key="s_av", horizontal=True)
        photo_av = st.camera_input("AVANT", key="c_av") if source_av == "Caméra" else st.file_uploader("Fichier Avant", key="f_av")
    with c2:
        st.markdown("**RÉSULTAT (APRÈS)**")
        source_ap = st.radio("Source Après :", ["Caméra", "Fichier"], key="s_ap", horizontal=True)
        photo_ap = st.camera_input("APRÈS", key="c_ap") if source_ap == "Caméra" else st.file_uploader("Fichier Après", key="f_ap")

# --- ONGLET 3 : GESTION ---
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
        nom_a_supprimer = st.selectbox("Sélectionner le nom à effacer", df["Nom"].tolist())
        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
        if st.button(f"❌ SUPPRIMER DÉFINITIVEMENT {nom_a_supprimer}"):
            df_mis_a_jour = df[df["Nom"] != nom_a_supprimer]
            conn.update(data=df_mis_a_jour)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
