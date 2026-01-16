import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Clé manquante")

# --- 2. INTERFACE SIMPLIFIÉE POUR TEST ---
st.subheader("🛠️ Test Diagnostic Technique")

source_photo = st.file_uploader("📸 Photo", type=["jpg", "jpeg", "png"])
notes = st.text_input("🗒️ Notes")
lancer = st.button("🔍 LANCER L'ANALYSE")

if lancer:
    if source_photo or notes:
        with st.spinner("Analyse..."):
            try:
                # Utilisation du nom standard que toutes les versions reconnaissent
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = "Tu es inspecteur technique. Analyse ce problème et dis si c'est au locataire. Phrase obligatoire : Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire."
                
                if source_photo:
                    img = Image.open(source_photo)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.write("### Résultat :")
                st.write(response.text)
            except Exception as e:
                st.error(f"Erreur : {e}")