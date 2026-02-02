import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import urllib.parse

# --- STYLE ---
st.set_page_config(page_title="GH Expert Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card { background: rgba(255, 0, 255, 0.05); border: 1px solid #ff00ff; border-radius: 12px; padding: 20px; }
    .mail-btn {
        background: #0078d4; color: white; padding: 12px; border-radius: 20px;
        text-decoration: none; font-weight: bold; display: block; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA & IA ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl="1s")

if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in models if "1.5-flash" in m), models[0])
    except: model_name = "models/gemini-1.5-flash"

# --- INTERFACE ---
st.title("📟 GH EXPERT - DIAGNOSTIC")

if not df.empty:
    col_l, col_r = st.columns([1, 1.5])
    with col_l:
        res = st.selectbox("📍 Résidence", df["Résidence"].unique())
        app = st.selectbox("🚪 Appartement", df[df["Résidence"] == res]["Appartement"].unique())
        nom_loc = df[(df["Résidence"] == res) & (df["Appartement"] == app)]["Nom"].iloc[0]
        dest_mail = st.text_input("📧 Envoyer à :", value="ludoak33@gmail.com")
        
    with col_r:
        st.markdown('<div class="holo-card">', unsafe_allow_html=True)
        img = st.camera_input("SCAN")
        
        if img and st.button("🚀 ANALYSER"):
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(["Expert GH. Dis qui paie et pourquoi en 5 lignes max.", Image.open(img)])
            st.session_state.verdict = response.text
            st.session_state.info = f"Appt {app} ({nom_loc})"

        if 'verdict' in st.session_state:
            st.success("Analyse terminée.")
            st.info(st.session_state.verdict)
            
            # Sécurité : On tronque le texte pour le mailto (limite à 300 car.)
            sujet = f"Constat GH {st.session_state.info}"
            texte_court = st.session_state.verdict[:300] + "..."
            
            link = f"mailto:{dest_mail}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(texte_court)}"
            
            st.markdown(f'<a href="{link}" class="mail-btn">📧 TENTER L\'OUVERTURE DU MAIL</a>', unsafe_allow_html=True)
            
            st.write("---")
            st.markdown("**Solution de secours (si erreur 400) :**")
            st.text_area("📋 Rapport complet à copier/coller :", st.session_state.verdict, height=200)
        st.markdown('</div>', unsafe_allow_html=True)
