import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

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

# On remet les 4 onglets
tab1, tab2, tab3, tab4 = st.tabs(["📟 DIAGNOSTIC & MAIL", "📸 PHOTOS", "📋 GUIDE CHARGES", "⚙️ GESTION"])

# --- ONGLET 1 : DIAGNOSTIC & MAIL ---
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
        
        type_signalement = st.selectbox("Type de signalement", [
            "1. Technique (Fuite, Panne, Dégradation)",
            "2. Voisinage (Bruit, Incivilité)",
            "3. Travaux / Matériel"
        ])

        email_dest = st.text_input("Email entreprise", "ludoak33@gmail.com")

    with col2:
        st.subheader("📸 Preuve / Photo")
        img = st.camera_input("Prendre la photo")
        contexte_user = st.text_area("Précisions (optionnel)", placeholder="Ex: 3ème fois ce mois...")

        if st.button("🚀 ANALYSER ET RÉDIGER"):
            if img or contexte_user:
                with st.spinner("Analyse en cours..."):
                    try:
                        image_pil = Image.open(img) if img else None
                        
                        # --- ÉTAPE 1 : ANALYSE PURE ---
                        prompt_analyse = """
                        Tu es expert technique pour un bailleur social.
                        Analyse cette photo et le contexte.
                        1. Identifie le problème.
                        2. Détermine QUI PAIE : LOCATAIRE (entretien courant, joints, ampoules), BAILLEUR (vétusté, gros oeuvre), ou PRESTATAIRE (contrat maintenance).
                        
                        Réponds par :
                        **Problème** : ...
                        **Responsable** : ...
                        **Justification** : ...
                        """
                        
                        content_analyse = [prompt_analyse]
                        if image_pil: content_analyse.append(image_pil)
                        if contexte_user: content_analyse.append(f"Contexte : {contexte_user}")
                        
                        analyse = model.generate_content(content_analyse)
                        st.session_state['analyse'] = analyse.text
                        
                        # --- ÉTAPE 2 : RÉDACTION DU MAIL ---
                        loc_text = f"Bat {bat}, Appartement {app}"
                        
                        if "Technique" in type_signalement:
                            prompt_mail = f"""
                            Rédige un mail professionnel très court.
                            Ne mets pas de titre "En qualité de...". Commence directement par "Bonjour."
                            
                            Contenu :
                            "Madame, Monsieur,
                            Bonjour.
                            Je vous informe d'une anomalie constatée ce jour sur la résidence {res}.
                            Description du problème :
                            Nature : [Décris le problème brièvement]
                            Localisation exacte : {loc_text}
                            Urgence : [Modérée ou Haute]
                            Les premières mesures conservatoires ont été prises. Je sollicite l’intervention rapide d'un prestataire.
                            Cordialement,
                            Aniotsbehere Ludovic"
                            
                            Contexte à utiliser : {contexte_user}
                            """
                        elif "Voisinage" in type_signalement:
                            prompt_mail = f"""
                            Rédige un mail professionnel très court.
                            Commence par "Bonjour."
                            
                            Contenu :
                            "Madame, Monsieur,
                            Bonjour.
                            Je souhaite porter à votre connaissance des faits perturbant la tranquillité des locataires de la résidence {res}.
                            Description : [Résume le problème]
                            Localisation : {loc_text}
                            Une médiation verbale a été tentée. Merci d'acter ce signalement.
                            Respectueusement,
                            Aniotsbehere Ludovic"
                            
                            Contexte : {contexte_user}
                            """
                        else: # Travaux
                            prompt_mail = f"""
                            Rédige un mail professionnel très court.
                            Commence par "Bonjour."
                            
                            Contenu :
                            "Madame, Monsieur,
                            Bonjour.
                            Dans le cadre de l’entretien courant de la résidence {res}, j’ai relevé le besoin suivant : [Identifie le besoin].
                            Localisation : {loc_text}
                            Merci de confirmer la prise en compte.
                            Cordialement,
                            Aniotsbehere Ludovic"
                            
                            Contexte : {contexte_user}
                            """

                        if image_pil:
                            prompt_mail += "\n\nVoici ce que montre la photo : " + analyse.text

                        mail = model.generate_content(prompt_mail)
                        st.session_state['mail_genere'] = mail.text
                        
                    except Exception as e:
                        st.error(f"Erreur : {e}")
            else:
                st.warning("Prenez une photo ou donnez un contexte.")

        # --- AFFICHAGE DES RÉSULTATS ---
        if 'analyse' in st.session_state:
            st.markdown("#### 🔍 Analyse Expert (Pour vous)")
            st.info(st.session_state['analyse'])
            st.divider()

        if 'mail_genere' in st.session_state:
            st.markdown("#### 📧 Mail à envoyer (Pour l'entreprise)")
            st.code(st.session_state['mail_genere'], language='text')
            
            sujet = f"Signalement - {res} - Bat {bat} Appt {app}"
            lien = f"mailto:{email_dest}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(st.session_state['mail_genere'])}"
            st.markdown(f"<a href='{lien}' style='background-color:#0078d4; color:white; padding:15px; border-radius:10px; text-decoration:none; display:block; text-align:center; font-weight:bold;'>📧 OUVRIR OUTLOOK / MAIL</a>", unsafe_allow_html=True)

# --- ONGLET 2 : PHOTOS (GALERIE AVANT/APRÈS) ---
with tab2:
    st.subheader("🛠️ Suivi de travaux (Preuves visuelles)")
    st.info("Prenez vos photos pour constituer un dossier avant/après.")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**📷 AVANT INTERVENTION**")
        img_av = st.camera_input("Photo AVANT", key="cam_av")
        if img_av:
            st.download_button(
                label="⬇️ Télécharger la photo AVANT",
                data=img_av,
                file_name=f"AVANT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                mime="image/jpeg"
            )
            
    with c2:
        st.markdown("**📷 APRÈS INTERVENTION**")
        img_ap = st.camera_input("Photo APRÈS", key="cam_ap")
        if img_ap:
            st.download_button(
                label="⬇️ Télécharger la photo APRÈS",
                data=img_ap,
                file_name=f"APRES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                mime="image/jpeg"
            )

# --- ONGLET 3 : GUIDE ---
with tab3:
    st.subheader("🔍 Qui paie quoi ?")
    st.markdown("- **Locataire** : Joints, ampoules, propreté, aération (moisissures surface)")
    st.markdown("- **Prestataire** : Chaudière, VMC, ascenseur")
    st.markdown("- **Bailleur (GH)** : Gros œuvre, infiltrations, toiture")

# --- ONGLET 4 : GESTION ---
with tab4:
    st.subheader("Ajouter un locataire")
    st.info("Ajoutez les lignes dans le Google Sheet pour mettre à jour la base.")
    st.dataframe(df)
