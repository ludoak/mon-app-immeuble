import streamlit as st
import requests

st.set_page_config(page_title="ImmoCheck GH", page_icon="🏢")

api_key = st.secrets.get("GEMINI_API_KEY")

def diagnostic_ultime(note, key):
    # On tente l'URL la plus simple possible chez Google
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}"
    
    payload = {
        "contents": [{"parts": [{"text": f"Expert technique GH. Analyse : {note}. Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire.'"}]}]
    }
    
    return requests.post(url, json=payload)

st.title("🏢 Diagnostic GH - Mode Survie")

note = st.text_input("Description du problème :")

if st.button("LANCER"):
    res = diagnostic_ultime(note, api_key)
    if res.status_code == 200:
        st.success("ENFIN !")
        st.write(res.json()['candidates'][0]['content']['parts'][0]['text'])
    else:
        st.error(f"Erreur {res.status_code}")
        st.json(res.json())