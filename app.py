import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("Clé API manquante dans les Secrets")

st.subheader("🛠️ Diagnostic Technique GH (Gemini 3)")

source_photo = st.file_uploader("📸 Photo", type=["jpg", "jpeg", "png"])
notes = st.text_input("🗒️ Notes (ex: moisissures, joint...)")
lancer = st.button("🔍 ANALYSER", type="primary")

if lancer:
    if source_photo or notes:
        with st.spinner("Analyse par Gemini 3 en cours..."):
            try:
                # MISE À JOUR DU NOM DU MODÈLE SELON TA VIDÉO
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                prompt = f"""Tu es l'inspecteur expert technique de Gironde Habitat. 
                Analyse les notes : '{notes}' et la photo.
                
                RÈGLES DE CHARGE LOCATIVE :
                - MOISISSURES : Si visibles sur joints ou parois = Défaut d'entretien.
                - JOINTS : Silicone noirci ou fuyant = Entretien locataire.
                
                Si c'est à la charge du locataire, ajoute obligatoirement : 
                'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire (Décret n°87-712).'
                
                Réponds de manière professionnelle et concise."""
                
                if source_photo:
                    img = Image.open(source_photo)
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.success("### Rapport d'analyse :")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Erreur avec Gemini 3 : {e}")
                st.info("Note : Si l'erreur persiste, essayez avec le nom 'gemini-3-flash' sans le '-preview'.")
    else:
        st.warning("⚠️ Ajoutez une photo ou une note.")