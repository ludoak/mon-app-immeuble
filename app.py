import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="GH ImmoCheck - VITESSE", layout="wide")

# IA Gemini 3
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Connexion GSheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTIONS DE DONNÉES ---
def charger_base():
    return conn.read(worksheet="Base_Locataires", ttl=0)

def sauver_base(df):
    conn.update(worksheet="Base_Locataires", data=df)
    st.cache_data.clear()

def ajouter_historique(date, lieu, locataire, diagnostic):
    try:
        hist = conn.read(worksheet="Historique", ttl=0)
    except:
        hist = pd.DataFrame(columns=["Date", "Lieu", "Locataire", "Diagnostic"])
    
    nouvelle_ligne = pd.DataFrame([[date, lieu, locataire, diagnostic]], columns=hist.columns)
    hist = pd.concat([hist, nouvelle_ligne], ignore_index=True)
    conn.update(worksheet="Historique", data=hist)

# --- INTERFACE ---
st.title("🚀 GH Diagnostic Rapide")

tab1, tab2, tab3 = st.tabs(["🔍 Diagnostic", "👥 Gestion Locataires", "📜 Historique"])

# --- TAB 1 : DIAGNOSTIC ---
with tab1:
    df_base = charger_base()
    col1, col2 = st.columns(2)
    
    with col1:
        residence = st.selectbox("Résidence", df_base['Résidence'].unique())
        df_res = df_base[df_base['Résidence'] == residence]
        appt = st.selectbox("N° Appt", sorted(df_res['Appartement'].astype(str).unique()))
        nom_loc = df_res[df_res['Appartement'].astype(str) == appt]['Nom'].iloc[0]
        st.info(f"👤 **Locataire : {nom_loc}**")

    with col2:
        foto = st.file_uploader("📸 Photo", type=["jpg", "png", "jpeg"])
        note = st.text_input("🗒️ Note rapide (ex: joint noir)")

    if st.button("🔍 ANALYSER MAINTENANT", type="primary", use_container_width=True):
        if foto or note:
            with st.spinner("Analyse..."):
                model = genai.GenerativeModel('gemini-3-flash-preview')
                prompt = f"Expert GH. Analyse : {note}. Charge locative ?"
                res = model.generate_content([prompt, Image.open(foto)] if foto else prompt)
                
                st.subheader("Diagnostic IA :")
                st.write(res.text)
                
                # Sauvegarde auto dans l'historique
                ajouter_historique(datetime.now().strftime("%d/%m/%Y %H:%M"), f"{residence} - {appt}", nom_loc, res.text)
                st.success("✅ Diagnostic enregistré dans l'historique")

# --- TAB 2 : GESTION LOCATAIRES ---
with tab2:
    st.subheader("Ajouter un locataire")
    with st.form("Ajout"):
        new_res = st.selectbox("Résidence", ["Canterane", "La Dussaude"])
        new_bat = st.selectbox("Bâtiment", ["A", "B", "N/A"])
        new_appt = st.text_input("N° Appartement")
        new_nom = st.text_input("Nom du locataire")
        if st.form_submit_button("➕ Ajouter à la base"):
            nouvelle_ligne = pd.DataFrame([[new_res, new_bat, new_appt, new_nom]], columns=df_base.columns)
            df_base = pd.concat([df_base, nouvelle_ligne], ignore_index=True)
            sauver_base(df_base)
            st.success("Locataire ajouté !")
            st.rerun()

    st.divider()
    st.subheader("Supprimer un locataire")
    idx_to_del = st.selectbox("Sélectionner pour supprimer", df_base.index, format_func=lambda x: f"{df_base.iloc[x]['Résidence']} - {df_base.iloc[x]['Appartement']} - {df_base.iloc[x]['Nom']}")
    if st.button("🗑️ Supprimer définitivement", type="secondary"):
        df_base = df_base.drop(idx_to_del)
        sauver_base(df_base)
        st.warning("Locataire supprimé.")
        st.rerun()

# --- TAB 3 : HISTORIQUE ---
with tab3:
    try:
        df_hist = conn.read(worksheet="Historique", ttl=0)
        st.dataframe(df_hist.sort_index(ascending=False), use_container_width=True)
    except:
        st.write("Aucun historique pour le moment.")