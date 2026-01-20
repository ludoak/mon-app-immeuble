import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("TEST FINAL GH")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("ERREUR : Clé absente des Secrets !")
else:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    img = st.camera_input("Photo")
    if img and st.button("GO"):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(["C'est quoi ?", Image.open(img)])
            st.write(res.text)
        except Exception as e:
            st.error(f"L'IA dit non : {e}")