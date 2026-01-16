import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH", page_icon="🏢")

# Récupération de la clé
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    # Initialisation propre de l'API
    genai.configure(api_key=api_key)
else:
    st.error("Clé API manquante dans les Secrets Streamlit")

st.subheader("🛠️ Diagnostic Technique Gironde Habitat")

# Interface
foto = st.file_uploader("📸 Photo (Caméra ou Galerie)", type=["jpg", "png", "jpeg"])
note = st.text_input("🗒️ Observation (ex: joint moisi, vitre cassée)")

if st.button("🔍 LANCER L'ANALYSE"):
    if foto or note:
        with st.spinner("Analyse en cours..."):
            try:
                # CHANGEMENT ICI : On utilise une configuration explicite pour éviter le 404
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                
                prompt = f"""Tu es expert technique GH. Analyse ce problème : {note}. 
                Si c'est un défaut d'entretien, précise que c'est à la charge du locataire.
                Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'"""
                
                if foto:
                    img = Image.open(foto)
                    # On envoie sans spécifier de version beta
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.success("### Diagnostic terminé :")
                st.write(response.text)
                
            except Exception as e:
                # Si le 1.5 Flash bug encore, on tente le modèle Pro qui est le plus stable au monde
                try:
                    model_secours = genai.GenerativeModel('gemini-1.0-pro')
                    response = model_secours.generate_content(prompt if not foto else f"{prompt} (Note: Image ignorée en mode secours)")
                    st.warning("Analyse effectuée par le mode de secours (Texte uniquement).")
                    st.write(response.text)
                except Exception as e2:
                    st.error(f"Erreur persistante : {e2}")
                    st.info("💡 Conseil : Si vous voyez encore '404', cela signifie que votre clé API n'a pas les droits pour Gemini 1.5. Vérifiez sur Google AI Studio que vous avez bien activé le modèle 'Flash'.")
    else:
        st.warning("Veuillez fournir une photo ou un texte.")