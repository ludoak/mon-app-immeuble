import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide")

# --- 2. GESTION DES DONNÉES ---
DB_FILE = "base_locataires_gh.csv"

def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
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

# --- 3. INTERFACE ---
tab1, tab2 = st.tabs(["📸 Diagnostic Photo", "👥 Gestion Locataires"])

with tab1:
    st.title("🚀 GH Diagnostic Instantané")
    df = st.session_state.df_locataires

    col_a, col_b = st.columns(2)
    with col_a:
        res_sel = st.selectbox("📍 Résidence", sorted(df["Résidence"].unique().astype(str)))
    with col_b:
        df_res = df[df["Résidence"] == res_sel]
        appt_sel = st.selectbox("🚪 Appartement", sorted(df_res["Appartement"].astype(str).unique()))
    
    nom_loc = df_res[df_res["Appartement"].astype(str) == appt_sel]["Nom"].iloc[0] if not df_res.empty else "Inconnu"
    st.success(f"👤 Locataire : **{nom_loc}**")

    st.markdown("---")
    # Double option : Caméra ou Galerie
    cam_photo = st.camera_input("Prendre une photo")
    file_photo = st.file_uploader("Ou importer une image", type=["jpg", "png", "jpeg"])
    photo = cam_photo if cam_photo is not None else file_photo

    if photo:
        if st.button("🔍 LANCER L'ANALYSE", type="primary", use_container_width=True):
            with st.spinner("Analyse technique en cours..."):
                # On récupère tes deux clés dans l'ordre
                cles = [st.secrets.get("GEMINI_API_KEY"), st.secrets.get("GEMINI_API_KEY_2")]
                success = False
                
                for ma_cle in cles:
                    if ma_cle and not success:
                        try:
                            genai.configure(api_key=ma_cle)
                            # Utilisation du modèle 1.5 Flash (le plus stable)
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            img = Image.open(photo)
                            prompt = "Expert bâtiment GH. Analyse cette photo, décris le problème technique et conclus impérativement par CODE_RESULTAT:GH, CODE_RESULTAT:LOC ou CODE_RESULTAT:PREST."
                            
                            response = model.generate_content([prompt, img])
                            
                            if response.text:
                                reponse_ia = response.text
                                success = True
                                
                                # Détection de la charge
                                type_c = "🏢 CHARGE GH"
                                label_s = "Charge GH"
                                if "CODE_RESULTAT:LOC" in reponse_ia:
                                    type_c = "🛠️ CHARGE LOCATIVE"; label_s = "Charge Locative"
                                elif "CODE_RESULTAT:PREST" in reponse_ia:
                                    type_c = "🏗️ CHARGE PRESTATAIRE"; label_s = "Charge Prestataire"
                                
                                st.divider()
                                st.metric("DÉCISION", type_c)
                                description = reponse_ia.split("CODE_RESULTAT:")[0]
                                st.write(description)
                                
                                # Courrier automatique
                                lettre = f"OBJET : Signalement technique - {res_sel} / Appt {appt_sel}\nDATE : {datetime.now().strftime('%d/%m/%Y')}\n\nMadame, Monsieur,\n\nJ'ai constaté le désordre suivant dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :\n{description.strip()}\n\nCe désordre est classé en : {label_s}.\n\nCordialement,\nL'équipe technique GH."
                                st.text_area("Texte à copier :", lettre, height=200)
                                break
                        except Exception as e:
                            # Si la clé échoue, on continue vers la suivante
                            continue
                
                if not success:
                    st.error("❌ Erreur : Les deux clés API sont saturées ou invalides. Attendez 1 minute.")

# --- ONGLET 2 : GESTION ---
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
                st.rerun()
    
    st.subheader("📋 Liste actuelle")
    st.dataframe(st.session_state.df_locataires, use_container_width=True)