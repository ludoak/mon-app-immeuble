import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. DESIGN HOLOGRAPHIQUE (STYLE NEON) ---
st.set_page_config(page_title="GH - Project Neon", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #00f2ff; }
    .holo-card {
        background: rgba(255, 0, 255, 0.05);
        border: 1px solid #ff00ff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 0 15px rgba(255, 0, 255, 0.2);
    }
    .neon-title { 
        color: #ff00ff; 
        text-align: center; 
        text-shadow: 0 0 15px #ff00ff;
        font-family: 'Courier New', monospace;
    }
    .stButton>button {
        background: linear-gradient(90deg, #ff00ff, #00f2ff);
        color: white; font-weight: bold; border-radius: 20px; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURATION IA ---
if "CLE_TEST" in st.secrets:
    genai.configure(api_key=st.secrets["CLE_TEST"])
else:
    st.error("🚨 Clé introuvable dans les secrets Streamlit.")
    st.stop()

# --- 3. CHARGEMENT DES DONNÉES ---
DB_FILE = "base_locataires_gh.csv"
def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
    return pd.DataFrame({"Résidence": ["Canterane"], "Appartement": ["10"], "Nom": ["Locataire Test"]})

if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# --- 4. INTERFACE ---
st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT</h1>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("👥 RÉSIDENTS")
    df = st.session_state.df_locataires
    st.dataframe(df, use_container_width=True, hide_index=True)

with col2:
    st.markdown('<div class="holo-card">', unsafe_allow_html=True)
    res_sel = st.selectbox("📍 Résidence", df["Résidence"].unique())
    appt_sel = st.selectbox("🚪 Appartement", df[df["Résidence"] == res_sel]["Appartement"])
    
    st.divider()
    source = st.radio("📸 Source :", ["Photo Directe", "Galerie / Fichier"], horizontal=True)
    photo = st.camera_input("SCAN") if source == "Photo Directe" else st.file_uploader("IMPORT", type=["jpg", "png", "jpeg"])
    
    if photo and st.button("🚀 LANCER L'ANALYSE TECHNIQUE"):
        try:
            # AUTO-DÉTECTION DU MODÈLE DISPONIBLE (Pour éviter l'erreur 404)
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "flash" in m), available_models[0])
            
            model = genai.GenerativeModel(target_model)
            img = Image.open(photo)
            
            with st.spinner(f"Analyse en cours via {target_model}..."):
                prompt = "Expert bâtiment. Analyse la photo. Dis si c'est la charge du Bailleur (Gironde Habitat), du Locataire ou d'un Prestataire. Réponse courte."
                response = model.generate_content([prompt, img])
                
                st.markdown("### 📋 RAPPORT")
                st.info(response.text)
                
                st.divider()
                nom_loc = df[df["Appartement"] == appt_sel]["Nom"].iloc[0]
                lettre = f"OBJET : Constat technique - {res_sel} / {appt_sel}\nLOCATAIRE : {nom_loc}\nDATE : {datetime.now().strftime('%d/%m/%Y')}\n\n{response.text}"
                st.text_area("Copier pour plateforme :", lettre, height=150)
                
            st.success("Analyse terminée.")
        except Exception as e:
            st.error(f"L'analyse a échoué : {e}")
    st.markdown('</div>', unsafe_allow_html=True)
