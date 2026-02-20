import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials

# Configuration de la page
st.set_page_config(page_title="GH Expert Pro", layout="wide")

# --- 1. CONNEXION GOOGLE SHEETS (Méthode Fiable) ---
def load_data():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["connections"]["gsheets"]["credentials"]
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        sh = client.open_by_url(spreadsheet_url)
        worksheet = sh.sheet1
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Connexion Google Sheets échouée (vérifiez le partage) : {e}")
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df = load_data()

# --- 2. CONNEXION IA (Détection automatique du modèle) ---
if "CLE_TEST" not in st.secrets:
    st.error("Clé API Gemini non trouvée dans les secrets.")
    st.stop()
else:
    try:
        genai.configure(api_key=st.secrets["CLE_TEST"])
        
        # On cherche automatiquement un modèle valide
        models_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # On prend le modèle Flash si dispo, sinon le premier de la liste
        model_id = next((m for m in models_list if "flash" in m), models_list[0])
        
        model = genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"Erreur de connexion IA : {e}")
        st.stop()

# --- 3. INTERFACE ---
st.markdown("<h1 style='text-align:center; color:#ff00ff;'>GH EXPERT PRO</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📟 DIAGNOSTIC", "📋 GUIDE", "⚙️ GESTION"])

# --- ONGLET DIAGNOSTIC ---
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Locataire")
        if df.empty:
            res = st.text_input("Résidence")
            app = st.text_input("Appartement")
            nom = "Inconnu"
        else:
            res = st.selectbox("Résidence", df["Résidence"].unique())
            filtre = df[df["Résidence"] == res]
            app = st.selectbox("Appartement", filtre["Appartement"].unique())
            nom = filtre[filtre["Appartement"] == app]["Nom"].iloc[0]
        
        st.info(f"Occupant : **{nom}**")
        email = st.text_input("Email entreprise", "ludoak33@gmail.com")

    with col2:
        st.subheader("📸 Constat")
        img = st.camera_input("Prendre la photo")
        
        if img and st.button("🚀 ANALYSER"):
            with st.spinner("Diagnostic en cours..."):
                try:
                    prompt = "Expert bailleur social. Analyse cette photo. Qui paie : LOCATAIRE, BAILLEUR ou PRESTATAIRE ?"
                    image = Image.open(img)
                    reponse = model.generate_content([prompt, image])
                    st.session_state['resultat'] = reponse.text
                except Exception as e:
                    st.error(f"Erreur : {e}")

        if 'resultat' in st.session_state:
            st.success(st.session_state['resultat'])
            sujet = f"Constat {app} - {res}"
            corps = f"Locataire : {nom}\n\nAnalyse :\n{st.session_state['resultat']}"
            lien = f"mailto:{email}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"
            st.markdown(f"<a href='{lien}' style='background-color:#0078d4; color:white; padding:15px; border-radius:10px; text-decoration:none; display:block; text-align:center;'>📧 ENVOYER LE MAIL</a>", unsafe_allow_html=True)

# --- ONGLET GUIDE ---
with tab2:
    st.subheader("🔍 Qui paie quoi ?")
    st.markdown("- **Locataire** : Joints, ampoules, propreté")
    st.markdown("- **Prestataire** : Chaudière, VMC, ascenseur")
    st.markdown("- **Bailleur (GH)** : Gros œuvre, fuites majeures")

# --- ONGLET GESTION ---
with tab3:
    st.subheader("Ajouter un locataire")
    st.info("Utilisez le Google Sheet directement pour ajouter des lignes, l'application se mettra à jour.")
    st.dataframe(df)
