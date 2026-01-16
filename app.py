import streamlit as st
import requests
import base64
from PIL import Image
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

def analyser_image_direct(image_file, texte_notes, api_key):
    # On force l'URL stable v1 (et non v1beta)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Préparation de l'image
    img = Image.open(image_file)
    # Redimensionner si trop gros pour l'envoi
    img.thumbnail((1024, 1024))
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Construction de la demande manuelle
    payload = {
        "contents": [{
            "parts": [
                {"text": f"Tu es expert technique GH. Analyse ce problème : {texte_notes}. Si c'est un défaut d'entretien, précise que c'est à la charge du locataire. Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'"},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_str}}
            ]
        }]
    }

    response = requests.post(url, json=payload)
    return response.json()

st.subheader("🛠️ Diagnostic Technique Gironde Habitat (Force v1)")

foto = st.file_uploader("📸 Photo", type=["jpg", "png", "jpeg"])
note = st.text_input("🗒️ Observation")

if st.button("🔍 LANCER L'ANALYSE"):
    if api_key and foto:
        with st.spinner("Analyse forcée en cours..."):
            try:
                resultat = analyser_image_direct(foto, note, api_key)
                # On affiche la réponse
                if "candidates" in resultat:
                    texte_ia = resultat["candidates"][0]["content"]["parts"][0]["text"]
                    st.success("### Diagnostic terminé :")
                    st.write(texte_ia)
                else:
                    st.error(f"Erreur Google : {resultat}")
            except Exception as e:
                st.error(f"Erreur technique : {e}")
    elif not api_key:
        st.error("Clé API manquante dans les Secrets.")
    else:
        st.warning("Veuillez charger une photo.")