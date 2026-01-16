import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    # On configure l'API en forçant la version 1
    genai.configure(api_key=api_key)
else:
    st.error("Clé API manquante dans les Secrets")

st.subheader("🛠️ Diagnostic Technique Gironde Habitat")

foto = st.file_uploader("📸 Photo (Caméra ou Galerie)", type=["jpg", "png", "jpeg"])
note = st.text_input("🗒️ Observation")

if st.button("🔍 LANCER L'ANALYSE"):
    if foto or note:
        with st.spinner("Analyse en cours..."):
            try:
                # VERSION FORCÉE SANS "BETA"
                # On utilise la méthode de génération avec un nom de modèle strict
                model = genai.GenerativeModel(
                    model_name='models/gemini-1.5-flash',
                )
                
                prompt = f"""Tu es expert technique GH. Analyse : {note}. 
                Si c'est un défaut d'entretien, précise que c'est à la charge du locataire.
                Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'"""
                
                if foto:
                    img = Image.open(foto)
                    # On demande à l'IA d'analyser l'image
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.success("### Diagnostic terminé :")
                st.write(response.text)
                
            except Exception as e:
                # Si le 404 persiste, on affiche une explication simple
                st.error("L'application utilise encore une ancienne version de connexion.")
                st.info("🔄 ACTION : Allez dans 'Manage App' sur Streamlit, cliquez sur les 3 points et faites 'Reboot App'. C'est le seul moyen de forcer le passage à la version stable.")
    else:
        st.warning("Veuillez fournir une photo ou un texte.")