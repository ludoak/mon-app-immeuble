import streamlit as st
import requests

st.set_page_config(page_title="ImmoCheck GH", page_icon="🏢")

# 1. Récupération de la clé
api_key = st.secrets.get("GEMINI_API_KEY")

def test_connexion_directe(key):
    # On utilise l'URL v1 stable et le modèle gemini-1.5-flash
    # C'est l'URL officielle de 2026
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}"
    
    payload = {
        "contents": [{"parts": [{"text": "Réponds 'OK' si tu reçois ce message."}]}]
    }
    
    response = requests.post(url, json=payload)
    return response

st.title("🏢 Système de Secours GH")

if not api_key:
    st.error("Clé API manquante dans les Secrets.")
else:
    st.success("Clé API détectée.")

    note = st.text_input("Décrivez le problème technique :")

    if st.button("LANCER L'ANALYSE"):
        with st.spinner("Tentative de connexion directe..."):
            res = test_connexion_directe(api_key)
            data = res.json()
            
            if res.status_code == 200:
                st.success("CONNEXION RÉUSSIE !")
                # Si la connexion marche, on demande le diagnostic
                url_diag = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                prompt = f"Tu es expert technique GH. Analyse : {note}. Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'"
                payload_diag = {"contents": [{"parts": [{"text": prompt}]}]}
                res_diag = requests.post(url_diag, json=payload_diag)
                st.write(res_diag.json()['candidates'][0]['content']['parts'][0]['text'])
            else:
                st.error(f"Erreur {res.status_code}")
                st.json(data) # Ceci va nous dire EXACTEMENT ce qui ne va pas