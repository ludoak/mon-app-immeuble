import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials

# Configuration de la page
st.set_page_config(page_title="GH Expert Pro", layout="wide")

# --- 1. CONNEXION GOOGLE SHEETS ---
def load_data():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["connections"]["gsheets"]["credentials"]
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        sh = client.open_by_url(spreadsheet_url)
        worksheet = sh.sheet1
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Connexion Google Sheets échouée : {e}")
        return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])

df = load_data()

# --- 2. CONNEXION IA ---
if "CLE_TEST" not in st.secrets:
    st.error("Clé API Gemini non trouvée.")
    st.stop()
else:
    try:
        genai.configure(api_key=st.secrets["CLE_TEST"])
        models_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_id = next((m for m in models_list if "flash" in m), models_list[0])
        model = genai.GenerativeModel(model_id)
    except Exception as e:
        st.error(f"Erreur IA : {e}")
        st.stop()

# --- 3. INTERFACE ---
st.markdown("<h1 style='text-align:center; color:#ff00ff;'>GH EXPERT PRO</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📟 RÉDACTION MAIL", "📋 GUIDE CHARGES", "⚙️ GESTION"])

# --- ONGLET 1 : RÉDACTION ---
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Infos Locataire")
        if df.empty:
            res = st.text_input("Résidence")
            bat = st.text_input("Bâtiment")
            app = st.text_input("Appartement")
            nom = "Inconnu"
        else:
            res = st.selectbox("Résidence", df["Résidence"].unique())
            filtre = df[df["Résidence"] == res]
            app = st.selectbox("Appartement", filtre["Appartement"].unique())
            nom = filtre[filtre["Appartement"] == app]["Nom"].iloc[0]
            bat = filtre[filtre["Appartement"] == app]["Bâtiment"].iloc[0] if "Bâtiment" in filtre.columns else ""
        
        st.info(f"Occupant : **{nom}**")
        
        # Choix du type de signalement
        type_signalement = st.selectbox("Type de signalement", [
            "1. Technique (Fuite, Panne, Dégradation)",
            "2. Voisinage (Bruit, Incivilité)",
            "3. Travaux / Matériel"
        ])

        email_dest = st.text_input("Email entreprise", "ludoak33@gmail.com")

    with col2:
        st.subheader("📸 Preuve / Photo")
        img = st.camera_input("Prendre la photo")
        
        # Champ pour préciser l'urgence ou le contexte
        contexte_user = st.text_area("Précisions (optionnel)", placeholder="Ex: 3ème fois ce mois, très urgent...")

        if st.button("🚀 GÉNÉRER LE MAIL"):
            if img or contexte_user:
                with st.spinner("Rédaction en cours..."):
                    try:
                        # On crée le prompt adapté au type choisi
                        if "Technique" in type_signalement:
                            prompt = f"""
                            Tu es assistant pour un chargé d'immeuble. Rédige un mail COURT et PROFESSIONNEL.
                            Remplis ce modèle STRICTEMENT. Ne mets pas de sujet, juste le corps du mail.
                            
                            Modèle :
                            "Madame, Monsieur,
                            En qualité de chargé d’immeuble, je vous informe d'une anomalie constatée ce jour sur la résidence {res}.
                            Description du problème :
                            Nature : [Identifie le problème sur la photo ou le contexte]
                            Localisation exacte : {bat}, {app}
                            Urgence : [Évalue l'urgence : Modérée / Haute]
                            Les premières mesures conservatoires ont été prises. Je sollicite l’intervention rapide d'un prestataire.
                            Cordialement,
                            Aniotsbehere Ludovic, Chargé d’immeuble"
                            
                            Photo : {img.name if img else 'Aucune'}
                            Contexte : {contexte_user}
                            """
                        elif "Voisinage" in type_signalement:
                            prompt = f"""
                            Tu es assistant pour un chargé d'immeuble. Rédige un mail COURT.
                            Modèle :
                            "Madame, Monsieur,
                            Je souhaite porter à votre connaissance des faits perturbant la tranquillité des locataires de la résidence {res}.
                            Description : [Résume le problème : nuisances, déchets...]
                            Localisation : {bat}, {app}
                            Une médiation verbale a été tentée. Merci d'acter ce signalement.
                            Respectueusement,
                            Aniotsbehere Ludovic, Chargé d’immeuble"
                            
                            Contexte : {contexte_user}
                            """
                        else: # Travaux
                            prompt = f"""
                            Tu es assistant pour un chargé d'immeuble. Rédige un mail COURT.
                            Modèle :
                            "Madame, Monsieur,
                            Dans le cadre de l’entretien courant de la résidence {res}, j’ai relevé le besoin suivant : [Identifie le besoin].
                            Localisation : {bat}, {app}
                            Ces éléments sont essentiels pour la sécurité/propreté. Merci de confirmer la prise en compte.
                            Cordialement,
                            Aniotsbehere Ludovic, Chargé d’immeuble"
                            
                            Photo : {img.name if img else 'Aucune'}
                            Contexte : {contexte_user}
                            """

                        # Analyse
                        image_pil = Image.open(img) if img else None
                        content = [prompt]
                        if image_pil:
                            content.append(image_pil)
                            
                        reponse = model.generate_content(content)
                        st.session_state['mail_genere'] = reponse.text
                        
                    except Exception as e:
                        st.error(f"Erreur : {e}")
            else:
                st.warning("Prenez une photo ou donnez un contexte.")

        if 'mail_genere' in st.session_state:
            st.markdown("#### 📧 Votre mail prêt à l'envoi")
            st.code(st.session_state['mail_genere'], language='text')
            
            # Préparation du lien mail
            sujet = f"Signalement - {res} - {app}"
            lien = f"mailto:{email_dest}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(st.session_state['mail_genere'])}"
            st.markdown(f"<a href='{lien}' style='background-color:#0078d4; color:white; padding:15px; border-radius:10px; text-decoration:none; display:block; text-align:center; font-weight:bold;'>📧 OUVRIR OUTLOOK / MAIL</a>", unsafe_allow_html=True)

# --- ONGLET 2 : GUIDE ---
with tab2:
    st.subheader("🔍 Qui paie quoi ?")
    st.markdown("- **Locataire** : Joints, ampoules, propreté, petits travaux")
    st.markdown("- **Prestataire** : Chaudière, VMC, ascenseur (contrat)")
    st.markdown("- **Bailleur (GH)** : Gros œuvre, fuites tuyauterie, toiture")

# --- ONGLET 3 : GESTION ---
with tab3:
    st.subheader("Ajouter un locataire")
    st.info("Ajoutez directement les lignes dans le Google Sheet pour mettre à jour la base.")
    st.dataframe(df)
