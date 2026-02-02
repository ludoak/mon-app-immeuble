import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. DESIGN HOLOGRAPHIQUE (CSS) ---
st.set_page_config(page_title="GH - Project Neon", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 2px solid rgba(255, 0, 255, 0.4);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.2);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    .neon-title {
        color: #ff00ff;
        text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff;
        font-family: 'Courier New', monospace;
        text-align: center;
        letter-spacing: 3px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff00ff, #00f2ff);
        color: white; font-weight: bold; border: none; border-radius: 20px;
    }
    .stRadio>div { color: #ff00ff !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DONNÉES & CONFIGURATION ---
DB_FILE = "base_locataires_gh.csv"
def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
    return pd.DataFrame({"Résidence": ["Canterane"], "Appartement": ["10"], "Nom": ["Locataire Test"]})

if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# Connexion IA (On force la config)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("🚨 Clé API introuvable dans les Secrets.")

# --- 3. INTERFACE PRINCIPALE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#00f2ff; opacity:0.8;'>VERSION HYBRIDE : TERRAIN & ARCHIVES</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1.3])

with col1:
    st.markdown("<h3 style='color:#ff00ff;'>👤 RÉSIDENTS</h3>", unsafe_allow_html=True)
    df = st.session_state.df_locataires
    for _, row in df.head(5).iterrows():
        st.markdown(f"<div class='holo-card'><b style='color:#ff00ff;'>{row['Nom']}</b><br><small>{row['Résidence']} - {row['Appartement']}</small></div>", unsafe_allow_html=True)

with col2:
    st.markdown("<h3 style='color:#ff00ff;'>🔧 ÉTAT SYSTÈME</h3>", unsafe_allow_html=True)
    st.markdown("<div class='holo-card'><b>RÉSEAU IA</b> : CONNECTÉ ✅<br><b>MODE</b> : SCAN & IMPORT 📡</div>", unsafe_allow_html=True)
    if st.button("🔄 RÉINITIALISER"):
        st.rerun()

with col3:
    st.markdown("<h3 style='color:#ff00ff;'>📟 DIAGNOSTIC</h3>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="holo-card">', unsafe_allow_html=True)
        
        # Sélections
        res_sel = st.selectbox("Résidence", df["Résidence"].unique())
        appt_sel = st.selectbox("Appartement", df[df["Résidence"] == res_sel]["Appartement"])
        
        # --- SOURCE PHOTO HYBRIDE ---
        source = st.radio("Acquisition de l'image :", ["Scanner (Photo)", "Importer (Galerie)"], horizontal=True)
        
        photo = None
        if source == "Scanner (Photo)":
            photo = st.camera_input("SCANNER")
        else:
            photo = st.file_uploader("CHOISIR UN FICHIER", type=["jpg", "jpeg", "png"])
        
        if photo and st.button("🚀 LANCER L'ANALYSE"):
            try:
                # Utilisation d'un modèle stable
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(photo)
                
                with st.spinner("Analyse du flux visuel..."):
                    prompt = "Expert bâtiment Gironde Habitat. Analyse la photo. Dis si c'est pour le BAILLEUR, le LOCATAIRE ou un PRESTATAIRE. Réponse courte et précise."
                    response = model.generate_content([prompt, img])
                    
                    st.markdown(f"<h4 style='color:#ff00ff;'>RÉSULTAT :</h4><p>{response.text}</p>", unsafe_allow_html=True)
                    
                    # Courrier automatique
                    st.divider()
                    nom_loc = df[df["Appartement"] == appt_sel]["Nom"].iloc[0]
                    date_str = datetime.now().strftime("%d/%m/%Y")
                    
                    lettre = f"OBJET : Signalement {res_sel} / {appt_sel}\nDATE : {date_str}\nLOCATAIRE : {nom_loc}\n\nCONSTAT : {response.text}"
                    st.text_area("Courrier prêt à copier :", lettre, height=150)
                    
            except Exception as e:
                st.error(f"Erreur lors du scan : {e}")
        st.markdown('</div>', unsafe_allow_html=True)
