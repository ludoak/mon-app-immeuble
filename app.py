import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck Rapide", page_icon="🏢")

# --- CONNEXIONS ---
# Lecture seule du tableau (Plus d'erreur 400)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], ttl=0)
except Exception as e:
    st.error(f"Erreur Tableau : {e}")
    df_base = pd.DataFrame(columns=["Logement", "Nom"])

# IA Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("IA non connectée (Clé manquante)")

# --- INTERFACE ---
st.title("🏢 Rapport d'Intervention")

with st.form("rapport"):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    n = st.text_input("N° Appartement (ex: A102 ou 45)")
    
    # Recherche du nom dans le tableau
    id_recherche = f"{res} - {n}" # Format simplifié pour le test
    nom_locataire = ""
    if not df_base.empty:
        # On cherche si le numéro d'appt est dans la colonne 'Logement'
        match = df_base[df_base['Logement'].astype(str).str.contains(n, na=False)]
        if not match.empty:
            nom_locataire = match.iloc[0]['Nom']

    nom = st.text_input("👤 Locataire", value=nom_locataire)
    
    st.divider()
    photo = st.camera_input("📸 Photo du problème")
    
    analyse = ""
    if photo:
        img = Image.open(photo)
        try:
            response = model.generate_content(["Décris ce problème technique en 15 mots max.", img])
            analyse = response.text
        except:
            analyse = "Erreur analyse IA"

    obs = st.text_area("📝 Observations", value=analyse)
    
    if st.form_submit_button("GÉNÉRER LE RAPPORT"):
        texte = f"INTERVENTION {date.today().strftime('%d/%m/%Y')}\nLieu : {res} Apt {n}\nLocataire : {nom}\nNote : {obs}"
        st.code(texte)
