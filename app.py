import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image

# Configuration
st.set_page_config(page_title="ImmoCheck IA", page_icon="🏢", layout="wide")

# --- CONNEXIONS ---
# 1. Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    st.error("Erreur de connexion Google Sheets. Vérifiez vos Secrets.")

# 2. Gemini IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception:
    st.warning("IA non configurée. Vérifiez GEMINI_API_KEY dans les Secrets.")

# --- FONCTIONS ---
def charger_donnees():
    try:
        return conn.read(worksheet="Locataires", ttl=0)
    except:
        return pd.DataFrame(columns=["Logement", "Nom"])

def sauvegarder_locataire(logement, nom):
    df = charger_donnees()
    if logement in df['Logement'].values:
        df.loc[df['Logement'] == logement, 'Nom'] = nom
    else:
        new_row = pd.DataFrame({"Logement": [logement], "Nom": [nom]})
        df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

# --- INTERFACE ---
st.title("🏢 Rapport avec Analyse IA")

# Sidebar : Gestion Locataires
with st.sidebar:
    st.header("👥 Base Locataires")
    res_a = st.selectbox("Résidence", ["Canterane", "La Dussaude"])
    nom_a = st.text_input("Nom du locataire")
    # Choix appt selon résidence...
    if st.button("Enregistrer Locataire"):
        # Logique de clé logement simplifiée pour l'exemple
        sauvegarder_locataire(f"{res_a} - Manuel", nom_a)
        st.success("Enregistré !")

# Formulaire Principal
df_base = charger_donnees()
with st.form("rapport_ia"):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    nom = st.text_input("👤 Nom du Locataire")
    
    st.divider()
    st.subheader("📸 Analyse des dégâts par IA")
    photo = st.camera_input("Prendre une photo du problème")
    
    analyse_ia = ""
    if photo:
        img = Image.open(photo)
        with st.spinner("L'IA analyse la photo..."):
            response = model.generate_content(["Décris précisément ce problème technique dans un immeuble (fuite, fissure, etc.) en 2 phrases pour un rapport.", img])
            analyse_ia = response.text
            st.info(f"Analyse suggérée : {analyse_ia}")

    notes = st.text_area("Observations complémentaires", value=analyse_ia)

    if st.form_submit_button("GÉNÉRER LE RAPPORT"):
        st.write(f"Rapport prêt pour {nom} à {res}")
