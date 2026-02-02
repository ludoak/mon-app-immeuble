import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import urllib.parse

# --- 1. STYLE & DESIGN ---
st.set_page_config(page_title="GH Expert Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 12px; padding: 20px; margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.2);
    }
    .neon-title { color: #ff00ff; text-align: center; text-shadow: 0 0 15px #ff00ff; font-family: monospace; }
    .stButton>button { background: linear-gradient(90deg, #ff00ff, #00f2ff); color: white; font-weight: bold; border-radius: 20px; }
    .mail-btn {
        background: #0078d4; color: white; padding: 12px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: block; text-align: center;
    }
    .badge-loc { background-color: #2ecc71; color: white; padding: 4px 8px; border-radius: 5px; }
    .badge-gh { background-color: #3498db; color: white; padding: 4px 8px; border-radius: 5px; }
    .badge-ent { background-color: #e67e22; color: white; padding: 4px 8px; border-radius: 5px; }
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
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if "1.5-flash" in m), models[0])
    except: model_name = "models/gemini-1.5-flash"

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT PRO</h1>", unsafe_allow_html=True)

tab_diag, tab_photos, tab_guide, tab_admin = st.tabs([
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
            st.subheader("👥 LOCATAIRE")
            res = st.selectbox("📍 Résidence", df["Résidence"].unique(), key="sel_res")
            app = st.selectbox("🚪 Appartement", df[df["Résidence"] == res]["Appartement"].unique(), key="sel_app")
            nom_loc = df[(df["Résidence"] == res) & (df["Appartement"] == app)]["Nom"].iloc[0]
            st.warning(f"Occupant : {nom_loc}")
            dest_mail = st.text_input("📧 Mail destinataire :", value="ludoak33@gmail.com")
            
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            src = st.radio("Source Image :", ["Caméra", "PC / Galerie"], horizontal=True)
            img = st.camera_input("SCAN") if src == "Caméra" else st.file_uploader("IMPORTER")
            
            if img and st.button("🚀 ANALYSER"):
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(["Expert GH. Qui paie : Bailleur, Locataire ou Entreprise ?", Image.open(img)])
                st.session_state.verdict = response.text
                st.session_state.info = f"Appt {app} ({nom_loc})"
            
            if 'verdict' in st.session_state:
                st.info(st.session_state.verdict)
                sujet = f"Constat GH {st.session_state.info}"
                # On tronque pour éviter l'erreur 400
                mail_link = f"mailto:{dest_mail}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(st.session_state.verdict[:400])}"
                st.markdown(f'<a href="{mail_link}" class="mail-btn">📧 OUVRIR LE MAIL</a>', unsafe_allow_html=True)
                st.text_area("📋 Copie complète (Sécurité) :", st.session_state.verdict)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ONGLET 2 : AVANT / APRÈS ---
with tab_photos:
    st.subheader("🛠️ Suivi de travaux")
    c1, c2 = st.columns(2)
    with c1: st.camera_input("📷 AVANT INTERVENTION", key="cam_av")
    with c2: st.camera_input("📷 APRÈS INTERVENTION", key="cam_ap")

# --- ONGLET 3 : GUIDE DES CHARGES ---
with tab_guide:
    st.subheader("🔍 Matrice des Responsabilités")
    
    guide_data = [
        {"Équipement": "Robinetterie / Joints", "Responsable": "LOCATAIRE", "Couleur": "badge-loc"},
        {"Équipement": "Chaudière / VMC", "Responsable": "ENTREPRISE (Contrat)", "Couleur": "badge-ent"},
        {"Équipement": "Gros œuvre / Toiture", "Responsable": "BAILLEUR (GH)", "Couleur": "badge-gh"},
    ]
    for item in guide_data:
        st.markdown(f"**{item['Équipement']}** : <span class='{item['Couleur']}'>{item['Responsable']}</span>", unsafe_allow_html=True)

# --- ONGLET 4 : GESTION ---
with tab_admin:
    st.subheader("➕ Ajouter un résident")
    with st.form("add"):
        r, b, a, n = st.text_input("Résidence"), st.text_input("Bâtiment"), st.text_input("Appartement"), st.text_input("Nom")
        if st.form_submit_button("💾 ENREGISTRER"):
            new = pd.DataFrame([{"Résidence": r, "Bâtiment": b, "Appartement": a, "Nom": n}])
            conn.update(data=pd.concat([df, new], ignore_index=True))
            st.success("Ajouté !")
            st.rerun()
    
    st.divider()
    st.subheader("🗑️ Supprimer")
    if not df.empty:
        target = st.selectbox("Choisir à supprimer", df["Nom"].tolist())
        if st.button("❌ SUPPRIMER DÉFINITIVEMENT"):
            conn.update(data=df[df["Nom"] != target])
            st.rerun()
