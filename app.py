import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Diag GH Force")
st.title("🏢 Diagnostic GH")

# Connexion directe
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ Erreur : Copie ta clé dans les Secrets Streamlit !")
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    img_file = st.camera_input("Prendre une photo")
    
    if img_file:
        if st.button("🔍 ANALYSER"):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(img_file)
                with st.spinner("Analyse..."):
                    response = model.generate_content(["Expert bâtiment. Analyse la photo et dis si c'est la charge du bailleur ou du locataire.", img])
                    st.success("Réussi !")
                    st.write(response.text)
            except Exception as e:
                st.error(f"L'API rejette la clé : {e}")