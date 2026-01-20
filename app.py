import streamlit as st
import google.generativeai as genai
from PIL import Image

# Config pure et dure
st.set_page_config(page_title="SOS Diagnostic")
st.title("🏢 Diagnostic GH : Relance Force")

# On vérifie la clé
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ La clé n'est pas dans les Secrets Streamlit !")
else:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    # Interface
    img_file = st.camera_input("Prendre une photo")
    
    if img_file:
        if st.button("🔍 ANALYSER MAINTENANT"):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(img_file)
                
                with st.spinner("L'IA bosse..."):
                    response = model.generate_content(["Expert bâtiment. Analyse cette photo : problème et charge (GH ou Locataire) ?", img])
                    st.success("Ça marche !")
                    st.write(response.text)
            except Exception as e:
                st.error(f"Erreur technique : {e}")