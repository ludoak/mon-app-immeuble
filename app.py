import streamlit as st
import pandas as pd
from datetime import date
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="ImmoCheck GH Pro", page_icon="🏢", layout="wide")

# Clé API Gemini
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. CONNEXION GOOGLE SHEETS ---
if "connections" in st.secrets:
    try:
        # On récupère l'URL et on s'assure qu'elle est propre
        url_sheet = st.secrets["connections"]["gsheets"]["spreadsheet"]
        if "/edit" in url_sheet:
            url_sheet = url_sheet.split("/edit")[0]
            
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # On tente de lire l'onglet "Base_Locataires"
        # Si ça échoue encore en 400, on tente de lire le premier onglet par défaut
        try:
            df_base = conn.read(spreadsheet=url_sheet, worksheet="Base_Locataires", ttl=0)
        except:
            df_base = conn.read(spreadsheet=url_sheet, ttl=0)
            
        df_base.columns = df_base.columns.str.strip()
        if 'Appartement' in df_base.columns:
            df_base['Appartement'] = df_base['Appartement'].astype(str).apply(lambda x: x.split('.')[0] if '.' in x else x)
            
    except Exception as e:
        st.error(f"❌ Erreur Sheets : {e}")
        df_base = pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])
else:
    st.error("❌ Configuration [connections.gsheets] manquante.")
    df_base = pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

# --- 3. INTERFACE ---
st.subheader("🛠️ Plateforme de signalement Gironde Habitat")

# (Le reste du code interface reste identique...)
with st.container(border=True):
    col_in1, col_in2 = st.columns([1, 1.5])
    with col_in1:
        source_photo = st.file_uploader("📸 Photo", type=["jpg", "jpeg", "png"])
    with col_in2:
        notes = st.text_input("🗒️ Notes terrain")
        lancer_analyse = st.button("🔍 ANALYSER", type="primary", use_container_width=True)

with st.expander("📍 Lieu et Locataire", expanded=True):
    res_sel = []
    c1, c2 = st.columns(2)
    if c1.checkbox("Canterane"): res_sel.append("Canterane")
    if c2.checkbox("La Dussaude"): res_sel.append("La Dussaude")
    
    if len(res_sel) == 1 and not df_base.empty:
        res = res_sel[0]
        filtre = df_base[df_base['Résidence'] == res]
        appts = sorted(filtre['Appartement'].unique())
        n_appt = st.selectbox("N° Appt", appts)
        nom_loc = filtre[filtre['Appartement'] == n_appt]['Nom'].iloc[0]
        st.write(f"👤 Locataire : **{nom_loc}**")
    else:
        st.info("Sélectionnez une seule résidence pour voir les locataires.")

# --- 4. ANALYSE IA (GEMINI 3) ---
if lancer_analyse:
    with st.spinner("Analyse Gemini 3..."):
        try:
            model = genai.GenerativeModel('gemini-3-flash-preview')
            res_ia = model.generate_content(f"Expert GH. Analyse : {notes}")
            st.success("### Analyse terminée")
            st.write(res_ia.text)
        except Exception as e:
            st.error(f"Erreur IA : {e}")