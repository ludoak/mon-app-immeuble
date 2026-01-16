import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Test IA GH")

# Configuration de la clé
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

st.title("🚀 Test Final Diagnostic")

foto = st.file_uploader("Prendre une photo", type=["jpg", "png", "jpeg"])
note = st.text_input("Observation")

if st.button("LANCER L'ANALYSE"):
    try:
        # On force l'appel au modèle sans fioritures
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if foto:
            img = Image.open(foto)
            # Test avec image + texte
            res = model.generate_content([f"Analyse ce problème technique : {note}", img])
        else:
            # Test avec texte seul
            res = model.generate_content(f"Dis si ce problème est à la charge du locataire : {note}")
            
        st.success("L'IA a répondu !")
        st.write(res.text)
        
    except Exception as e:
        st.error(f"Erreur technique : {e}")