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
        new_res = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="add_res")
        
        # Logique Bâtiment pour l'ajout
        new_bat = ""
        if new_res == "Canterane":
            new_bat = st.radio("Bâtiment", ["A", "B"], horizontal=True, key="add_bat")
            
        new_app = st.text_input("N° Appt", key="add_app")
        new_nom = st.text_input("Nom", key="add_nom")
        
        if st.button("Enregistrer"):
            log_id = f"{new_res} {new_bat} {new_app}".replace("  ", " ").strip()
            new_row = pd.DataFrame({"Logement": [log_id], "Nom": [new_nom]})
            df_base = pd.concat([df_base, new_row], ignore_index=True)
            st.success(f"Ajouté : {log_id}")

# Formulaire Principal
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"], key="main_res")
        
        # --- AJOUT DU BATIMENT SI CANTERANE ---
        bat = ""
        if res == "Canterane":
            bat = st.radio("Bâtiment", ["A", "B"], horizontal=True, key="main_bat")
            
        n = st.text_input("N° Appartement", key="main_n")
    
    with col2:
        # On essaie de trouver le nom avec la logique Résidence + Bâtiment + Appt
        id_recherche = f"{res} {bat} {n}".replace("  ", " ").strip()
        nom_trouve = ""
        if not df_base.empty:
            # On cherche une correspondance dans la base
            match = df_base[df_base['Logement'].astype(str).str.contains(n, na=False)]
            if res == "Canterane":
                match = match[match['Logement'].astype(str).str.contains(bat, na=False)]
            
            if not match.empty: 
                nom_trouve = match.iloc[0]['Nom']
        
        nom = st.text_input("👤 Nom du Locataire", value=nom_trouve)

    st.divider()
    
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
        # On formate joliment le lieu
        lieu_affichage = f"{res}"
        if bat: lieu_affichage += f" - Bât {bat}"
        lieu_affichage += f" - Appt {n}"
        
        rapport = f"🏢 RAPPORT D'INTERVENTION\n📅 Date : {date_j}\n📍 Lieu : {lieu_affichage}\n👤 Locataire : {nom}\n🛠️ Type : {type_inter}\n\nCONSTAT :\n{notes}"
        st.divider()
        st.subheader("✅ Texte à copier :")
        st.code(rapport)
