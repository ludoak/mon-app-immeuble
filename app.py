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
        return pd.read_csv(DB_FILE, dtype={"Appartement": str}) # On force le texte
    else:
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
        res_sel = st.selectbox("Résidence", sorted(df["Résidence"].unique().astype(str)))
        df_res = df[df["Résidence"] == res_sel]
        
        # CORRECTION ICI : On force en texte (str) pour éviter le crash du tri
        liste_appts = sorted(df_res["Appartement"].astype(str).unique())
        appt_sel = st.selectbox("Appartement", liste_appts)
        
        filtre = df_res[df_res["Appartement"].astype(str) == appt_sel]
        nom_loc = filtre["Nom"].iloc[0] if not filtre.empty else "Inconnu"
        st.success(f"👤 Locataire : **{nom_loc}**")

    with col2:
        st.subheader("📸 Constat")
        photo = st.file_uploader("Prendre la photo", type=["jpg", "png", "jpeg"])

    if st.button("🔍 ANALYSER ET GÉNÉRER LA LETTRE", type="primary", use_container_width=True):
        if not photo:
            st.warning("Ajoutez une photo !")
        else:
            with st.spinner("Analyse par gemini-3-flash-preview..."):
                try:
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    prompt = "Expert GH. Analyse cette photo, décris le problème et conclus par CODE_RESULTAT:GH, CODE_RESULTAT:LOC ou CODE_RESULTAT:PREST."
                    img = Image.open(photo)
                    res = model.generate_content([prompt, img])
                    reponse_ia = res.text
                    
                    # Logique de badge
                    type_c = "🏢 CHARGE GH"
                    label_simple = "Charge GH"
                    if "CODE_RESULTAT:LOC" in reponse_ia: 
                        type_c = "🛠️ CHARGE LOCATIVE"; label_simple = "Charge Locative"
                    elif "CODE_RESULTAT:PREST" in reponse_ia: 
                        type_c = "🏗️ CHARGE PRESTATAIRE"; label_simple = "Charge Prestataire"
                    
                    st.divider()
                    st.metric("DÉCISION", type_c)
                    description = reponse_ia.split("CODE_RESULTAT:")[0]
                    st.write(description)
                    
                    # --- GÉNÉRATION DE LA LETTRE ---
                    st.subheader("✉️ Courrier pour la plateforme")
                    lettre = f"""OBJET : Signalement technique - {res_sel} / Appt {appt_sel}
DATE : {datetime.now().strftime("%d/%m/%Y")}

Madame, Monsieur,

J'ai constaté le désordre suivant dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :
{description.strip()}

Après diagnostic, ce désordre est classé en : {label_simple}.

Cordialement,
L'équipe technique GH."""
                    st.text_area("Texte à copier :", lettre, height=200)

                except Exception as e:
                    st.error(f"Erreur : {e}")

# --- ONGLET 2 : GESTION DES LOCATAIRES ---
with tab2:
    st.title("👥 Gestion de la Base")
    with st.expander("➕ Ajouter un locataire"):
        with st.form("ajout"):
            r = st.text_input("Résidence")
            a = st.text_input("Appartement")
            n = st.text_input("Nom")
            if st.form_submit_button("Enregistrer"):
                new_line = pd.DataFrame({"Résidence": [r], "Appartement": [str(a)], "Nom": [n]})
                st.session_state.df_locataires = pd.concat([st.session_state.df_locataires, new_line], ignore_index=True)
                sauvegarder_donnees(st.session_state.df_locataires)
                st.success("Sauvegardé !")
                st.rerun()

    with st.expander("🗑️ Supprimer un locataire"):
        df_cur = st.session_state.df_locataires
        idx = st.selectbox("Sélectionner pour supprimer", range(len(df_cur)), 
                           format_func=lambda x: f"{df_cur.iloc[x]['Nom']} ({df_cur.iloc[x]['Résidence']})")
        if st.button("Confirmer la suppression"):
            st.session_state.df_locataires = df_cur.drop(idx).reset_index(drop=True)
            sauvegarder_donnees(st.session_state.df_locataires)
            st.rerun()

    st.dataframe(st.session_state.df_locataires, use_container_width=True)