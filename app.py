import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="ImmoCheck GH", layout="wide")

# Configuration IA
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Chargement des locataires via le CSV publié
@st.cache_data(ttl=300)
def charger_donnees():
    try:
        url_csv = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = pd.read_csv(url_csv)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Erreur de lecture des données : {e}")
        return pd.DataFrame()

df_base = charger_donnees()

st.title("🛠️ Diagnostic Technique GH")

# Sélection du locataire
if not df_base.empty:
    col1, col2 = st.columns(2)
    with col1:
        residence = st.selectbox("Résidence", df_base['Résidence'].unique())
        df_res = df_base[df_base['Résidence'] == residence]
    with col2:
        df_res['Appartement'] = df_res['Appartement'].astype(str)
        appt = st.selectbox("Appartement", sorted(df_res['Appartement'].unique()))
        nom_loc = df_res[df_res['Appartement'] == appt]['Nom'].iloc[0]
        st.info(f"👤 Locataire : **{nom_loc}**")

st.divider()

# Analyse IA avec Gemini 3
foto = st.file_uploader("📸 Photo du problème", type=["jpg", "png", "jpeg"])
note = st.text_input("🗒️ Précisions (ex: moisissures joints)")

if st.button("🔍 LANCER L'ANALYSE", type="primary"):
    with st.spinner("Analyse en cours..."):
        try:
            model = genai.GenerativeModel('gemini-3-flash-preview')
            prompt = f"Expert GH. Analyse : {note}. Phrase obligatoire : 'Ce remplacement relève de l'entretien courant et des menues réparations, il est donc à la charge exclusive du locataire (Décret n°87-712).'"
            
            if foto:
                img = Image.open(foto)
                res = model.generate_content([prompt, img])
            else:
                res = model.generate_content(prompt)
            
            st.success("### Résultat du diagnostic :")
            st.write(res.text)
        except Exception as e:
            st.error(f"Erreur IA : {e}")