import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from streamlit_option_menu import option_menu
import importlib
import datetime
from scripts.nettoyage import charger_fichier_universel

# Mapping entre noms de page et fichiers réels (compatibilité noms avec emoji)
pages_modules = {
    "Exploration": "2_🔍_Exploration",
    "Modélisation": "3_📊_Modelisation",
    "Rapport": "4_📄_Rapport",
    "Aide": "1_🆘_Aide",
    "Analyse IA": "4_👁️_Agent_IA"
}

st.set_page_config(layout="wide", page_title="Analyse Animale")

# Menu latéral
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1998/1998613.png", width=100)
    st.title("Menu Navigation")
    # Thème utilisateur
    theme = st.radio(" Thème", ["Clair", "Sombre"], index=0, horizontal=True)
    st.session_state['theme'] = theme
    page = option_menu("Navigation", ["Exploration", "Modélisation", "Rapport", "Aide", "Analyse IA"], icons=['table', 'graph-up', 'file-earmark-pdf', 'info-circle', 'eye'])
    st.markdown("---")
    uploaded_file = st.file_uploader(" Déposez votre fichier (.xlsx ou .csv)", type=["xlsx", "csv"])
    if uploaded_file:
        st.session_state['df'] = charger_fichier_universel(uploaded_file)
        st.success("Fichier chargé avec succès !")
        st.dataframe(st.session_state['df'].head())
    elif 'df' not in st.session_state:
        st.warning("Aucun fichier chargé. Allez dans la page Aide si besoin.")
    st.markdown("---")
    st.write(" **Utilisateur :**", os.getenv('USERNAME', 'Invité'))
    st.write(f" **Heure locale :** {datetime.datetime.now().strftime('%H:%M:%S')}")

# Import dynamique du module de page sélectionné
module_name = pages_modules.get(page)
if module_name:
    module = importlib.import_module(f"pages.{module_name}")
    # Appelle la fonction app() de chaque page
    if hasattr(module, "app"):
        module.app()
    else:
        st.error("La page sélectionnée n'est pas correctement structurée (fonction app() manquante).")
else:
    st.error("Page non trouvée.")
