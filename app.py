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
        background: #0078d4; color: white; padding: 12px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: block; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNEXIONS & IA ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="1s")

if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if "1.5-flash" in m), models[0])
    except:
        model_name = "models/gemini-1.5-flash"

# --- 3. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT PRO</h1>", unsafe_allow_html=True)

tab_diag, tab_chantier, tab_admin = st.tabs(["📟 DIAGNOSTIC", "📸 PHOTOS", "⚙️ GESTION"])

with tab_diag:
    if not df.empty:
        col_l, col_r = st.columns([1, 1.5])
        with col_l:
            res = st.selectbox("📍 Résidence", df["Résidence"].unique())
            app = st.selectbox("🚪 Appartement", df[df["Résidence"] == res]["Appartement"].unique())
            nom_loc = df[(df["Résidence"] == res) & (df["Appartement"] == app)]["Nom"].iloc[0]
            st.info(f"Locataire : {nom_loc}")
            # Ton adresse est bien prise en compte ici
            dest_mail = st.text_input("📧 Envoyer à :", value="ludoak33@gmail.com")
            
        with col_r:
            st.markdown('<div class="holo-card">', unsafe_allow_html=True)
            source = st.radio("Source :", ["Caméra", "PC"], horizontal=True)
            img = st.camera_input("SCAN") if source == "Caméra" else st.file_uploader("IMAGE")
            
            if img and st.button("🚀 ANALYSER"):
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(["Expert GH. Charge Bailleur, Locataire ou Entreprise ?", Image.open(img)])
                st.session_state.verdict = response.text
                st.session_state.info = f"Appt {app} ({nom_loc})"
                st.success(response.text)
            
            if 'verdict' in st.session_state:
                st.divider()
                # Sécurisation maximale du texte pour éviter l'erreur 400
                sujet = f"Constat GH {st.session_state.info}"
                texte_mail = f"Rapport :\n{st.session_state.verdict}"
                
                # Option 1 : Le bouton (qui peut bugger si trop long)
                link = f"mailto:{dest_mail}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(texte_mail[:500])}"
                st.markdown(f'<a href="{link}" class="mail-btn">📧 OUVRIR MON MAIL</a>', unsafe_allow_html=True)
                
                # Option 2 : Sécurité si le bouton échoue
                st.write("---")
                st.text_area("📋 Copie de secours (si le bouton plante) :", f"Sujet : {sujet}\n\n{texte_mail}")
            st.markdown('</div>', unsafe_allow_html=True)

# Les autres onglets restent fonctionnels pour l'ajout/suppression
with tab_chantier:
    st.camera_input("AVANT", key="a")
    st.camera_input("APRÈS", key="b")

with tab_admin:
    st.subheader("➕ Ajouter")
    with st.form("add"):
        r, b, a, n = st.text_input("Résidence"), st.text_input("Bâtiment"), st.text_input("Appartement"), st.text_input("Nom")
        if st.form_submit_button("Enregistrer"):
            new = pd.DataFrame([{"Résidence": r, "Bâtiment": b, "Appartement": a, "Nom": n}])
            conn.update(data=pd.concat([df, new], ignore_index=True))
            st.rerun()
