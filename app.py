import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("🚀 Diagnostic GH - Version Force")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Clé manquante dans les Secrets !")
else:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
        # On cherche un modèle valide automatiquement
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = available_models[0] if available_models else None
        
        if not target_model:
            st.error("Aucun modèle compatible trouvé sur cette clé.")
        else:
            st.caption(f"Modèle activé : {target_model}")
            
            img_file = st.camera_input("Prendre une photo")
            if img_file and st.button("LANCER L'ANALYSE"):
                try:
                    model = genai.GenerativeModel(target_model)
                    img = Image.open(img_file)
                    with st.spinner("Analyse technique..."):
                        response = model.generate_content(["Analyse ce désordre immobilier.", img])
                        st.success("Analyse réussie !")
                        st.write(response.text)
                except Exception as e:
                    st.error(f"Erreur d'analyse : {e}")

    except Exception as e:
        st.error(f"Erreur de connexion : {e}")