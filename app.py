import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import urllib.parse
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="GH Expert Pro", layout="wide", initial_sidebar_state="expanded")

# --- BARRE LATÉRALE : ANNUAIRE D'URGENCE ---
with st.sidebar:
    st.title("📞 URGENCE & CONTACTS")
    st.markdown("Cliquez pour appeler :")
    st.markdown("---")
    st.markdown(f"🚒 **Pompiers** : [18](tel:18)")
    st.markdown(f"👮 **Police** : [17](tel:17)")
    st.markdown(f"🚑 **SAMU** : [15](tel:15)")
    st.markdown("---")
    st.markdown(f"🔧 **Astreinte Technique GH** : [06 00 00 00 00](tel:0600000000)") 
    st.markdown(f"🛡️ **Gardiennage / Sécurité** : [06 00 00 00 00](tel:0600000000)")
    st.divider()
    st.caption("GH Expert Pro v2.1")

# --- 1. CONNEXION GOOGLE SHEETS ---
def get_gspread_client():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["connections"]["gsheets"]["credentials"]
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client, spreadsheet_url
    except Exception as e:
        st.error(f"Erreur de connexion Google : {e}")
        return None, None

def load_data():
    client, url = get_gspread_client()
    if not client: return pd.DataFrame(columns=["Résidence", "Bâtiment", "Appartement", "Nom"])
    try:
        sh = client.open_by_url(url)
        worksheet = sh.sheet1
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Erreur lecture sheet : {e}")
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
        source = st.radio("Source :", ["📷 Caméra", "🖼️ Galerie"], horizontal=True)
        
        img = None
        if source == "📷 Caméra":
            img = st.camera_input("Prendre une photo")
        else:
            img = st.file_uploader("Choisir une image", type=["jpg", "png", "jpeg"])
            
        contexte_user = st.text_area("Précisions (optionnel)", placeholder="Ex: 3ème fois ce mois...")
        
        st.markdown("---")
        st.markdown("**✅ Validation avant signalement**")
        c1, c2 = st.columns(2)
        with c1:
            check_secu = st.checkbox("Lieux sécurisés")
        with c2:
            check_info = st.checkbox("Locataire informé")

        if st.button("🚀 ANALYSER ET RÉDIGER", type="primary"):
            if img or contexte_user:
                with st.spinner("Analyse en cours..."):
                    try:
                        image_pil = Image.open(img) if img else None
                        
                        # --- ANALYSE PURE ---
                        prompt_analyse = """
                        Tu es expert technique pour un bailleur social.
                        Analyse cette photo et le contexte.
                        1. Identifie le problème.
                        2. Détermine QUI PAIE : LOCATAIRE (entretien courant), BAILLEUR (vétusté), ou PRESTATAIRE (contrat).
                        
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
                        st.session_state['contexte_save'] = contexte_user
                        
                        # --- RÉDACTION MAIL INTELLIGENTE ---
                        loc_text = f"Bat {bat}, Appartement {app}"
                        
                        # On passe l'analyse au prompt du mail pour qu'il s'adapte
                        if "Technique" in type_signalement:
                            prompt_mail = f"""
                            Tu es assistant de rédaction. Rédige un mail pro très court.
                            Commence par "Bonjour."
                            
                            Voici les infos :
                            - Résidence : {res}
                            - Localisation : {loc_text}
                            - Analyse de l'expert : {st.session_state['analyse']}
                            
                            Instructions pour la conclusion :
                            - Si le responsable est le LOCATAIRE : Écris "Ce problème relève de l'entretien locatif. Merci de rappeler au locataire ses obligations."
                            - Si le responsable est le BAILLEUR ou PRESTATAIRE : Écris "Je sollicite l’intervention d'un technicien."
                            
                            Signe : Aniotsbehere Ludovic
                            """
                        elif "Voisinage" in type_signalement:
                            prompt_mail = f"""
                            Rédige un mail pro très court. Commence par "Bonjour."
                            "Madame, Monsieur, Bonjour. Faits perturbants sur résidence {res}.
                            Description : [Résume]
                            Localisation : {loc_text}
                            Médiation tentée. Merci d'acter.
                            Respectueusement, Aniotsbehere Ludovic"
                            Contexte : {contexte_user}
                            """
                        else:
                            prompt_mail = f"""
                            Rédige un mail pro très court. Commence par "Bonjour."
                            "Madame, Monsieur, Bonjour. Besoin identifié sur résidence {res}.
                            Besoin : [Décris]
                            Localisation : {loc_text}
                            Merci de confirmer.
                            Cordialement, Aniotsbehere Ludovic"
                            Contexte : {contexte_user}
                            """

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
            
            if st.button("💾 Sauvegarder dans l'historique"):
                try:
                    client, url = get_gspread_client()
                    sh = client.open_by_url(url)
                    try:
                        wks_hist = sh.worksheet("Historique")
                    except gspread.exceptions.WorksheetNotFound:
                        wks_hist = sh.add_worksheet(title="Historique", rows="100", cols="5")
                        wks_hist.append_row(["Date", "Résidence", "Appartement", "Problème", "Responsable"])
                    
                    resp = "Inconnu"
                    if "Responsable" in st.session_state['analyse']:
                        resp = st.session_state['analyse'].split("**Responsable**")[1].split("\n")[0].strip()
                    
                    now = datetime.now().strftime("%d/%m/%Y %H:%M")
                    wks_hist.append_row([now, res, app, st.session_state.get('contexte_save', 'Photo'), resp])
                    st.success("✅ Intervention archivée !")
                except Exception as e:
                    st.error(f"Erreur d'archivage : {e}")
            
            st.divider()

        if 'mail_genere' in st.session_state:
            st.markdown("#### 📧 Mail à envoyer")
            st.code(st.session_state['mail_genere'], language='text')
            
            sujet = f"Signalement - {res} - Bat {bat} Appt {app}"
            lien = f"mailto:{email_dest}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(st.session_state['mail_genere'])}"
            st.markdown(f"<a href='{lien}' style='background-color:#0078d4; color:white; padding:15px; border-radius:10px; text-decoration:none; display:block; text-align:center; font-weight:bold;'>📧 OUVRIR OUTLOOK / MAIL</a>", unsafe_allow_html=True)

# --- ONGLET 2 : PHOTOS ---
with tab2:
    st.subheader("🛠️ Suivi de travaux")
    st.info("Importez vos photos Avant / Après.")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**📷 AVANT**")
        src_av = st.radio("Source:", ["Caméra", "Galerie"], key="src_av", horizontal=True)
        img_av = st.camera_input("Photo AVANT", key="cam_av") if src_av == "Caméra" else st.file_uploader("Fichier", key="file_av")
        if img_av:
            st.download_button("⬇️ Télécharger", img_av, file_name=f"AVANT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            
    with c2:
        st.markdown("**📷 APRÈS**")
        src_ap = st.radio("Source:", ["Caméra", "Galerie"], key="src_ap", horizontal=True)
        img_ap = st.camera_input("Photo APRÈS", key="cam_ap") if src_ap == "Caméra" else st.file_uploader("Fichier", key="file_ap")
        if img_ap:
            st.download_button("⬇️ Télécharger", img_ap, file_name=f"APRES_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")

# --- ONGLET 3 : GUIDE ---
with tab3:
    st.subheader("🔍 Qui paie quoi ?")
    st.markdown("- **Locataire** : Joints, ampoules, propreté, aération")
    st.markdown("- **Prestataire** : Chaudière, VMC, ascenseur")
    st.markdown("- **Bailleur (GH)** : Gros œuvre, infiltrations, toiture")

# --- ONGLET 4 : GESTION ---
with tab4:
    st.subheader("Ajouter un locataire")
    st.info("Les locataires sont dans l'onglet 1 du Sheet. L'historique est dans l'onglet 'Historique'.")
    st.dataframe(df)
