import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    # ON FORCE LA CONFIGURATION SUR LA VERSION STABLE
    genai.configure(api_key=api_key, transport='rest')
else:
    st.error("Clé API manquante dans les Secrets Streamlit")

st.subheader("🛠️ Diagnostic Technique Gironde Habitat")

foto = st.file_uploader("📸 Photo (Caméra ou Galerie)", type=["jpg", "png", "jpeg"])
note = st.text_input("🗒️ Observation")

if st.button("🔍 LANCER L'ANALYSE"):
    if foto or note:
        with st.spinner("Analyse en cours..."):
            try:
                # Utilisation du modèle sans préfixe
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""Tu es expert technique GH. Analyse ce problème : {note}. 
                Si c'est un défaut d'entretien, précise que c'est à la charge du locataire.
                Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'"""
                
                if foto:
                    img = Image.open(foto)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.success("### Diagnostic terminé :")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.info("🔄 Si l'erreur persiste, créez une NOUVELLE clé sur Google AI Studio en choisissant 'Create API key in NEW project'.")