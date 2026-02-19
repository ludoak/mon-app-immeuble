import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuration de la page
st.set_page_config(page_title="GH Expert Pro", layout="wide")

# --- 1. CONNEXION AUX DONNÉES ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read()
except Exception as e:
    st.warning("Connexion Google Sheets échouée.")
    df = pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

# --- 2. CONNEXION IA ---
if "CLE_TEST" not in st.secrets:
    st.error("Clé API Gemini non trouvée dans les secrets Streamlit.")
    st.stop()
else:
    genai.configure(api_key=st.secrets["CLE_TEST"])
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. INTERFACE ---
st.markdown("<h1 style='text-align:center; color:#ff00ff;'>GH EXPERT PRO</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📟 DIAGNOSTIC", "📋 GUIDE", "⚙️ GESTION"])

# --- ONGLET DIAGNOSTIC ---
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Locataire")
        if df.empty:
            res = st.text_input("Résidence")
            app = st.text_input("Appartement")
            nom = "Inconnu"
        else:
            res = st.selectbox("Résidence", df["Résidence"].unique())
            filtre = df[df["Résidence"] == res]
            app = st.selectbox("Appartement", filtre["Appartement"].unique())
            nom = filtre[filtre["Appartement"] == app]["Nom"].iloc[0]
        
        st.info(f"Occupant : **{nom}**")
        email = st.text_input("Email entreprise", "ludoak33@gmail.com")

    with col2:
        st.subheader("📸 Constat")
        img = st.camera_input("Prendre la photo")
        
        if img and st.button("🚀 ANALYSER"):
            with st.spinner("Diagnostic en cours..."):
                try:
                    prompt = "Expert bailleur social. Analyse cette photo. Qui paie : LOCATAIRE, BAILLEUR ou PRESTATAIRE ?"
                    image = Image.open(img)
                    reponse = model.generate_content([prompt, image])
                    st.session_state['resultat'] = reponse.text
                except Exception as e:
                    st.error(f"Erreur : {e}")

        if 'resultat' in st.session_state:
            st.success(st.session_state['resultat'])
            sujet = f"Constat {app} - {res}"
            corps = f"Locataire : {nom}\n\nAnalyse :\n{st.session_state['resultat']}"
            lien = f"mailto:{email}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"
            st.markdown(f"<a href='{lien}' style='background-color:#0078d4; color:white; padding:15px; border-radius:10px; text-decoration:none; display:block; text-align:center;'>📧 ENVOYER LE MAIL</a>", unsafe_allow_html=True)

# --- ONGLET GUIDE ---
with tab2:
    st.subheader("🔍 Qui paie quoi ?")
    st.markdown("- **Locataire** : Joints, ampoules, propreté")
    st.markdown("- **Prestataire** : Chaudière, VMC, ascenseur")
    st.markdown("- **Bailleur (GH)** : Gros œuvre, fuites majeures")

# --- ONGLET GESTION ---
with tab3:
    st.subheader("Ajouter un locataire")
    with st.form("ajout"):
        r = st.text_input("Résidence")
        b = st.text_input("Bâtiment")
        a = st.text_input("Appartement")
        n = st.text_input("Nom")
        if st.form_submit_button("Sauvegarder"):
            if r and a and n:
                nouveau = pd.DataFrame([{"Résidence": r, "Bâtiment": b, "Appartement": a, "Nom": n}])
                try:
                    base = conn.read()
                    total = pd.concat([base, nouveau], ignore_index=True)
                    conn.update(data=total)
                    st.success("Bien ajouté !")
                except:
                    st.error("Erreur de sauvegarde")
