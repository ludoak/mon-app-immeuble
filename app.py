import streamlit as st
from datetime import date
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
CLE_IA = "AIzaSyAiAI7LNaeqHw5OjVJK6XIrNsCFQNsf4bY"
genai.configure(api_key=CLE_IA)

st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢")
st.title("🏢 Rapport d'Intervention")

# --- RECHERCHE AUTOMATIQUE DU MODÈLE ---
@st.cache_resource
def load_available_model():
    try:
        # On cherche dans ta liste quel modèle est autorisé à générer du contenu
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name or 'pro' in m.name:
                    return genai.GenerativeModel(m.name)
        return None
    except:
        return None

model = load_available_model()

with st.container(border=True):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    n = st.text_input("N° Appartement")
    nom = st.text_input("👤 Nom du Locataire")
    
    st.divider()
    st.subheader("📸 Diagnostic Photo")
    photo = st.camera_input("Prendre une photo")
    
    analyse_ia = ""
    if photo:
        if model is None:
            st.error("L'IA n'est pas accessible avec cette clé. Vérifiez votre compte Google AI Studio.")
        else:
            try:
                img = Image.open(photo)
                # On utilise le modèle trouvé automatiquement
                response = model.generate_content(["Décris le problème sur la photo en 15 mots max.", img])
                analyse_ia = response.text
                st.success(f"✅ Analyse réussie avec {model.model_name}")
            except Exception as e:
                st.error(f"Erreur : {e}")

    notes = st.text_area("📝 Observations (IA)", value=analyse_ia)

    if st.button("GÉNÉRER LE RAPPORT"):
        date_j = date.today().strftime('%d/%m/%Y')
        rapport = f"RAPPORT DU {date_j}\nLIEU : {res} Apt {n}\nLOCATAIRE : {nom}\n\nCONSTAT :\n{notes}"
        st.code(rapport)
