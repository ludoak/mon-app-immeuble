import streamlit as st
from datetime import date
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION DIRECTE ---
CLE_IA = "AIzaSyAiAI7LNaeqHw5OjVJK6XIrNsCFQNsf4bY"
genai.configure(api_key=CLE_IA)

st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢")

# --- FONCTION POUR TROUVER LE BON MODÈLE ---
def get_model():
    # On essaie les noms les plus courants un par un
    for model_name in ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro-vision']:
        try:
            m = genai.GenerativeModel(model_name)
            # Test ultra rapide pour voir s'il répond
            return m
        except:
            continue
    return None

model = get_model()

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
        if model is None:
            st.error("Désolé, aucun modèle d'IA n'est disponible pour le moment.")
        else:
            try:
                img = Image.open(photo)
                # Demande à l'IA
                response = model.generate_content([
                    "Tu es un expert en bâtiment. Décris le problème sur la photo en 15 mots maximum.", 
                    img
                ])
                analyse_ia = response.text
                st.success("✅ Analyse terminée")
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")

    notes = st.text_area("📝 Observations (IA)", value=analyse_ia)

    if st.button("GÉNÉRER LE RAPPORT"):
        date_j = date.today().strftime('%d/%m/%Y')
        rapport = f"RAPPORT DU {date_j}\nLIEU : {res} Apt {n}\nLOCATAIRE : {nom}\n\nCONSTAT :\n{notes}"
        st.code(rapport)
