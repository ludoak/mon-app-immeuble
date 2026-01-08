import streamlit as st
from datetime import date
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
CLE_IA = "AIzaSyAiAI7LNaeqHw5OjVJK6XIrNsCFQNsf4bY"
genai.configure(api_key=CLE_IA)
# Utilisation du nom le plus simple
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢")
st.title("🏢 Rapport d'Intervention")

with st.container(border=True):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    n = st.text_input("N° Appartement")
    nom = st.text_input("👤 Nom du Locataire")
    
    st.divider()
    st.subheader("📸 Diagnostic Photo")
    photo = st.camera_input("Prendre une photo")
    
    analyse_ia = ""
    if photo:
        try:
            img = Image.open(photo)
            # Appel direct
            response = model.generate_content(["Décris le problème sur la photo en 15 mots max.", img])
            analyse_ia = response.text
            st.success("✅ Analyse terminée")
        except Exception as e:
            st.error(f"Erreur d'analyse : {e}")

    notes = st.text_area("📝 Observations (IA)", value=analyse_ia)

    if st.button("GÉNÉRER LE RAPPORT"):
        date_j = date.today().strftime('%d/%m/%Y')
        rapport = f"RAPPORT DU {date_j}\nLIEU : {res} Apt {n}\nLOCATAIRE : {nom}\n\nCONSTAT :\n{notes}"
        st.code(rapport)
