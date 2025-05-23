import streamlit as st
import pandas as pd
import os

def app():
    st.title("🆘 Aide Utilisateur")

    st.markdown("""
    Bienvenue dans l'application d'estimation de l'héritabilité.

    ### 📁 Fichiers acceptés :
    - `.xlsx` : Fichiers Excel
    - `.csv` : Fichiers séparés par des virgules

    ### 🧾 Structure recommandée :
    Le fichier doit contenir des colonnes telles que :
    - `NNI`, `Date naissance`, `Race`, `Sexe`
    - `Rendement laitier`, `Taux MG`, `Taux Prot`
    - `Mère NNI`, `Père NNI` (ou équivalent)

    ### 📥 Télécharger un exemple :
    Cliquez sur le bouton ci-dessous pour obtenir un fichier exemple :
    """)

    # Charger l'exemple
    chemin_fichier = "assets/exemple_fichier.xlsx"
    try:
        with open(f"streamlit_app/{chemin_fichier}", "rb") as f:
            st.download_button("📄 Télécharger l'exemple (.xlsx)", f, file_name="exemple_fichier.xlsx")
    except FileNotFoundError:
        st.warning(f"Le fichier d'exemple {chemin_fichier} n'a pas été trouvé.")

    st.title("🆘 Aide & Exemple de fichier")
    st.markdown("""
    - Votre fichier doit contenir au minimum les colonnes suivantes : ID, rendement, grasse, prot, etc.
    - Les colonnes peuvent être en majuscules ou minuscules.
    - Les identifiants doivent être uniques par animal.
    - Les valeurs manquantes seront ignorées automatiquement.

    **Exemple de structure minimale :**
    | ID | rendement | grasse | prot | environnement |
    |----|-----------|--------|------|---------------|
    | A1 | 5000      | 38     | 32   | Zone1         |
    | A2 | 4200      | 35     | 30   | Zone2         |
    """)
