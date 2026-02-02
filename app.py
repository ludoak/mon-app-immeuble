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
        margin-bottom: 20px;
        box-shadow: 0 0 10px rgba(255, 0, 255, 0.2);
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

st.markdown("<h1 class='neon-title'>GIRONDE HABITAT - EXPERT</h1>", unsafe_allow_html=True)

# --- 2. GESTION DE LA CLÉ API ---
# On essaie d'abord les secrets, sinon on affiche la zone de saisie
api_key = st.secrets.get("CLE_TEST", "")

if not api_key:
    st.info("💡 Connexion aux secrets en attente...")
    api_key = st.text_input("🔑 Colle ta clé AIzaSy... ici pour activer l'IA :", type="password")
else:
    st.success("✅ Système connecté via Secrets")

# --- 3. CHARGEMENT DES DONNÉES ---
DB_FILE = "base_locataires_gh.csv"
def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
    return pd.DataFrame({"Résidence": ["Canterane"], "Appartement": ["10"], "Nom": ["Locataire Test"]})

if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# --- 4. INTERFACE PRINCIPALE ---
if api_key:
    genai.configure(api_key=api_key)
    df = st.session_state.df_locataires
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("👥 RÉSIDENTS")
        st.dataframe(df, use_container_width=True)

    with col2:
        st.markdown('<div class="holo-card">', unsafe_allow_html=True)
        res_sel = st.selectbox("Résidence", df["Résidence"].unique())
        appt_sel = st.selectbox("Appartement", df[df["Résidence"] == res_sel]["Appartement"])
        
        source = st.radio("Méthode d'acquisition :", ["Scanner Photo", "Galerie / Fichier"], horizontal=True)
        
        photo = None
        if source == "Scanner Photo":
            photo = st.camera_input("SCAN EN DIRECT")
        else:
            photo = st.file_uploader("IMPORTER UNE IMAGE", type=["jpg", "png", "jpeg"])
        
        if photo and st.button("🚀 LANCER L'ANALYSE TECHNIQUE"):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(photo)
                with st.spinner("Analyse holographique en cours..."):
                    prompt = "Expert bâtiment. Analyse la photo. Charge : BAILLEUR (GH), LOCATAIRE ou PRESTATAIRE ? Justifie en 2 lignes."
                    response = model.generate_content([prompt, img])
                    
                    st.markdown(f"### RÉSULTAT :")
                    st.info(response.text)
                    
                    # --- COURRIER AUTOMATIQUE ---
                    st.divider()
                    nom_loc = df[df["Appartement"] == appt_sel]["Nom"].iloc[0]
                    date_str = datetime.now().strftime("%d/%m/%Y")
                    lettre = f"OBJET : Signalement {res_sel} / Appt {appt_sel}\nDATE : {date_str}\n\nMadame, Monsieur,\n\nConstat : {response.text}"
                    st.text_area("Courrier prêt à copier :", lettre, height=150)
            except Exception as e:
                st.error(f"L'analyse a échoué : {e}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("🔒 En attente de la clé API pour activer les capteurs de diagnostic.")
