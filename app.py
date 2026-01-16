import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. CONFIGURATION PAGE ---
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

# --- 3. INTERFACE ---
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
    cam_photo = st.camera_input("Option A : Appareil photo")
    file_photo = st.file_uploader("Option B : Galerie", type=["jpg", "png", "jpeg"])
    photo = cam_photo if cam_photo is not None else file_photo

    if photo:
        if st.button("🔍 LANCER L'ANALYSE", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours (Vérification des accès)..."):
                # On récupère les deux clés depuis les secrets
                cles = [st.secrets.get("GEMINI_API_KEY"), st.secrets.get("GEMINI_API_KEY_2")]
                # Noms de modèles standardisés pour éviter l'erreur 404
                modeles = ['gemini-1.5-flash', 'gemini-1.5-pro']
                
                success = False
                for c in cles:
                    if c and not success:
                        try:
                            genai.configure(api_key=c)
                            for m in modeles:
                                if not success:
                                    try:
                                        model = genai.GenerativeModel(model_name=m)
                                        img = Image.open(photo)
                                        
                                        # Demande d'analyse
                                        response = model.generate_content([
                                            "Expert bâtiment GH. Analyse cette photo, décris le problème technique précisément et conclus impérativement par CODE_RESULTAT:GH, CODE_RESULTAT:LOC ou CODE_RESULTAT:PREST.", 
                                            img
                                        ])
                                        
                                        if response and response.text:
                                            reponse_ia = response.text
                                            success = True
                                            
                                            # Logique de badge
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
                                            st.caption(f"Analysé avec succès par {m}")
                                            
                                            # Courrier auto
                                            lettre = f"OBJET : Signalement technique - {res_sel} / Appt {appt_sel}\nDATE : {datetime.now().strftime('%d/%m/%Y')}\n\nMadame, Monsieur,\n\nJ'ai constaté le désordre suivant dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :\n{description.strip()}\n\nCe désordre est classé en : {label_s}.\n\nCordialement,\nL'équipe technique GH."
                                            st.text_area("Texte à copier :", lettre, height=200)
                                            break
                                    except Exception as e_inner:
                                        # Si le modèle m échoue, on passe au modèle suivant
                                        continue
                        except Exception as e_outer:
                            # Si la clé c échoue, on passe à la clé suivante
                            continue
                
                if not success:
                    st.error("❌ Erreur de quota ou technique. Les clés ne répondent pas. Vérifie tes secrets ou attends 1 minute.")

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