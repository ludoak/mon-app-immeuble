import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide", page_icon="🏢")

# --- 2. BASE DE DONNÉES ---
DB_FILE = "base_locataires_gh.csv"
def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
    return pd.DataFrame({
        "Résidence": ["Canterane", "La Dussaude"], 
        "Appartement": ["10", "95"], 
        "Nom": ["lolo", "zezette"]
    })

if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# --- 3. CONNEXION IA (MODE AUTO-DÉTECTION) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # On cherche le modèle qui fonctionne sur ton compte
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target_model = models[0] if models else "models/gemini-1.5-flash"
except:
    st.error("Erreur de configuration API")

# --- 4. INTERFACE ---
st.title("🏢 Assistant GH - Expertise")

tab1, tab2 = st.tabs(["📸 Diagnostic Terrain", "👥 Liste Locataires"])

with tab1:
    df = st.session_state.df_locataires
    
    col1, col2 = st.columns(2)
    with col1:
        res_sel = st.selectbox("📍 Résidence", sorted(df["Résidence"].unique().astype(str)))
    with col2:
        df_res = df[df["Résidence"] == res_sel]
        appt_sel = st.selectbox("🚪 Appartement", sorted(df_res["Appartement"].unique().astype(str)))
    
    st.divider()
    
    # --- PHOTOS ---
    st.subheader("📷 Constat visuel")
    cam = st.camera_input("Prendre une photo")
    gal = st.file_uploader("Ou importer un fichier", type=["jpg", "png", "jpeg"])
    photo = cam if cam else gal

    if photo:
        if st.button("🔍 LANCER L'ANALYSE TECHNIQUE", type="primary", use_container_width=True):
            with st.spinner("L'IA analyse le désordre..."):
                try:
                    model = genai.GenerativeModel(target_model)
                    img = Image.open(photo)
                    
                    prompt = """Tu es un expert en maintenance immobilière. 
                    Analyse la photo. Décris le problème technique.
                    Dis si c'est une charge pour le BAILLEUR (Gironde Habitat) ou le LOCATAIRE.
                    Termine par CODE:GH ou CODE:LOC."""
                    
                    response = model.generate_content([prompt, img])
                    
                    st.divider()
                    st.subheader("📋 Rapport d'expertise")
                    st.write(response.text)
                    
                    # Bouton pour copier le texte
                    st.info("Tu peux copier le texte ci-dessus pour ton compte-rendu.")
                    
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")

with tab2:
    st.subheader("👥 Gestion des Locataires")
    st.dataframe(st.session_state.df_locataires, use_container_width=True)
    
    with st.expander("➕ Ajouter un nouveau logement"):
        with st.form("add_loc"):
            r = st.text_input("Résidence")
            a = st.text_input("Appartement")
            n = st.text_input("Nom du locataire")
            if st.form_submit_button("Enregistrer"):
                new_row = pd.DataFrame({"Résidence": [r], "Appartement": [a], "Nom": [n]})
                st.session_state.df_locataires = pd.concat([st.session_state.df_locataires, new_row], ignore_index=True)
                st.session_state.df_locataires.to_csv(DB_FILE, index=False)
                st.rerun()