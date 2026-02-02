import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import urllib.parse

# --- 1. CONFIG & STYLE ---
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
        background: linear-gradient(90deg, #0078d4, #00bcf2);
        color: white; padding: 12px 20px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: block; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNEXIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)
def load_data():
    try: return conn.read(ttl="1s")
    except: return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df = load_data()

# Configuration IA avec détection intelligente
if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
    # On cherche le modèle disponible qui supporte la vision
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # On cherche 'gemini-1.5-flash' ou le premier de la liste
        model_name = next((m for m in available_models if "1.5-flash" in m), available_models[0])
    except:
        model_name = "models/gemini-1.5-flash" # Repli par défaut

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT PRO</h1>", unsafe_allow_html=True)

tab_diag, tab_chantier, tab_admin = st.tabs(["📟 DIAGNOSTIC IA", "📸 AVANT / APRÈS", "⚙️ GESTION"])

with tab_diag:
    if not df.empty:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            st.subheader("👥 CHOIX LOCATAIRE")
            res = st.selectbox("📍 Résidence", df["Résidence"].unique())
            bat = st.selectbox("🏢 Bâtiment", df[df["Résidence"] == res]["Bâtiment"].unique())
            app = st.selectbox("🚪 Appartement", df[(df["Résidence"] == res) & (df["Bâtiment"] == bat)]["Appartement"].unique())
            nom_loc = df[(df["Résidence"] == res) & (df["Bâtiment"] == bat) & (df["Appartement"] == app)]["Nom"].iloc[0]
            st.warning(f"Occupant : {nom_loc}")
            dest_mail = st.text_input("📧 Mail destinataire :", placeholder="ex: technique@gh.fr")
            
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            source_diag = st.radio("Source image :", ["Caméra", "Fichier PC/Tel"], horizontal=True, key="src_diag")
            img_diag = st.camera_input("SCAN") if source_diag == "Caméra" else st.file_uploader("IMPORTER", type=["jpg", "png", "jpeg"])
            
            if img_diag and st.button("🚀 ANALYSER"):
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(["Expert GH. Charge Bailleur, Locataire ou Entreprise ?", Image.open(img_diag)])
                    st.session_state.verdict = response.text
                    st.session_state.loc_info = f"{res} - {bat} - Appt {app}"
                    st.session_state.loc_name = nom_loc
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Détails de l'erreur : {e}")
            
            if 'verdict' in st.session_state:
                st.divider()
                objet = urllib.parse.quote(f"Constat GH : {st.session_state.loc_info}")
                corps = urllib.parse.quote(f"Bonjour,\n\nLogement : {st.session_state.loc_name}\n\nDiagnostic :\n{st.session_state.verdict}")
                st.markdown(f'<a href="mailto:{dest_mail}?subject={objet}&body={corps}" class="mail-btn">📧 GÉNÉRER LE MAIL</a>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# Les onglets 2 et 3 restent identiques
with tab_chantier:
    st.markdown("### 🛠️ Suivi de travaux")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**AVANT**")
        s_av = st.radio("Source A", ["Caméra", "Fichier"], horizontal=True, key="s_av")
        if s_av == "Caméra": st.camera_input("AVANT", key="c_av")
        else: st.file_uploader("Fichier A", key="f_av")
    with c2:
        st.markdown("**APRÈS**")
        s_ap = st.radio("Source B", ["Caméra", "Fichier"], horizontal=True, key="s_ap")
        if s_ap == "Caméra": st.camera_input("APRÈS", key="c_ap")
        else: st.file_uploader("Fichier B", key="f_ap")

with tab_admin:
    st.subheader("⚙️ Gestion")
    with st.form("add_loc"):
        ca, cb = st.columns(2)
        r_i = ca.text_input("Résidence")
        b_i = ca.text_input("Bâtiment")
        a_i = cb.text_input("Appartement")
        n_i = cb.text_input("Nom")
        if st.form_submit_button("💾 ENREGISTRER"):
            new_row = pd.DataFrame([{"Résidence": r_i, "Bâtiment": b_i, "Appartement": a_i, "Nom": n_i}])
            conn.update(data=pd.concat([df, new_row], ignore_index=True))
            st.rerun()
    
    st.divider()
    if not df.empty:
        target = st.selectbox("Supprimer :", df["Nom"].tolist())
        if st.button("❌ SUPPRIMER"):
            conn.update(data=df[df["Nom"] != target])
            st.rerun()
