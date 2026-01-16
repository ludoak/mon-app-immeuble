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
st.caption("Modèle : gemini-3-flash-preview")
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
    note_facultative = st.text_input("Détail supplémentaire (facultatif)")

# --- 5. LOGIQUE D'ANALYSE AUTOMATIQUE ---
if st.button("🔍 GÉNÉRER LE RAPPORT ET LA LETTRE", type="primary", use_container_width=True):
    if not photo:
        st.warning("⚠️ Merci de prendre une photo pour lancer l'analyse automatique.")
    else:
        with st.spinner("L'IA examine la photo..."):
            try:
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # Prompt sécurisé pour éviter les erreurs de badge
                prompt_global = f"""
                Tu es l'expert technique de Gironde Habitat.
                Regarde cette photo et :
                1. Décris précisément le problème technique.
                2. Justifie selon les règles d'entretien.
                3. Conclus EXCLUSIVEMENT par l'un de ces trois codes en fin de réponse : 
                   CODE_RESULTAT:GH (si c'est pour Gironde Habitat)
                   CODE_RESULTAT:LOC (si c'est une charge locative)
                   CODE_RESULTAT:PREST (si c'est pour un prestataire)
                """
                
                img = Image.open(photo)
                res = model.generate_content([prompt_global, img])
                reponse_ia = res.text
                
                # --- LOGIQUE DE DÉTECTION DU BADGE ---
                type_charge = "🏢 CHARGE GH"
                label_lettre = "CHARGE GH"
                
                if "CODE_RESULTAT:LOC" in reponse_ia:
                    type_charge = "🛠️ CHARGE LOCATIVE"
                    label_lettre = "CHARGE LOCATIVE"
                elif "CODE_RESULTAT:PREST" in reponse_ia:
                    type_charge = "🏗️ CHARGE PRESTATAIRE"
                    label_lettre = "CHARGE PRESTATAIRE"
                elif "CODE_RESULTAT:GH" in reponse_ia:
                    type_charge = "🏢 CHARGE GH"
                    label_lettre = "CHARGE GH"
                
                # Nettoyage du texte pour l'affichage
                affichage_texte = reponse_ia.split("CODE_RESULTAT:")[0]

                # --- AFFICHAGE ---
                st.markdown("---")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.metric("TYPE DE CHARGE", type_charge)
                with c2:
                    st.subheader("📋 Analyse Technique")
                    st.write(affichage_texte)
                
                # --- GÉNÉRATION DU COURRIER ---
                st.markdown("---")
                st.subheader("✉️ Courrier pour la plateforme")
                
                date_jour = datetime.now().strftime("%d/%m/%Y")
                lettre = f"""OBJET : Signalement technique - {res_sel} / Appt {appt_sel}
DATE : {date_jour}

Madame, Monsieur,

J'ai constaté le désordre suivant dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :
{affichage_texte.split('.')[0]}.

Après diagnostic, ce désordre est classé en : {label_lettre}.

Merci de prendre les dispositions nécessaires.

Cordialement,
L'équipe technique GH."""

                st.text_area("Texte à copier :", lettre, height=200)
                
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")

st.markdown("---")
st.caption("GH-Auto-Pilot : Plus rien à saisir, l'IA s'occupe de tout.")