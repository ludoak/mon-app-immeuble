import streamlit as st
from datetime import date
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# Configuration de la page
st.set_page_config(page_title="ImmoCheck Pro IA", page_icon="📸", layout="wide")

# --- CONNEXION GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    try:
        return conn.read(worksheet="Locataires", ttl="0")
    except:
        return pd.DataFrame(columns=["Logement", "Nom"])

def sauvegarder_locataire(logement, nom):
    df = charger_donnees()
    if logement in df['Logement'].values:
        df.loc[df['Logement'] == logement, 'Nom'] = nom
    else:
        new_row = pd.DataFrame({"Logement": [logement], "Nom": [nom]})
        df = pd.concat([df, new_row], ignore_index=True)
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

def supprimer_locataire(logement):
    df = charger_donnees()
    df = df[df['Logement'] != logement]
    conn.update(worksheet="Locataires", data=df)
    st.cache_data.clear()

# --- CONFIGURATION GEMINI (IA) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_vision = genai.GenerativeModel('gemini-pro-vision')
except Exception as e:
    st.error(f"Erreur de configuration Gemini : {e}. Assurez-vous que GEMINI_API_KEY est dans les Secrets.")
    model_vision = None

# --- CHARGEMENT DES DONNÉES ---
df_base = charger_donnees()

st.title("🏢 Rapport d'Intervention ImmoCheck Pro IA")

# --- BARRE LATÉRALE : GESTION DES LOCATAIRES ---
with st.sidebar:
    st.header("👥 Base Locataires")
    
    tab_ajout, tab_suppr = st.tabs(["➕ Ajouter", "🗑️ Supprimer"])
    
    with tab_ajout:
        res_a = st.selectbox("Résidence", ["Canterane", "La Dussaude"], key="res_add")
        if res_a == "Canterane":
            bat_a = st.radio("Bâtiment", ["A", "B"], horizontal=True, key="bat_add")
            app_a = st.text_input("N° Appt", key="app_add")
            cle_loc = f"Canterane - Bat {bat_a} - Appt {app_a}"
        else:
            app_a = st.number_input("N° Appt", 1, 95, key="app_add_duss")
            cle_loc = f"La Dussaude - Appt {app_a}"
        
        nom_a = st.text_input("Nom du locataire", key="nom_add")
        if st.button("💾 Enregistrer le locataire"):
            sauvegarder_locataire(cle_loc, nom_a)
            st.success("Enregistré dans Google Sheets !")
            st.rerun()

    with tab_suppr:
        if not df_base.empty:
            log_a_supprimer = st.selectbox("Choisir le logement à vider", df_base['Logement'].tolist())
            if st.button("❌ Confirmer suppression"):
                supprimer_locataire(log_a_supprimer)
                st.warning(f"Locataire de {log_a_supprimer} supprimé")
                st.rerun()
        else:
            st.write("La base est vide.")

# --- FORMULAIRE PRINCIPAL ---
st.subheader("📝 Nouveau Constat avec IA")

# Sélection du logement HORS du formulaire pour la recherche instantanée
col1, col2 = st.columns(2)
with col1:
    res_search = st.selectbox("📍 Résidence", ["Canterane", "La Dussaude"], key="res_s")
    if res_search == "Canterane":
        bat_s = st.radio("Bâtiment", ["A", "B"], horizontal=True, key="bat_s")
        app_s = st.text_input("N° Appt", key="app_s")
        id_logement = f"Canterane - Bat {bat_s} - Appt {app_s}"
    else:
        app_s = st.number_input("N° Appt", 1, 95, key="app_s_duss")
        id_logement = f"La Dussaude - Appt {app_s}"

# RECHERCHE DU NOM (Instantane)
nom_locataire = ""
if not df_base.empty and id_logement in df_base['Logement'].values:
    nom_locataire = df_base.loc[df_base['Logement'] == id_logement, 'Nom'].values[0]

with col2:
    date_visite = st.date_input("📅 Date", format="DD/MM/YYYY")
    st.text_input("👤 Locataire (auto)", value=nom_locataire, disabled=True)

# Début du formulaire pour le reste des infos
with st.form("rapport_technique_ia"):
    st.markdown("---")
    st.write("### 📸 Prenez une photo du problème :")
    uploaded_file = st.camera_input("Prendre une photo") # Utilise la caméra du téléphone
    
    observations_ia = ""
    if uploaded_file is not None:
        # Afficher l'image prise
        st.image(uploaded_file, caption="Photo du problème", use_column_width=True)
        
        # Préparer l'image pour Gemini
        image_bytes = uploaded_file.getvalue()
        image_pil = Image.open(io.BytesIO(image_bytes))

        # Appel à Gemini pour l'analyse
        if st.button("🔍 Analyser la photo avec l'IA"):
            if model_vision:
                with st.spinner("Analyse en cours par l'IA..."):
                    try:
                        prompt = "Décris en français le problème visible sur cette photo pour un rapport d'intervention technique. Sois concis et professionnel. Exemple: 'Fuite d'eau sous l'évier', 'Prise électrique endommagée', 'Traces d'humidité sur le mur', 'Joint de baignoire à refaire'."
                        response = model_vision.generate_content([prompt, image_pil])
                        observations_ia = response.text
                        st.session_state.observations_ia = observations_ia # Pour conserver le texte
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse IA : {e}")
                        st.session_state.observations_ia = "Impossible d'analyser la photo."
            else:
                st.warning("L'IA Gemini n'est pas configurée.")
                st.session_state.observations_ia = "IA non disponible."

    # Afficher le résultat de l'IA (ou vide si pas de photo/analyse)
    observations_finales = st.text_area("🗒️ Observations détaillées (modifiable ou IA)", 
                                        value=st.session_state.get('observations_ia', ''), # Récupère le texte de l'IA ou vide
                                        height=150)

    st.markdown("---")
    urgence = st.select_slider("🚦 Urgence", options=["Faible", "Moyenne", "Haute"])
    
    type_probleme = st.selectbox("🛠️ Type de problème", [
        "Plomberie (Fuite, robinet, chasse d'eau)",
        "Chauffage / Eau Chaude",
        "Électricité (Prise, tableau, éclairage)",
        "VMC / Ventilation",
        "Serrurerie / Porte",
        "Infiltration / Humidité",
        "Autre"
    ])
    
    soumettre = st.form_submit_button("🚀 GÉNÉRER LE RAPPORT")

# --- AFFICHAGE DU MESSAGE ---
if soumettre:
    st.success("Rapport généré ! Copiez le texte ci-dessous :")
    
    msg = f"""*RAPPORT D'INTERVENTION* 🏢
----------------------------------
📍 *Lieu :* {id_logement}
👤 *Locataire :* {nom_locataire if nom_locataire else "Non renseigné"}
📅 *Date :* {date_visite.strftime('%d/%m/%Y')}
🚦 *Urgence :* {urgence}

🛠️ *Type :* {type_probleme}
📝 *Constat :* {observations_finales}
----------------------------------"""
    
    st.code(msg, language="text")
    st.info("💡 Vous pouvez maintenant copier ce texte et l'envoyer par SMS ou Email.")
