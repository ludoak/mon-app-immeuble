import streamlit as st
from datetime import date
import google.generativeai as genai
from PIL import Image
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
CLE_IA = "AIzaSyAiAI7LNaeqHw5OjVJK6XIrNsCFQNsf4bY"
genai.configure(api_key=CLE_IA)

st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢", layout="wide")

# --- CONNEXION TABLEAU ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(worksheet="Locataires", ttl=0)
except:
    df_base = pd.DataFrame(columns=["Logement", "Nom"])

# --- DETECTION IA (Gemini 2.5) ---
@st.cache_resource
def load_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except: return None

model = load_model()

# --- INTERFACE ---
st.title("🏢 Rapport d'Intervention Pro")

# Barre latérale pour gérer les locataires
with st.sidebar:
    st.header("👥 Base Locataires")
    with st.expander("➕ Ajouter un locataire"):
        new_res = st.selectbox("Résidence", ["Canterane", "La Dussaude"])
        new_app = st.text_input("N° Appt")
        new_nom = st.text_input("Nom")
        if st.button("Enregistrer"):
            # Ici on simule l'ajout pour l'affichage immédiat
            new_row = pd.DataFrame({"Logement": [f"{new_res} {new_app}"], "Nom": [new_nom]})
            df_base = pd.concat([df_base, new_row], ignore_index=True)
            st.success("Ajouté (pensez à l'écrire sur votre Google Sheet)")

# Formulaire Principal
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
        n = st.text_input("N° Appartement")
    with col2:
        # On essaie de trouver le nom automatiquement
        id_recherche = f"{res} {n}"
        nom_trouve = ""
        if not df_base.empty:
            match = df_base[df_base['Logement'].astype(str).str.contains(n, na=False)]
            if not match.empty: nom_trouve = match.iloc[0]['Nom']
        nom = st.text_input("👤 Nom du Locataire", value=nom_trouve)

    st.divider()
    
    # Choix du type d'intervention
    type_inter = st.selectbox("🛠️ Type d'intervention", 
                               ["Plomberie", "VMC", "Serrurerie", "Électricité", "Chauffage", "Autre"])
    
    st.subheader("📸 Diagnostic Photo")
    photo = st.camera_input("Prendre une photo")
    
    analyse_ia = ""
    if photo and model:
        try:
            img = Image.open(photo)
            response = model.generate_content([f"En tant qu'expert {type_inter}, décris le problème sur la photo en 15 mots max.", img])
            analyse_ia = response.text
        except: analyse_ia = "Analyse impossible"

    notes = st.text_area("📝 Observations", value=analyse_ia)

    if st.button("GÉNÉRER LE RAPPORT FINAL"):
        date_j = date.today().strftime('%d/%m/%Y')
        rapport = f"🏢 RAPPORT D'INTERVENTION\n📅 Date : {date_j}\n📍 Lieu : {res} - Appt {n}\n👤 Locataire : {nom}\n🛠️ Type : {type_inter}\n\nCONSTAT :\n{notes}"
        st.divider()
        st.subheader("✅ Texte à copier :")
        st.code(rapport)
