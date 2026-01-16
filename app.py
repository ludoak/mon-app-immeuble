import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# Configuration IA
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Connexion Sheets
conn = st.connection("gsheets", type=GSheetsConnection)
url_fiche = st.secrets["connections"]["gsheets"]["spreadsheet"]

# --- CHARGEMENT ---
try:
    # On lit sans filtre pour voir ce qui arrive
    df_base = conn.read(spreadsheet=url_fiche, ttl=0)
    # Nettoyage profond des noms de colonnes
    df_base.columns = [str(c).strip() for c in df_base.columns]
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    df_base = pd.DataFrame()

st.title("🚀 GH Diagnostic Rapide")

# --- VERIFICATION VISUELLE ---
if df_base.empty:
    st.warning("📂 Le fichier semble vide ou l'onglet est introuvable.")
    if st.button("🛠️ Créer la structure automatique"):
        df_init = pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])
        conn.update(spreadsheet=url_fiche, worksheet="Base_Locataires", data=df_init)
        st.success("Structure créée ! Ajoutez un locataire dans l'onglet Gestion.")
        st.rerun()
else:
    # On vérifie si "Résidence" existe, sinon on prend la 1ère colonne
    col_res = "Résidence" if "Résidence" in df_base.columns else df_base.columns[0]
    col_nom = "Nom" if "Nom" in df_base.columns else df_base.columns[-1]

    tab1, tab2, tab3 = st.tabs(["🔍 Diagnostic", "👥 Gestion Locataires", "📜 Historique"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            res_list = sorted(df_base[col_res].dropna().unique())
            residence = st.selectbox("Résidence", res_list)
            
            df_res = df_base[df_base[col_res] == residence]
            appts = sorted(df_res['Appartement'].astype(str).unique())
            appt_sel = st.selectbox("N° Appartement", appts)
            
            df_sel = df_res[df_res['Appartement'].astype(str) == appt_sel]
            
            if not df_sel.empty:
                nom_loc = df_sel[col_nom].iloc[0]
                st.success(f"👤 Locataire : **{nom_loc}**")
            else:
                nom_loc = "Inconnu"

        with col2:
            foto = st.file_uploader("📸 Photo", type=["jpg", "png", "jpeg"])
            note = st.text_input("🗒️ Note terrain")

        if st.button("🔍 ANALYSER", type="primary", use_container_width=True):
            with st.spinner("Analyse Gemini 3..."):
                try:
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt = f"Expert GH. Analyse : {note}. Charge locative ?"
                    res = model.generate_content([prompt, Image.open(foto)] if foto else prompt)
                    st.info(res.text)
                    
                    # Historique auto-créé si besoin
                    try:
                        n_ligne = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y %H:%M"), f"{residence}-{appt_sel}", nom_loc, res.text]], columns=["Date", "Lieu", "Locataire", "Diagnostic"])
                        conn.update(spreadsheet=url_fiche, worksheet="Historique", data=n_ligne)
                    except: pass
                except Exception as e:
                    st.error(f"Erreur IA : {e}")

    with tab2:
        st.write("### Ajouter un locataire")
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            r = c1.text_input("Résidence")
            b = c2.text_input("Bâtiment")
            a = c3.text_input("Appartement")
            n = c4.text_input("Nom")
            if st.form_submit_button("➕ Ajouter"):
                new_row = pd.concat([df_base, pd.DataFrame([[r,b,a,n]], columns=df_base.columns[:4])], ignore_index=True)
                conn.update(spreadsheet=url_fiche, worksheet="Base_Locataires", data=new_row)
                st.rerun()

    with tab3:
        st.write("Dernières analyses enregistrées :")
        try:
            df_h = conn.read(spreadsheet=url_fiche, worksheet="Historique", ttl=0)
            st.table(df_h.tail(10))
        except:
            st.info("L'historique s'affichera après votre première analyse.")

# --- ZONE DE DEBUG (Visible seulement si problème) ---
with st.expander("🛠️ Debug : Voir ce que l'application reçoit"):
    st.write("Titres détectés :", list(df_base.columns))
    st.dataframe(df_base)