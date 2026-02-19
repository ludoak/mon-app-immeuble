import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import urllib.parse
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Expert", layout="wide")

# Connexion Google Sheets (Mode Sécurisé)
try:
    conn = st.connection("gsheets", type="streamlit_gsheets.connection.GSheetsConnection")
    df = conn.read()
except Exception as e:
    st.warning(f"Impossible de charger les locataires (erreur sheets). Utilisation mode manuel. Erreur: {e}")
    df = pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

# Configuration Gemini
try:
    if "CLE_TEST" in st.secrets:
        genai.configure(api_key=st.secrets["CLE_TEST"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.error("Clé Gemini absente des secrets.")
        st.stop()
except Exception as e:
    st.error(f"Erreur initialisation Gemini : {e}")
    st.stop()

# --- 2. INTERFACE ---
st.title("GH EXPERT PRO")

# Création des onglets
tab1, tab2 = st.tabs(["📟 DIAGNOSTIC", "📋 GUIDE"])

# --- ONGLET DIAGNOSTIC ---
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Locataire")
        # Si le fichier est vide, on permet la saisie manuelle
        if df.empty:
            res = st.text_input("Résidence")
            app = st.text_input("Appartement")
            nom_loc = "Inconnu"
        else:
            res = st.selectbox("Résidence", df["Résidence"].unique())
            filtered = df[df["Résidence"] == res]
            app = st.selectbox("Appartement", filtered["Appartement"].unique())
            nom_loc = filtered[filtered["Appartement"] == app]["Nom"].iloc[0]
        
        st.write(f"**Occupant :** {nom_loc}")
        dest_mail = st.text_input("Email", "ludoak33@gmail.com")

    with col2:
        st.subheader("Photo")
        img = st.camera_input("Prendre la photo")
        
        if img and st.button("ANALYSER"):
            with st.spinner("Analyse..."):
                try:
                    prompt = "Expert bailleur social. Analyse cette photo. Qui paie : Locataire, Bailleur ou Prestataire ? Sois bref."
                    image = Image.open(img)
                    response = model.generate_content([prompt, image])
                    st.session_state['verdict'] = response.text
                except Exception as e:
                    st.error(f"Erreur IA : {e}")

        if 'verdict' in st.session_state:
            st.success(st.session_state['verdict'])
            # Bouton Mail simple
            sujet = f"Constat {app}"
            body = f"Locataire : {nom_loc}\nAnalyse : {st.session_state['verdict']}"
            link = f"mailto:{dest_mail}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(body)}"
            st.markdown(f"[📧 Envoyer le mail]({link})")

# --- ONGLET GUIDE ---
with tab2:
    st.subheader("Tableau des responsabilités")
    st.markdown("- **Plomberie (joints)** : LOCATAIRE")
    st.markdown("- **Chaudière** : PRESTATAIRE")
    st.markdown("- **Gros œuvres** : BAILLEUR")
