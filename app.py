import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# --- 2. GESTION DU FICHIER DE SAUVEGARDE ---
DB_FILE = "base_locataires_gh.csv"

def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        # Données initiales si le fichier n'existe pas encore
        data = {
            "Résidence": ["Canterane", "Canterane", "La Dussaude", "La Dussaude"],
            "Appartement": ["10", "40", "95", "64"],
            "Nom": ["lolo", "Aniotsbehere", "zezette", "kiki"]
        }
        df = pd.DataFrame(data)
        df.to_csv(DB_FILE, index=False)
        return df

def sauvegarder_donnees(df):
    df.to_csv(DB_FILE, index=False)

# Initialisation de la session
if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# --- 3. CONFIGURATION DE L'IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Clé API manquante !")

# --- 4. INTERFACE À ONGLETS ---
tab1, tab2 = st.tabs(["🔍 Diagnostic Photo", "👥 Gestion Locataires"])

# --- ONGLET 1 : DIAGNOSTIC ---
with tab1:
    st.title("🚀 GH Auto-Signalement")
    df = st.session_state.df_locataires

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📍 Localisation")
        res_sel = st.selectbox("Résidence", sorted(df["Résidence"].unique()))
        df_res = df[df["Résidence"] == res_sel]
        appt_sel = st.selectbox("Appartement", sorted(df_res["Appartement"].unique()))
        
        filtre = df_res[df_res["Appartement"] == appt_sel]
        if not filtre.empty:
            nom_loc = filtre["Nom"].iloc[0]
            st.success(f"👤 Locataire : **{nom_loc}**")

    with col2:
        st.subheader("📸 Constat")
        photo = st.file_uploader("Prendre la photo", type=["jpg", "png", "jpeg"])

    if st.button("🔍 ANALYSER", type="primary", use_container_width=True):
        if not photo:
            st.warning("Ajoutez une photo !")
        else:
            with st.spinner("Analyse par gemini-3-flash-preview..."):
                try:
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt = "Expert GH. Analyse cette photo, décris le problème et conclus par CODE_RESULTAT:GH, CODE_RESULTAT:LOC ou CODE_RESULTAT:PREST."
                    img = Image.open(photo)
                    res = model.generate_content([prompt, img])
                    
                    # Logique de badge
                    type_c = "🏢 CHARGE GH"
                    if "CODE_RESULTAT:LOC" in res.text: type_c = "🛠️ CHARGE LOCATIVE"
                    elif "CODE_RESULTAT:PREST" in res.text: type_c = "🏗️ CHARGE PRESTATAIRE"
                    
                    st.metric("DÉCISION", type_c)
                    st.write(res.text.split("CODE_RESULTAT:")[0])
                except Exception as e:
                    st.error(f"Erreur : {e}")

# --- ONGLET 2 : GESTION DES LOCATAIRES (SAUVEGARDE RÉELLE) ---
with tab2:
    st.title("👥 Gestion de la Base")
    
    # Ajouter
    with st.expander("➕ Ajouter un locataire"):
        with st.form("ajout"):
            c1, c2, c3 = st.columns(3)
            r = c1.text_input("Résidence")
            a = c2.text_input("Appartement")
            n = c3.text_input("Nom")
            if st.form_submit_button("Enregistrer"):
                new_line = pd.DataFrame({"Résidence": [r], "Appartement": [a], "Nom": [n]})
                st.session_state.df_locataires = pd.concat([st.session_state.df_locataires, new_line], ignore_index=True)
                sauvegarder_donnees(st.session_state.df_locataires)
                st.success("Sauvegardé !")
                st.rerun()

    # Supprimer
    with st.expander("🗑️ Supprimer un locataire"):
        df_cur = st.session_state.df_locataires
        idx = st.selectbox("Locataire à retirer", range(len(df_cur)), 
                           format_func=lambda x: f"{df_cur.iloc[x]['Nom']} ({df_cur.iloc[x]['Résidence']})")
        if st.button("Confirmer la suppression"):
            st.session_state.df_locataires = df_cur.drop(idx).reset_index(drop=True)
            sauvegarder_donnees(st.session_state.df_locataires)
            st.warning("Supprimé et sauvegardé !")
            st.rerun()

    st.subheader("📋 Liste actuelle")
    st.dataframe(st.session_state.df_locataires, use_container_width=True)