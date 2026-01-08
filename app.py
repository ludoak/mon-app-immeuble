import streamlit as st
from datetime import date
import google.generativeai as genai
from PIL import Image
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck Pro", page_icon="🏢", layout="wide")

# Connexion IA via les Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé IA manquante dans les Secrets")

# Connexion Tableau
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(worksheet="Locataires", ttl=0)
except:
    df_base = pd.DataFrame(columns=["Logement", "Nom"])

# Chargement du modèle Gemini 2.5 (Automatique)
@st.cache_resource
def load_model():
    try:
        # On cherche le modèle Flash le plus récent disponible pour ton compte
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except: return None

model = load_model()

# --- INTERFACE ---
st.title("🏢 Rapport d'Intervention Pro")

# Barre latérale : Gestion Locataires
with st.sidebar:
    st.header("👥 Base Locataires")
    with st.expander("➕ Ajouter un locataire"):
        new_res = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="add_res")
        new_bat = st.radio("Bâtiment", ["A", "B"], horizontal=True) if new_res == "Canterane" else ""
        new_app = st.text_input("N° Appt")
        new_nom = st.text_input("Nom")
        
        if st.button("Enregistrer"):
            log_id = f"{new_res} {new_bat} {new_app}".replace("  ", " ").strip()
            new_row = pd.DataFrame({"Logement": [log_id], "Nom": [new_nom]})
            df_updated = pd.concat([df_base, new_row], ignore_index=True)
            try:
                conn.update(worksheet="Locataires", data=df_updated)
                st.success(f"Enregistré : {log_id}")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur d'écriture : {e}")

# Formulaire Principal
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"], key="main_res")
        bat = st.radio("Bâtiment", ["A", "B"], horizontal=True) if res == "Canterane" else ""
        n = st.text_input("N° Appartement")
    with col2:
        id_recherche = f"{res} {bat} {n}".replace("  ", " ").strip()
        nom_trouve = ""
        if not df_base.empty:
            match = df_base[df_base['Logement'].astype(str).str.contains(n, na=False)]
            if res == "Canterane":
                match = match[match['Logement'].astype(str).str.contains(bat, na=False)]
            if not match.empty: nom_trouve = match.iloc[0]['Nom']
        nom = st.text_input("👤 Nom du Locataire", value=nom_trouve)

    st.divider()
    type_inter = st.selectbox("🛠️ Type d'intervention", ["Plomberie", "VMC", "Serrurerie", "Électricité", "Chauffage", "Autre"])
    
    photo = st.camera_input("📸 Photo du problème")
    
    analyse_ia = ""
    if photo:
        if model:
            try:
                img = Image.open(photo)
                # On demande à l'IA d'analyser
                response = model.generate_content([f"Analyse ce problème de {type_inter} et décris-le en 15 mots max pour un rapport.", img])
                analyse_ia = response.text
                st.success("✅ Analyse terminée")
            except Exception as e:
                st.error(f"Erreur IA : {e}")
        else:
            st.error("IA non disponible")

    notes = st.text_area("📝 Observations", value=analyse_ia)

    if st.button("GÉNÉRER LE RAPPORT FINAL"):
        date_j = date.today().strftime('%d/%m/%Y')
        lieu = f"{res} {'- Bât '+bat if bat else ''} - Appt {n}"
        rapport = f"🏢 RAPPORT D'INTERVENTION\n📅 Date : {date_j}\n📍 Lieu : {lieu}\n👤 Locataire : {nom}\n🛠️ Type : {type_inter}\n\nCONSTAT :\n{notes}"
        st.code(rapport)
