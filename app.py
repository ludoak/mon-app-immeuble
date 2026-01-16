import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Clé API manquante dans les Secrets")

# --- 2. INTERFACE ---
st.subheader("🛠️ Diagnostic Technique")

source_photo = st.file_uploader("📸 Photo", type=["jpg", "jpeg", "png"])
notes = st.text_input("🗒️ Notes")
lancer = st.button("🔍 ANALYSER", type="primary")

if lancer:
    if source_photo or notes:
        with st.spinner("Analyse en cours..."):
            try:
                # METHODE DE SECOURS : On essaie 'gemini-1.5-flash'
                # Si ça rate, on essaie 'gemini-pro'
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                except:
                    model = genai.GenerativeModel('gemini-pro')
                
                prompt = f"Expert technique. Analyse : {notes}. Dis si c'est au locataire. Phrase : Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire."
                
                if source_photo:
                    img = Image.open(source_photo)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.info(response.text)
            except Exception as e:
                # Si ça affiche encore 404, on affiche une aide précise
                st.error(f"Erreur de modèle : {e}")
                st.warning("Conseil : Allez sur Streamlit Cloud, cliquez sur 'Settings' > 'Delete Cache' puis 'Reboot'.")