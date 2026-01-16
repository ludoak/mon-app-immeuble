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

# --- CHARGEMENT SÉCURISÉ ---
try:
    # On lit le premier onglet disponible
    df_base = conn.read(spreadsheet=url_fiche, ttl=0)
    
    # NETTOYAGE : On enlève les espaces vides et on s'assure que les titres sont lisibles
    df_base.columns = [str(c).strip() for c in df_base.columns]
    
    # On vérifie si les colonnes essentielles sont là
    colonnes_ok = "Résidence" in df_base.columns and "Nom" in df_base.columns
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    df_base = pd.DataFrame()
    colonnes_ok = False

st.title("🚀 GH Diagnostic Rapide")

if colonnes_ok:
    tab1, tab2, tab3 = st.tabs(["🔍 Diagnostic", "👥 Gestion Locataires", "📜 Historique"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            res_list = df_base['Résidence'].unique()
            residence = st.selectbox("Sélectionner la Résidence", res_list)
            df_res = df_base[df_base['Résidence'] == residence]
            
            appts = sorted(df_res['Appartement'].astype(str).unique())
            appt_sel = st.selectbox("N° Appartement", appts)
            
            nom_loc = df_res[df_res['Appartement'].astype(str) == appt_sel]['Nom'].iloc[0]
            st.success(f"👤 Locataire : **{nom_loc}**")

        with col2:
            foto = st.file_uploader("📸 Photo", type=["jpg", "png", "jpeg"])
            note = st.text_input("🗒️ Note technique")

        if st.button("🔍 ANALYSER", type="primary", use_container_width=True):
            with st.spinner("Analyse Gemini 3..."):
                model = genai.GenerativeModel('gemini-3-flash-preview')
                prompt = f"Expert GH. Analyse : {note}. Charge locative ?"
                res = model.generate_content([prompt, Image.open(foto)] if foto else prompt)
                st.info(res.text)
                
                # Tentative d'historique (silencieuse si l'onglet manque)
                try:
                    df_h = conn.read(spreadsheet=url_fiche, worksheet="Historique", ttl=0)
                    n_ligne = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), f"{residence}-{appt_sel}", nom_loc, res.text]], columns=df_h.columns)
                    df_h = pd.concat([df_h, n_ligne], ignore_index=True)
                    conn.update(spreadsheet=url_fiche, worksheet="Historique", data=df_h)
                except:
                    pass

    with tab2:
        st.subheader("Ajouter un locataire")
        with st.form("add"):
            c1, c2, c3, c4 = st.columns(4)
            r = c1.text_input("Résidence")
            b = c2.text_input("Bâtiment")
            a = c3.text_input("Appartement")
            n = c4.text_input("Nom")
            if st.form_submit_button("Enregistrer"):
                new_row = pd.DataFrame([[r,b,a,n]], columns=df_base.columns[:4])
                df_base = pd.concat([df_base, new_row], ignore_index=True)
                conn.update(spreadsheet=url_fiche, data=df_base)
                st.rerun()

    with tab3:
        try:
            df_hist = conn.read(spreadsheet=url_fiche, worksheet="Historique", ttl=0)
            st.dataframe(df_hist, use_container_width=True)
        except:
            st.write("Onglet 'Historique' non détecté.")

else:
    # --- MODE DEBUG SI CA NE MARCHE PAS ---
    st.warning("⚠️ Problème de format détecté.")
    st.write("Voici les titres que l'IA voit actuellement dans votre fichier :")
    st.code(list(df_base.columns))
    st.write("Aperçu de vos données :")
    st.dataframe(df_base.head())
    st.info("💡 CONSEIL : Vérifiez que vos titres en ligne 1 sont exactement : Résidence, Bâtiment, Appartement, Nom")