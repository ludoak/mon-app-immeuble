import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="GH Expert", layout="wide")

# Connexion sécurisée au Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl="1s") # On force la lecture fraîche

df = load_data()

st.title("GIRONDE HABITAT - GESTION DYNAMIQUE")

tab1, tab2 = st.tabs(["📟 DIAGNOSTIC", "⚙️ GESTION LOCATAIRES"])

with tab1:
    # ... (Ton code de diagnostic habituel)
    st.write("Sélectionnez un locataire et lancez le scan.")
    st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("➕ Ajouter un résident au Google Sheets")
    with st.form("form_ajout"):
        res = st.text_input("Résidence")
        bat = st.text_input("Bâtiment")
        app = st.text_input("Appartement")
        nom = st.text_input("Nom")
        
        if st.form_submit_button("Enregistrer définitivement"):
            new_data = pd.DataFrame([{"Résidence": res, "Bâtiment": bat, "Appartement": app, "Nom": nom}])
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(data=updated_df) # ICI ÇA VA ÉCRIRE POUR DE VRAI
            st.success("C'est enregistré dans Google Sheets !")
            st.rerun()
