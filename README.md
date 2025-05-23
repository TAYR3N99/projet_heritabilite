# Estimation de l'héritabilité des caractères de production : (rendement laitier, taux de matière grasse et protéique)

Ce projet propose une solution automatisée pour estimer l'héritabilité de caractères de production (rendement laitier, matière grasse, protéines) chez les bovins laitiers à partir de fichiers Excel (.xlsx) ou CSV (.csv). L'objectif est de remplacer les méthodes manuelles par un pipeline automatisé de traitement, modélisation, visualisation et génération de rapports.

## Fonctionnalités principales
- **Importation intelligente** de fichiers Excel/CSV
- **Détection automatique** des colonnes pertinentes (identifiant animal, lactation, production)
- **Nettoyage, validation et prétraitement** des données
- **Modélisation statistique** (modèles linéaires mixtes via statsmodels)
- **Modélisation machine learning** (régression linéaire, Random Forest via scikit-learn)
- **Calcul et interprétation de l'héritabilité (h²)**
- **Visualisation interactive** (matplotlib, seaborn, plotly)
- **Génération automatique de rapport PDF** (FPDF)
- **Interface web locale** via Streamlit

## Structure du projet
- `scripts/` : fonctions de nettoyage, modélisation, génération de rapport
- `models/` : implémentations Random Forest et régression linéaire
- `streamlit_app/` : application web interactive (entrée principale : `main.py`)
- `pages/` : pages modulaires pour Streamlit (exploration, modélisation, rapport, aide)
- `data/` : fichiers de données d'exemple (bruts et nettoyés)
- `requirements.txt` : dépendances Python

## Démarrage rapide
```bash
pip install -r requirements.txt
streamlit run streamlit_app/main.py
```

## Utilisation
1. Lancez l'application Streamlit (voir ci-dessus).
2. Importez votre fichier de données (`.xlsx` ou `.csv`).
3. Explorez et visualisez vos données dans l'onglet "Exploration".
4. Lancez la modélisation et l'estimation de l'héritabilité dans "Modélisation".
5. Générez un rapport PDF complet dans l'onglet "Rapport".

## Technologies utilisées
- **Langage** : Python 3.10+
- **Librairies** : pandas, numpy, statsmodels, scikit-learn, matplotlib, seaborn, plotly, openpyxl, FPDF, Streamlit

## Livrables
- Pipeline d'analyse automatisé
- Application web locale
- Rapport PDF généré automatiquement
- Documentation technique et fonctionnelle

## Rapport généré
Le rapport PDF comprend :
- Introduction générale (contexte, problématique, objectifs)
- Présentation du domaine agricole ciblé
- État de l'art (méthodes d'estimation de l'héritabilité)
- Conception technique et architecture du pipeline
- Résultats d'analyse, modélisation et visualisation

## Encadrement
Projet réalisé avec l'accompagnement de M. Achraf Akanzal, encadrant technique chez GoBranding.

---

Pour toute question ou contribution, n'hésitez pas à ouvrir une issue ou une pull request.
