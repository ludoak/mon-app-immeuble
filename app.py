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

# --- 3. CONFIGURATION IA ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 4. INTERFACE ---
tab1, tab2 = st.tabs(["📸 Diagnostic Direct", "👥 Gestion Locataires"])

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

    # --- DOUBLE OPTION PHOTO ---
    st.subheader("📷 Étape 1 : Prendre ou Choisir une photo")
    cam_photo = st.camera_input("Option A : Appareil photo en direct")
    file_photo = st.file_uploader("Option B : Choisir depuis la galerie", type=["jpg", "png", "jpeg"])

    photo = cam_photo if cam_photo is not None else file_photo

    if photo:
        if st.button("🔍 LANCER L'ANALYSE EXPERTE", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                # LISTE DES MODÈLES (Gemini 3 en priorité, Flash en secours pour le quota)
                modeles_a_tester = ['gemini-3-flash-preview', 'gemini-1.5-flash']
                success = False
                
                for nom_modele in modeles_a_tester:
                    if not success:
                        try:
                            model = genai.GenerativeModel(nom_modele)
                            prompt = "Expert bâtiment GH. Analyse cette photo, décris le problème technique et conclus par CODE_RESULTAT:GH, CODE_RESULTAT:LOC ou CODE_RESULTAT:PREST."
                            
                            img = Image.open(photo)
                            response = model.generate_content([prompt, img], safety_settings={
                                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE", 
                                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE", 
                                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                            })
                            
                            if response.candidates and response.candidates[0].content.parts:
                                reponse_ia = response.text
                                success = True
                                
                                # --- LOGIQUE DE BADGE ---
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
                                st.caption(f"Analysé par : {nom_modele}")
                                
                                # --- COURRIER ---
                                st.subheader("✉️ Courrier pour la plateforme")
                                lettre = f"OBJET : Signalement technique - {res_sel} / Appt {appt_sel}\nDATE : {datetime.now().strftime('%d/%m/%Y')}\n\nMadame, Monsieur,\n\nJ'ai constaté le désordre suivant chez M./Mme {nom_loc} (Appt {appt_sel}) :\n{description.strip()}\n\nCe désordre est classé en : {label_s}.\n\nCordialement,\nL'équipe technique GH."
                                st.text_area("Texte à copier :", lettre, height=200)
                        
                        except Exception as e:
                            if "429" in str(e) or "quota" in str(e).lower():
                                continue # Passe au modèle suivant
                            else:
                                st.error(f"Erreur technique : {e}")
                                break
                
                if not success:
                    st.error("❌ Quota dépassé sur tous les modèles. Réessayez dans une minute ou utilisez une autre clé API.")

# --- ONGLET 2 : GESTION ---
with tab2:
    st.title("👥 Gestion de la Base")
    with st.expander("➕ Ajouter un locataire"):
        with st.form("ajout"):
            r = st.text_input("Résidence"); a = st.text_input("Appartement"); n = st.text_input("Nom")
            if st.form_submit_button("Enregistrer"):
                new_line = pd.DataFrame({"Résidence": [r], "Appartement": [str(a)], "Nom": [n]})
                st.session_state.df_locataires = pd.concat([st.session_state.df_locataires, new_line], ignore_index=True)
                sauvegarder_donnees(st.session_state.df_locataires)
                st.rerun()
    
    with st.expander("🗑️ Supprimer un locataire"):
        df_cur = st.session_state.df_locataires
        idx = st.selectbox("Locataire à retirer", range(len(df_cur)), format_func=lambda x: f"{df_cur.iloc[x]['Nom']} ({df_cur.iloc[x]['Résidence']})")
        if st.button("Confirmer la suppression"):
            st.session_state.df_locataires = df_cur.drop(idx).reset_index(drop=True)
            sauvegarder_donnees(st.session_state.df_locataires)
            st.rerun()
            
    st.dataframe(st.session_state.df_locataires, use_container_width=True)