if st.button("🔍 ANALYSER ET GÉNÉRER LA LETTRE", type="primary", use_container_width=True):
        if not photo:
            st.warning("Ajoutez une photo !")
        else:
            with st.spinner("Analyse par gemini-3-flash-preview..."):
                try:
                    # On configure l'IA pour qu'elle ne bloque pas sur les photos techniques
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    
                    prompt = "Expert GH. Analyse cette photo de bâtiment, décris le problème technique et conclus par CODE_RESULTAT:GH, CODE_RESULTAT:LOC ou CODE_RESULTAT:PREST."
                    
                    img = Image.open(photo)
                    
                    # AJOUT : Paramètres pour éviter le blocage "Safety"
                    response = model.generate_content(
                        [prompt, img],
                        safety_settings={
                            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                        }
                    )
                    
                    # Vérification si l'IA a répondu
                    if response.candidates and response.candidates[0].content.parts:
                        reponse_ia = response.text
                        
                        # Logique de badge
                        type_c = "🏢 CHARGE GH"
                        label_simple = "Charge GH"
                        if "CODE_RESULTAT:LOC" in reponse_ia: 
                            type_c = "🛠️ CHARGE LOCATIVE"; label_simple = "Charge Locative"
                        elif "CODE_RESULTAT:PREST" in reponse_ia: 
                            type_c = "🏗️ CHARGE PRESTATAIRE"; label_simple = "Charge Prestataire"
                        
                        st.divider()
                        st.metric("DÉCISION", type_c)
                        description = reponse_ia.split("CODE_RESULTAT:")[0]
                        st.write(description)
                        
                        # --- GÉNÉRATION DE LA LETTRE ---
                        st.subheader("✉️ Courrier pour la plateforme")
                        lettre = f"""OBJET : Signalement technique - {res_sel} / Appt {appt_sel}\nDATE : {datetime.now().strftime("%d/%m/%Y")}\n\nMadame, Monsieur,\n\nJ'ai constaté le désordre suivant dans le logement de M./Mme {nom_loc} (Appt {appt_sel}) :\n{description.strip()}\n\nApres diagnostic, ce désordre est classé en : {label_simple}.\n\nCordialement,\nL'équipe technique GH."""
                        st.text_area("Texte à copier :", lettre, height=200)
                    else:
                        st.error("L'IA n'a pas pu analyser cette image. Essayez de reprendre la photo avec un angle différent (sans personne dessus).")

                except Exception as e:
                    st.error(f"Erreur : {e}")