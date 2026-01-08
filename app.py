import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="ImmoCheck Pro IA", page_icon="🏢", layout="wide")

# --- 1. CONNEXION GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_base = conn.read(worksheet="Locataires", ttl=0)
except Exception as e:
    st.error(f"Erreur Google Sheets : {e}")
    df_base = pd.DataFrame(columns=["Logement", "Nom"])

# --- 2. CONFIGURATION IA GEMINI ---
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"Erreur technique IA : {e}")
else:
    st.warning("⚠️ Clé GEMINI_API_KEY manquante dans les Secrets.")

# --- FONCTIONS SAUVEGARDE ---
def sauvegarder_locataire(logement, nom):
    df = conn.read(worksheet="Locataires", ttl=0)
    if logement in df['Logement'].values:
        df.loc[df['Logement'] == logement, 'Nom'] = nom
    else:
        new_row = pd.DataFrame({"Logement": [logement], "Nom": [nom]})
        df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

# --- INTERFACE PRINCIPALE ---
st.title("🏢 Gestion & Rapports IA")

# Menu latéral : Gestion des locataires
with st.sidebar:
    st.header("👥 Base Locataires")
    with st.expander("➕ Ajouter / Modifier"):
        res_a = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="res_a")
        bat_a = ""
        if res_a == "Canterane":
            bat_a = st.radio("Bâtiment", ["A", "B"], horizontal=True, key="bat_a")
            app_a = st.text_input("Appartement", key="app_a")
            cle_a = f"Canterane - Bat {bat_a} - Appt {app_a}"
        else:
            app_a = st.number_input("Appartement", 1, 95, key="app_a_d")
            cle_a = f"La Dussaude - Appt {app_a}"
        
        nom_a = st.text_input("Nom du locataire", key="nom_a")
        
        if st.button("Enregistrer dans le tableau"):
            sauvegarder_locataire(cle_a, nom_a)
            st.success("C'est enregistré ! Actualisez la page.")
            st.rerun()

# --- FORMULAIRE DE RAPPORT ---
st.subheader("📝 Nouveau Rapport d'Intervention")
with st.container(border=True):
    res = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"])
    
    col1, col2 = st.columns(2)
    with col1:
        if res == "Canterane":
            bat = st.radio("Bâtiment", ["A", "B"], horizontal=True)
            n = st.text_input("N° Appt")
            id_l = f"Canterane - Bat {bat} - Appt {n}"
        else:
            n = st.number_input("N° Appt", 1, 95)
            id_l = f"La Dussaude - Appt {n}"
            
    with col2:
        # Recherche auto du nom
        nom_auto = ""
        if not df_base.empty and id_l in df_base['Logement'].values:
            nom_auto = df_base.loc[df_base['Logement'] == id_l, 'Nom'].values[0]
        nom = st.text_input("👤 Locataire", value=nom_auto)

    st.divider()
    
    # PARTIE PHOTO & IA
    st.subheader("📸 Diagnostic Photo")
    photo = st.camera_input("Prendre une photo du problème")
    
    analyse_ia = ""
    if photo and "GEMINI_API_KEY" in st.secrets:
        img = Image.open(photo)
        with st.spinner("L'IA analyse les dégâts..."):
            try:
                prompt = "En tant qu'expert en maintenance de bâtiment, décris ce problème technique visible sur la photo. Sois concis (max 30 mots) pour un rapport d'intervention."
                response = model.generate_content([prompt, img])
                analyse_ia = response.text
            except Exception as e:
                st.error(f"L'IA n'a pas pu répondre : {e}")

    notes = st.text_area("Observations (Rempli par l'IA si photo prise)", value=analyse_ia)

    if st.form_submit_button("GÉNÉRER LE TEXTE"):
        date_jour = date.today().strftime('%d/%m/%Y')
        rapport = f"DATE : {date_jour}\nLIEU : {id_l}\nLOCATAIRE : {nom}\n\nCONSTAT :\n{notes}"
        st.text_area("Copier le texte ci-dessous :", value=rapport, height=200)
