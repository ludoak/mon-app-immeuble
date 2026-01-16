import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime
import os

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="GH Diagnostic Pro", layout="wide", page_icon="🏢")

# --- 2. GESTION DE LA BASE DE DONNÉES LOCALE (CSV) ---
DB_FILE = "base_locataires_gh.csv"

def charger_donnees():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE, dtype={"Appartement": str})
    else:
        # Données par défaut si le fichier n'existe pas encore
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

# Initialisation de la base dans la session
if 'df_locataires' not in st.session_state:
    st.session_state.df_locataires = charger_donnees()

# --- 3. CONFIGURATION DE L'IA ---
# Utilise la clé que tu as débloquée en "Pay-as-you-go"
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Clé API manquante dans les Secrets Streamlit !")

# --- 4. INTERFACE À ONGLETS ---
tab1, tab2 = st.tabs(["📸 Diagnostic Terrain", "👥 Gestion Locataires"])

# --- ONGLET 1 : DIAGNOSTIC ---
with tab1:
    st.title("🚀 GH Auto-Signalement")
    df = st.session_state.df_locataires

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📍 Localisation")
        res_sel = st.selectbox("Sélectionner la Résidence", sorted(df["Résidence"].unique().astype(str)))
        
        df_res = df[df["Résidence"] == res_sel]
        appt_sel = st.selectbox("Numéro d'Appartement", sorted(df_res["Appartement"].unique().astype(str)))
        
        # Récupération du nom du locataire
        filtre = df_res[df_res["Appartement"].astype(str) == appt_sel]
        nom_loc = filtre["Nom"].iloc[0] if not filtre.empty else "Inconnu"
        st.success(f"👤 Locataire : **{nom_loc}**")

    st.divider()

    # SECTION PHOTO
    st.subheader("📷 Constat Visuel")
    cam_photo = st.camera_input("Prendre une photo en direct")
    file_photo = st.file_uploader("Ou importer depuis la galerie", type=["jpg", "png", "jpeg"])
    
    # Priorité à la caméra si les deux sont présents
    photo = cam_photo if cam_photo is not None else file_photo

    if photo:
        if st.button("🔍 LANCER L'ANALYSE TECHNIQUE", type="primary", use_container_width=True):
            with st.spinner("Analyse par l'IA en cours..."):
                try:
                    # Modèle Flash : le plus rapide et stable pour le mode payant
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    img = Image.open(photo)
                    prompt = """Tu es un expert en maintenance immobilière pour Gironde Habitat. 
                    Analyse cette photo de désordre. 
                    1. Décris techniquement le problème.
                    2. Détermine si c'est une charge pour le BAILLEUR (GH) ou le LOCATAIRE.
                    Conclus impérativement ton texte par : CODE_RESULTAT:GH ou CODE_RESULTAT:LOC."""
                    
                    response = model.generate_content([prompt, img])
                    reponse_ia = response.text
                    
                    # Logique d'affichage du résultat
                    type_c = "🏢 CHARGE GH (Bailleur)"
                    label_simple = "Charge GH"
                    if "CODE_RESULTAT:LOC" in reponse_ia.upper():
                        type_c = "🛠️ CHARGE LOCATIVE"
                        label_simple = "Charge Locative"
                    
                    st.divider()
                    st.metric("DÉCISION", type_c)
                    
                    # Nettoyage du texte IA
                    description = reponse_ia.split("CODE_RESULTAT:")[0].strip()
                    st.markdown(f"**Analyse de l'expert :**\n\n{description}")
                    
                    # --- GÉNÉRATION DU COURRIER ---
                    st.subheader("✉️ Courrier de signalement")
                    lettre = f"""OBJET : Signalement technique - {res_sel} / Appt {appt_sel}
DATE : {datetime.now().strftime('%d/%m/%Y')}

Madame, Monsieur,

Un désordre technique a été constaté dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :
{description}

Ce désordre est classé en : {label_simple}.

Cordialement,
L'équipe technique GH."""
                    st.text_area("Texte à copier :", lettre, height=250)
                    
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")

# --- ONGLET 2 : GESTION DES LOCATAIRES ---
with tab2:
    st.title("👥 Gestion de la Base")
    
    # Ajouter un locataire
    with st.expander("➕ Ajouter un nouveau locataire"):
        with st.form("form_ajout"):
            new_res = st.text_input("Résidence")
            new_appt = st.text_input("Appartement")
            new_nom = st.text_input("Nom du locataire")
            if st.form_submit_button("Enregistrer dans la base"):
                if new_res and new_appt and new_nom:
                    nouveau_df = pd.DataFrame({"Résidence": [new_res], "Appartement": [str(new_appt)], "Nom": [new_nom]})
                    st.session_state.df_locataires = pd.concat([st.session_state.df_locataires, nouveau_df], ignore_index=True)
                    sauvegarder_donnees(st.session_state.df_locataires)
                    st.success("Locataire ajouté !")
                    st.rerun()
                else:
                    st.warning("Veuillez remplir tous les champs.")

    # Supprimer un locataire
    with st.expander("🗑️ Supprimer un locataire"):
        df_actuel = st.session_state.df_locataires
        liste_suppr = [f"{row['Nom']} ({row['Résidence']} - {row['Appartement']})" for idx, row in df_actuel.iterrows()]
        choix_suppr = st.selectbox("Sélectionner le locataire à retirer", range(len(liste_suppr)), format_func=lambda x: liste_suppr[x])
        
        if st.button("Confirmer la suppression définitive"):
            st.session_state.df_locataires = df_actuel.drop(choix_suppr).reset_index(drop=True)
            sauvegarder_donnees(st.session_state.df_locataires)
            st.warning("Locataire supprimé.")
            st.rerun()

    st.divider()
    st.subheader("📋 Liste complète des locataires")
    st.dataframe(st.session_state.df_locataires, use_container_width=True)