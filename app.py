import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH ImmoCheck - VITESSE", layout="wide")

# IA Gemini 3
api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Connexion GSheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. FONCTIONS DE DONNÉES (VERSION ROBUSTE) ---
def charger_base():
    try:
        # On utilise l'URL propre des secrets pour éviter l'erreur urllib
        url_propre = st.secrets["connections"]["gsheets"]["spreadsheet"].split("/edit")[0]
        df = conn.read(spreadsheet=url_propre, worksheet="Base_Locataires", ttl=0)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"⚠️ Erreur de lecture : {e}")
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

def sauver_base(df):
    try:
        url_propre = st.secrets["connections"]["gsheets"]["spreadsheet"].split("/edit")[0]
        conn.update(spreadsheet=url_propre, worksheet="Base_Locataires", data=df)
        st.cache_data.clear()
        st.success("💾 Base mise à jour avec succès !")
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde : {e}")

def ajouter_historique(date, lieu, locataire, diagnostic):
    try:
        url_propre = st.secrets["connections"]["gsheets"]["spreadsheet"].split("/edit")[0]
        try:
            hist = conn.read(spreadsheet=url_propre, worksheet="Historique", ttl=0)
        except:
            hist = pd.DataFrame(columns=["Date", "Lieu", "Locataire", "Diagnostic"])
        
        nouvelle_ligne = pd.DataFrame([[date, lieu, locataire, diagnostic]], columns=["Date", "Lieu", "Locataire", "Diagnostic"])
        hist = pd.concat([hist, nouvelle_ligne], ignore_index=True)
        conn.update(spreadsheet=url_propre, worksheet="Historique", data=hist)
    except Exception as e:
        st.warning(f"Impossible d'enregistrer l'historique : {e}")

# --- 3. CHARGEMENT INITIAL ---
df_base = charger_base()

# --- 4. INTERFACE ---
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
            note = st.text_input("🗒️ Note rapide", placeholder="Ex: Joint douche noirci")

        if st.button("🔍 ANALYSER", type="primary", use_container_width=True):
            with st.spinner("Analyse par Gemini 3..."):
                try:
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt = f"Expert technique GH. Analyse : {note}. Charge locative ?"
                    res = model.generate_content([prompt, Image.open(foto)] if foto else prompt)
                    
                    st.subheader("Diagnostic IA :")
                    st.write(res.text)
                    
                    ajouter_historique(datetime.now().strftime("%d/%m/%Y %H:%M"), f"{residence} - {appt}", nom_loc, res.text)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")
    else:
        st.warning("La base de données est vide ou inaccessible.")

# --- TAB 2 : GESTION LOCATAIRES ---
with tab2:
    st.subheader("➕ Ajouter un locataire")
    with st.form("form_ajout"):
        c1, c2, c3, c4 = st.columns(4)
        n_res = c1.selectbox("Résidence", ["Canterane", "La Dussaude"])
        n_bat = c2.selectbox("Bâtiment", ["A", "B", "N/A"])
        n_app = c3.text_input("N° Appt")
        n_nom = c4.text_input("Nom")
        if st.form_submit_button("Ajouter à la base"):
            new_row = pd.DataFrame([[n_res, n_bat, n_app, n_nom]], columns=df_base.columns)
            df_base = pd.concat([df_base, new_row], ignore_index=True)
            sauver_base(df_base)
            st.rerun()

    st.divider()
    st.subheader("🗑️ Supprimer un locataire")
    if not df_base.empty:
        target = st.selectbox("Locataire à supprimer", df_base.index, 
                              format_func=lambda x: f"{df_base.loc[x, 'Résidence']} - {df_base.loc[x, 'Appartement']} - {df_base.loc[x, 'Nom']}")
        if st.button("Supprimer définitivement"):
            df_base = df_base.drop(target)
            sauver_base(df_base)
            st.rerun()

# --- TAB 3 : HISTORIQUE ---
with tab3:
    if st.button("🔄 Actualiser l'historique"):
        st.rerun()
    try:
        url_propre = st.secrets["connections"]["gsheets"]["spreadsheet"].split("/edit")[0]
        df_hist = conn.read(spreadsheet=url_propre, worksheet="Historique", ttl=0)
        st.dataframe(df_hist.sort_index(ascending=False), use_container_width=True)
    except:
        st.write("Aucun historique trouvé.")