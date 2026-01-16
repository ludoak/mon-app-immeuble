import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Rapide", layout="wide")

# IA Gemini 3
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# Connexion GSheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FONCTIONS DE LECTURE/ÉCRITURE ---
def charger_donnees(nom_onglet):
    try:
        # On récupère l'URL et on enlève tout ce qui dépasse après l'ID du document
        url_brute = st.secrets["connections"]["gsheets"]["spreadsheet"]
        url_propre = url_brute.split("/edit")[0].split("/pub")[0]
        
        # On lit l'onglet spécifique
        df = conn.read(spreadsheet=url_propre, worksheet=nom_onglet, ttl=0)
        
        # Nettoyage des colonnes
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        # Si l'onglet spécifique échoue, on tente de lire le fichier sans préciser l'onglet
        try:
            url_brute = st.secrets["connections"]["gsheets"]["spreadsheet"]
            url_propre = url_brute.split("/edit")[0].split("/pub")[0]
            df = conn.read(spreadsheet=url_propre, ttl=0)
            df.columns = df.columns.str.strip()
            return df
        except:
            return pd.DataFrame()

# --- 3. CHARGEMENT DES DONNÉES ---
df_base = charger_donnees("Base_Locataires")

st.title("🚀 GH Diagnostic Rapide")

tab1, tab2, tab3 = st.tabs(["🔍 Diagnostic", "👥 Gestion Locataires", "📜 Historique"])

# --- TAB 1 : DIAGNOSTIC ---
with tab1:
    if not df_base.empty and 'Nom' in df_base.columns:
        col1, col2 = st.columns(2)
        with col1:
            res_list = df_base['Résidence'].unique()
            residence = st.selectbox("Résidence", res_list)
            df_res = df_base[df_base['Résidence'] == residence]
            
            appts = sorted(df_res['Appartement'].astype(str).unique())
            appt_sel = st.selectbox("N° Appartement", appts)
            
            nom_loc = df_res[df_res['Appartement'].astype(str) == appt_sel]['Nom'].iloc[0]
            st.info(f"👤 **Locataire : {nom_loc}**")

        with col2:
            foto = st.file_uploader("📸 Photo", type=["jpg", "png", "jpeg"])
            note = st.text_input("🗒️ Note technique (ex: moisissures)")

        if st.button("🔍 ANALYSER LE DÉFAUT", type="primary", use_container_width=True):
            with st.spinner("Analyse par Gemini 3..."):
                try:
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt = f"Expert technique GH. Analyse : {note}. Charge locative ?"
                    res = model.generate_content([prompt, Image.open(foto)] if foto else prompt)
                    st.subheader("Diagnostic :")
                    st.success(res.text)
                    
                    # Sauvegarde Historique
                    try:
                        url_brute = st.secrets["connections"]["gsheets"]["spreadsheet"]
                        url_propre = url_brute.split("/edit")[0]
                        df_h = conn.read(spreadsheet=url_propre, worksheet="Historique", ttl=0)
                        n_ligne = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), f"{residence}-{appt_sel}", nom_loc, res.text]], 
                                               columns=["Date", "Lieu", "Locataire", "Diagnostic"])
                        df_h = pd.concat([df_h, n_ligne], ignore_index=True)
                        conn.update(spreadsheet=url_propre, worksheet="Historique", data=df_h)
                    except:
                        st.warning("⚠️ Impossible d'écrire dans l'onglet 'Historique'.")
                except Exception as e:
                    st.error(f"Erreur IA : {e}")
    else:
        st.error("❌ La base de données est vide ou mal formatée. Vérifiez vos titres de colonnes.")

# --- TAB 2 : GESTION ---
with tab2:
    st.subheader("➕ Ajouter un locataire")
    with st.form("add"):
        c1, c2, c3, c4 = st.columns(4)
        r = c1.selectbox("Résidence", ["Canterane", "La Dussaude"])
        b = c2.selectbox("Bâtiment", ["A", "B", "N/A"])
        a = c3.text_input("Appartement")
        n = c4.text_input("Nom")
        if st.form_submit_button("Valider"):
            new_row = pd.DataFrame([[r, b, a, n]], columns=df_base.columns)
            df_total = pd.concat([df_base, new_row], ignore_index=True)
            url_propre = st.secrets["connections"]["gsheets"]["spreadsheet"].split("/edit")[0]
            conn.update(spreadsheet=url_propre, worksheet="Base_Locataires", data=df_total)
            st.success("Ajouté ! Rafraîchissez la page.")

# --- TAB 3 : HISTORIQUE ---
with tab3:
    try:
        url_propre = st.secrets["connections"]["gsheets"]["spreadsheet"].split("/edit")[0]
        df_hist = conn.read(spreadsheet=url_propre, worksheet="Historique", ttl=0)
        st.dataframe(df_hist.sort_index(ascending=False), use_container_width=True)
    except:
        st.write("Historique vide.")