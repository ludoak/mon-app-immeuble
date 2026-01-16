import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    # On configure l'IA
    genai.configure(api_key=api_key)
else:
    st.error("Clé API manquante dans les Secrets")

# --- 2. INTERFACE ---
st.subheader("🛠️ Diagnostic Technique GH")

source_photo = st.file_uploader("📸 Photo (Caméra ou Galerie)", type=["jpg", "jpeg", "png"])
notes = st.text_input("🗒️ Notes (ex: moisissures, joint...)")
lancer = st.button("🔍 ANALYSER", type="primary")

if lancer:
    if source_photo or notes:
        with st.spinner("Analyse en cours..."):
            try:
                # FORCE LE MODÈLE SANS PRÉFIXE BUGGÉ
                # On utilise une méthode plus directe pour éviter l'erreur 404
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                
                prompt = f"""Tu es inspecteur technique pour Gironde Habitat. 
                Analyse : {notes}. 
                RÈGLE : Si c'est un défaut d'entretien (moisissures, joints sales, vitres), c'est au locataire.
                PHRASE OBLIGATOIRE : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'
                Rédige un message court et pro."""
                
                if source_photo:
                    img = Image.open(source_photo)
                    # Envoi direct pour éviter les erreurs de version
                    response = model.generate_content([prompt, img])
                else:
                    response = model.generate_content(prompt)
                
                st.success("### Résultat du diagnostic :")
                st.write(response.text)
                
            except Exception as e:
                # SI GEMINI 1.5 FLASH ÉCHOUE ENCORE, ON FORCE LE VIEUX GEMINI PRO
                try:
                    model_secours = genai.GenerativeModel('gemini-pro')
                    response = model_secours.generate_content(prompt)
                    st.warning("Note : Analyse effectuée par le mode de secours.")
                    st.write(response.text)
                except Exception as e2:
                    st.error(f"Erreur persistante : {e2}")
                    st.info("💡 Action : Supprimez l'application sur Streamlit Cloud et recréez-la, c'est parfois la seule façon de vider le cache Google.")