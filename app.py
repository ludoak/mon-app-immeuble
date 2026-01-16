import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH ImmoCheck", layout="wide")

# IA Gemini 3
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# Connexion GSheets
conn = st.connection("gsheets", type=GSheetsConnection)
url_fiche = st.secrets["connections"]["gsheets"]["spreadsheet"]

# --- 2. FONCTIONS ---
def charger_donnees(onglet):
    try:
        return conn.read(spreadsheet=url_fiche, worksheet=onglet, ttl=0)
    except:
        return pd.DataFrame()

# --- 3. CHARGEMENT ---
df_base = charger_donnees("Base_Locataires")

st.title("🚀 GH Diagnostic Rapide")

tab1, tab2, tab3 = st.tabs(["🔍 Diagnostic", "👥 Gestion Locataires", "📜 Historique"])

# --- TAB 1 : DIAGNOSTIC ---
with tab1:
    if not df_base.empty:
        col1, col2 = st.columns(2)
        with col1:
            residence = st.selectbox("Résidence", df_base['Résidence'].unique())
            df_res = df_base[df_base['Résidence'] == residence]
            appt = st.selectbox("N° Appt", sorted(df_res['Appartement'].astype(str).unique()))
            nom_loc = df_res[df_res['Appartement'].astype(str) == appt]['Nom'].iloc[0]
            st.info(f"👤 **Locataire : {nom_loc}**")

        with col2:
            foto = st.file_uploader("📸 Photo", type=["jpg", "png", "jpeg"])
            note = st.text_input("🗒️ Note terrain")

        if st.button("🔍 ANALYSER", type="primary", use_container_width=True):
            with st.spinner("Analyse..."):
                model = genai.GenerativeModel('gemini-3-flash-preview')
                prompt = f"Expert GH. Analyse : {note}. Charge locative ?"
                res = model.generate_content([prompt, Image.open(foto)] if foto else prompt)
                st.subheader("Diagnostic IA :")
                st.write(res.text)
                
                # Sauvegarde Historique
                try:
                    hist = charger_donnees("Historique")
                    new_h = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), f"{residence}-{appt}", nom_loc, res.text]], 
                                         columns=["Date", "Lieu", "Locataire", "Diagnostic"])
                    hist = pd.concat([hist, new_h], ignore_index=True)
                    conn.update(spreadsheet=url_fiche, worksheet="Historique", data=hist)
                    st.success("✅ Enregistré")
                except:
                    st.warning("Onglet 'Historique' manquant.")
    else:
        st.error("Impossible de charger la Base_Locataires. Vérifiez le lien dans les Secrets.")

# --- TAB 2 : GESTION ---
with tab2:
    st.subheader("➕ Ajouter un locataire")
    with st.form("add_loc"):
        res_n = st.selectbox("Résidence", ["Canterane", "La Dussaude"])
        bat_n = st.selectbox("Bâtiment", ["A", "B", "N/A"])
        app_n = st.text_input("Appartement")
        nom_n = st.text_input("Nom")
        if st.form_submit_button("Valider l'ajout"):
            new_df = pd.concat([df_base, pd.DataFrame([[res_n, bat_n, app_n, nom_n]], columns=df_base.columns)], ignore_index=True)
            conn.update(spreadsheet=url_fiche, worksheet="Base_Locataires", data=new_df)
            st.success("Ajouté ! Actualisez la page.")

# --- TAB 3 : HISTORIQUE ---
with tab3:
    df_h = charger_donnees("Historique")
    if not df_h.empty:
        st.dataframe(df_h.sort_index(ascending=False), use_container_width=True)