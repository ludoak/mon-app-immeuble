import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# IA Gemini 3
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# Connexion GSheets (Lien Éditeur pour écriture)
conn = st.connection("gsheets", type=GSheetsConnection)
url_fiche = st.secrets["connections"]["gsheets"]["spreadsheet"]

def charger_onglet(nom):
    try:
        return conn.read(spreadsheet=url_fiche, worksheet=nom, ttl=0)
    except:
        return pd.DataFrame()

# --- CHARGEMENT ---
df_base = charger_onglet("Base_Locataires")

st.title("🚀 GH Diagnostic & Historique")

tab1, tab2, tab3 = st.tabs(["🔍 Diagnostic", "👥 Gestion Locataires", "📜 Historique"])

# --- TAB 1 : DIAGNOSTIC ---
with tab1:
    if not df_base.empty:
        col1, col2 = st.columns(2)
        with col1:
            residence = st.selectbox("Résidence", df_base['Résidence'].unique())
            df_res = df_base[df_base['Résidence'] == residence]
            appt_sel = st.selectbox("N° Appartement", sorted(df_res['Appartement'].astype(str).unique()))
            nom_loc = df_res[df_res['Appartement'].astype(str) == appt_sel]['Nom'].iloc[0]
            st.info(f"👤 **Locataire : {nom_loc}**")
        with col2:
            foto = st.file_uploader("📸 Photo du désordre", type=["jpg", "png", "jpeg"])
            note = st.text_input("🗒️ Note technique")

        if st.button("🔍 ANALYSER", type="primary", use_container_width=True):
            with st.spinner("Analyse par Gemini 3..."):
                model = genai.GenerativeModel('gemini-3-flash-preview')
                res = model.generate_content([f"Expert GH: {note}", Image.open(foto)] if foto else f"Expert GH: {note}")
                
                # Affichage résultat
                st.subheader("Diagnostic :")
                st.success(res.text)
                
                # SAUVEGARDE AUTO DANS L'HISTORIQUE
                try:
                    df_h = charger_onglet("Historique")
                    nouvelle_ligne = pd.DataFrame([[
                        datetime.now().strftime("%d/%m/%Y %H:%M"), 
                        f"{residence}-{appt_sel}", 
                        nom_loc, 
                        res.text
                    ]], columns=["Date", "Lieu", "Locataire", "Diagnostic"])
                    
                    df_h = pd.concat([df_h, nouvelle_ligne], ignore_index=True)
                    conn.update(spreadsheet=url_fiche, worksheet="Historique", data=df_h)
                    st.toast("✅ Rapport enregistré !")
                except Exception as e:
                    st.error(f"Erreur d'enregistrement historique : {e}")
    else:
        st.error("Base de données introuvable. Vérifiez les onglets du Google Sheets.")

# --- TAB 2 : GESTION ---
with tab2:
    st.subheader("➕ Ajouter un locataire")
    with st.form("ajout_form"):
        c1, c2, c3, c4 = st.columns(4)
        r = c1.selectbox("Résidence", ["Canterane", "La Dussaude"])
        b = c2.selectbox("Bâtiment", ["A", "B", "N/A"])
        a = c3.text_input("N° Appt")
        n = c4.text_input("Nom du locataire")
        if st.form_submit_button("Enregistrer dans la base"):
            new_df = pd.concat([df_base, pd.DataFrame([[r, b, a, n]], columns=df_base.columns)], ignore_index=True)
            conn.update(spreadsheet=url_fiche, worksheet="Base_Locataires", data=new_df)
            st.success("Locataire ajouté ! Veuillez rafraîchir la page.")

# --- TAB 3 : HISTORIQUE ---
with tab3:
    if st.button("🔄 Actualiser la liste"):
        st.rerun()
    df_histo = charger_onglet("Historique")
    if not df_histo.empty:
        st.dataframe(df_histo.sort_index(ascending=False), use_container_width=True)
    else:
        st.write("L'historique est vide pour le moment.")