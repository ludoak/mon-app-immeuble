import streamlit as st
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

def analyser_texte_direct(texte_notes, api_key):
    # Utilisation du modèle PRO qui est le plus compatible au monde
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": f"Tu es expert technique pour Gironde Habitat. Analyse ce problème : {texte_notes}. Si c'est un défaut d'entretien (moisissures, joints sales, calcaire), précise que c'est à la charge du locataire. Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'"}
            ]
        }]
    }

    response = requests.post(url, json=payload)
    return response.json()

st.subheader("🛠️ Diagnostic Technique Gironde Habitat")
st.info("Note : Suite à un blocage technique de Google sur les photos, merci de décrire le problème par écrit ci-dessous.")

note = st.text_input("🗒️ Décrivez le problème (ex: moisissures joints douche)")

if st.button("🔍 LANCER L'ANALYSE"):
    if api_key and note:
        with st.spinner("Analyse en cours..."):
            try:
                resultat = analyser_texte_direct(note, api_key)
                if "candidates" in resultat:
                    texte_ia = resultat["candidates"][0]["content"]["parts"][0]["text"]
                    st.success("### Diagnostic terminé :")
                    st.write(texte_ia)
                else:
                    st.error(f"Erreur technique : {resultat}")
            except Exception as e:
                st.error(f"Erreur : {e}")
    else:
        st.warning("Veuillez saisir une description.")