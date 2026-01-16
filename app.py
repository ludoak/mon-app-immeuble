import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic Auto", layout="wide")

# --- 2. CONFIGURATION DE L'IA ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("⚠️ Clé API manquante dans les Secrets !")

# --- 3. BASE DE DONNÉES LOCATAIRES ---
data = {
    "Résidence": ["Canterane", "Canterane", "La Dussaude", "La Dussaude", "Canterane"],
    "Appartement": ["10", "40", "95", "64", "103"],
    "Nom": ["lolo", "Aniotsbehere", "zezette", "kiki", "Dédé"]
}
df = pd.DataFrame(data)

# --- 4. INTERFACE ---
st.title("🚀 GH Auto-Signalement")
st.caption("Analyse automatique par photo - Modèle : gemini-3-flash-preview")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Localisation")
    res_sel = st.selectbox("Résidence", sorted(df["Résidence"].unique()))
    df_res = df[df["Résidence"] == res_sel]
    appt_sel = st.selectbox("Appartement", sorted(df_res["Appartement"].unique()))
    nom_loc = df_res[df_res["Appartement"] == appt_sel]["Nom"].iloc[0]
    st.info(f"👤 Locataire : **{nom_loc}**")

with col2:
    st.subheader("📸 Preuve visuelle")
    photo = st.file_uploader("Prendre/Joindre la photo", type=["jpg", "png", "jpeg"])
    # Note optionnelle au cas où tu veuilles préciser un détail, mais pas obligatoire
    note_facultative = st.text_input("Détail supplémentaire (facultatif)")

# --- 5. LOGIQUE D'ANALYSE AUTOMATIQUE ---
if st.button("🔍 GÉNÉRER LE RAPPORT ET LA LETTRE", type="primary", use_container_width=True):
    if not photo:
        st.warning("⚠️ Merci de prendre une photo pour lancer l'analyse automatique.")
    else:
        with st.spinner("L'IA examine la photo et prépare tout..."):
            try:
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # Le Prompt qui force l'IA à TOUT faire
                prompt_global = f"""
                Tu es l'expert technique de Gironde Habitat.
                Regarde cette photo et :
                1. Décris précisément le problème technique constaté.
                2. Détermine le type de charge : 'CHARGE LOCATIVE', 'CHARGE GH' ou 'CHARGE PRESTATAIRE'.
                3. Justifie selon les règles d'entretien des logements sociaux.
                
                Informations complémentaires si fournies : {note_facultative}
                """
                
                img = Image.open(photo)
                res = model.generate_content([prompt_global, img])
                reponse_ia = res.text
                
                # --- AFFICHAGE DE LA CHARGE ---
                st.markdown("---")
                type_charge = "🏢 CHARGE GH" # Par défaut
                if "LOCATIVE" in reponse_ia.upper(): type_charge = "🛠️ CHARGE LOCATIVE"
                elif "PRESTATAIRE" in reponse_ia.upper(): type_charge = "🏗️ CHARGE PRESTATAIRE"
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("TYPE DE CHARGE", type_charge)
                with c2:
                    st.subheader("📋 Analyse Technique")
                    st.write(reponse_ia)
                
                # --- GÉNÉRATION AUTOMATIQUE DU COURRIER ---
                st.markdown("---")
                st.subheader("✉️ Courrier prêt à l'envoi")
                
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                # On demande à l'IA de résumer le problème en une phrase pour l'objet
                prompt_lettre = f"Résume ce problème technique en 5 mots maximum pour un objet de mail : {reponse_ia}"
                objet_court = model.generate_content(prompt_lettre).text
                
                lettre = f"""OBJET : {objet_court.strip()} - {res_sel} / Appt {appt_sel}
DATE : {date_jour}

Madame, Monsieur,

Lors d'une visite à la résidence {res_sel}, j'ai constaté le désordre suivant dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :

{reponse_ia.split('.')[0]}.

Après diagnostic visuel, ce désordre est classé en : {type_charge}.

Merci de prendre les dispositions nécessaires.

Cordialement,
L'équipe technique GH."""

                st.text_area("Copier pour la plateforme :", lettre, height=250)
                st.button("✅ Copié dans le presse-papier (Simulation)") # Note : Streamlit ne permet pas le vrai copier-coller auto sans composants complexes
                
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")

st.markdown("---")
st.caption("GH-Auto-Pilot : Plus rien à saisir, l'IA s'occupe de tout.")