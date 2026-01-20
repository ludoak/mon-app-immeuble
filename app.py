import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Diag GH")
st.title("🏢 Diagnostic GH - Relance")

# Vérification de la clé
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ LA CLÉ N'EST PAS DANS LES SECRETS STREAMLIT")
else:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    img_file = st.camera_input("Prendre une photo")
    
    if img_file:
        if st.button("🔍 ANALYSER"):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(img_file)
                with st.spinner("Analyse..."):
                    response = model.generate_content(["Analyse cette photo de désordre immobilier.", img])
                    st.success("Ça fonctionne !")
                    st.write(response.text)
            except Exception as e:
                st.error(f"L'API refuse la clé : {e}")