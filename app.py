import streamlit as st
from datetime import date
import google.generativeai as genai
from PIL import Image
import pandas as pd

# --- CONFIGURATION DIRECTE ---
# On met la clé ici pour être SUR que l'IA la voit
CLE_IA = "AIzaSyAiAI7LNaeqHw5OjVJK6XIrNsCFQNsf4bY"
genai.configure(api_key=CLE_IA)
model = genai.GenerativeModel('gemini-pro-vision')
st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢")

st.title("🏢 Rapport d'Intervention")

# Formulaire simple
with st.container(border=True):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    n = st.text_input("N° Appartement")
    nom = st.text_input("👤 Nom du Locataire")
    
    st.divider()
    
    # PARTIE PHOTO
    st.subheader("📸 Diagnostic Photo")
    photo = st.camera_input("Prendre une photo")
    
    analyse_ia = ""
    if photo:
        try:
            img = Image.open(photo)
            # L'IA analyse ici
            response = model.generate_content(["En 15 mots max, décris le problème technique sur cette photo pour un rapport de maintenance.", img])
            analyse_ia = response.text
            st.success("✅ Analyse terminée")
        except Exception as e:
            st.error(f"L'IA a eu un problème : {e}")

    notes = st.text_area("📝 Observations (IA)", value=analyse_ia)

    if st.button("GÉNÉRER LE RAPPORT"):
        date_j = date.today().strftime('%d/%m/%Y')
        rapport = f"RAPPORT DU {date_j}\nLIEU : {res} Apt {n}\nLOCATAIRE : {nom}\n\nCONSTAT :\n{notes}"
        st.code(rapport)


