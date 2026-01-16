import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="GH Diagnostic", layout="wide")

# IA Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Connexion stable
conn = st.connection("gsheets", type=GSheetsConnection)
url_fiche = st.secrets["connections"]["gsheets"]["spreadsheet"]

# Chargement simplifié : on lit le premier onglet disponible
try:
    df_base = conn.read(spreadsheet=url_fiche, ttl=0)
    df_base.columns = [str(c).strip() for c in df_base.columns]
    erreur = False
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    erreur = True

st.title("🚀 GH Diagnostic Rapide")

if not erreur and not df_base.empty:
    col1, col2 = st.columns(2)
    with col1:
        # On utilise tes colonnes : Résidence, Bâtiment, Appartement, Nom
        res = st.selectbox("Résidence", df_base['Résidence'].unique())
        df_res = df_base[df_base['Résidence'] == res]
        
        appts = sorted(df_res['Appartement'].astype(str).unique())
        appt_sel = st.selectbox("Appartement", appts)
        
        nom_loc = df_res[df_res['Appartement'].astype(str) == appt_sel]['Nom'].iloc[0]
        st.success(f"👤 Locataire : **{nom_loc}**")

    with col2:
        note = st.text_input("🗒️ Note terrain")
        if st.button("🔍 ANALYSER", type="primary"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res_ia = model.generate_content(f"Expert GH. Analyse : {note}")
            st.info(res_ia.text)
            
            # Sauvegarde historique simplifiée
            try:
                n_ligne = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), res, nom_loc, res_ia.text]], columns=["Date", "Lieu", "Locataire", "Diagnostic"])
                conn.update(spreadsheet=url_fiche, worksheet="Historique", data=n_ligne)
                st.toast("Enregistré dans l'Historique")
            except: pass
else:
    st.warning("⚠️ Vérifiez que votre lien dans les secrets est le lien DIRECT (pas /pub).")