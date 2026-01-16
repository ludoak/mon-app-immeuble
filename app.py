import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GH Diagnostic & Courrier", layout="wide")

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
st.title("🚀 GH Diagnostic & Signalement")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Localisation")
    res_sel = st.selectbox("Sélectionner la Résidence", sorted(df["Résidence"].unique()))
    df_res = df[df["Résidence"] == res_sel]
    appt_sel = st.selectbox("N° Appartement", sorted(df_res["Appartement"].unique()))
    nom_loc = df_res[df_res["Appartement"] == appt_sel]["Nom"].iloc[0]
    st.success(f"👤 Locataire : **{nom_loc}**")

with col2:
    st.subheader("📸 Constat")
    photo = st.file_uploader("Photo du désordre", type=["jpg", "png", "jpeg"])
    note = st.text_area("Description rapide pour la plateforme")

# --- 5. ANALYSE ET GÉNÉRATION ---
if st.button("🔍 ANALYSER ET PRÉPARER LE COURRIER", type="primary", use_container_width=True):
    if not note:
        st.warning("⚠️ Décrivez le problème pour générer le rapport.")
    else:
        with st.spinner("Analyse par gemini-3-flash-preview..."):
            try:
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # Prompt pour l'analyse technique + décision de charge
                prompt_analyse = f"""
                En tant qu'expert technique GH, analyse ce problème : '{note}'.
                1. Détermine la nature du problème.
                2. Décide si c'est : 'CHARGE LOCATIVE', 'CHARGE GH' ou 'CHARGE PRESTATAIRE'.
                3. Justifie brièvement.
                """
                
                if photo:
                    img = Image.open(photo)
                    res = model.generate_content([prompt_analyse, img])
                else:
                    res = model.generate_content(prompt_analyse)
                
                # --- AFFICHAGE DU RÉSULTAT ---
                st.markdown("---")
                
                # Bloc "Type de Charge" bien visible
                analyse_texte = res.text
                type_charge = "À DÉTERMINER"
                if "LOCATIVE" in analyse_texte.upper(): type_charge = "🛠️ CHARGE LOCATIVE"
                elif "PRESTATAIRE" in analyse_texte.upper(): type_charge = "🏗️ CHARGE PRESTATAIRE"
                else: type_charge = "🏢 CHARGE GH (Bailleur)"
                
                st.metric(label="Décision de prise en charge :", value=type_charge)
                
                st.subheader("📋 Rapport Technique")
                st.write(analyse_texte)
                
                # --- GÉNÉRATION DE LA LETTRE ---
                st.markdown("---")
                st.subheader("✉️ Modèle de courrier pour la plateforme")
                
                date_jour = datetime.now().strftime("%d/%m/%Y")
                
                lettre = f"""
                OBJET : Signalement technique - Résidence {res_sel} - Appt {appt_sel}
                DATE : {date_jour}
                
                Madame, Monsieur,
                
                Je vous informe d'un désordre technique constaté ce jour dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) au sein de la résidence {res_sel}.
                
                Description du problème : 
                {note}
                
                Après diagnostic sur place, ce désordre semble relever d'une : {type_charge}.
                
                Merci de faire le nécessaire pour déclencher l'intervention ou informer le locataire de ses obligations.
                
                Cordialement,
                L'équipe technique GH.
                """
                
                st.text_area("Copiez le texte ci-dessous :", lettre, height=300)
                st.info("💡 Vous pouvez copier ce texte et l'envoyer directement par mail ou sur la plateforme technique.")
                
            except Exception as e:
                st.error(f"Erreur : {e}")

st.markdown("---")
st.caption("Application Terrain GH - Expertise Instantanée")