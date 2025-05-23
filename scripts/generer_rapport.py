from fpdf import FPDF
import datetime
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

def generer_rapport_pdf(nom_fichier, mse, importances, cible, variables_exp, analyse_qualite, heritabilites, analyse_genetique, user):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # En-tête
    pdf.cell(200, 10, txt="Rapport d'Analyse Automatique", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Date : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=2, align='C')
    pdf.cell(200, 10, txt=f"Utilisateur : {user}", ln=3, align='C')
    pdf.ln(10)

    # Structure génétique
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="1. Structure génétique", ln=1)
    pdf.set_font("Arial", size=11)
    
    pdf.cell(200, 10, txt=f"Profondeur généalogique : {analyse_genetique['profondeur_genealogique']} générations", ln=1)
    
    if 'stats_parents' in analyse_genetique:
        stats = analyse_genetique['stats_parents']
        pdf.cell(200, 10, txt="Distribution des liens parentaux :", ln=1)
        pdf.cell(200, 10, txt=f"• Deux parents connus : {stats['deux_parents']} individus", ln=1)
        pdf.cell(200, 10, txt=f"• Un parent connu : {stats['un_parent']} individus", ln=1)
        pdf.cell(200, 10, txt=f"• Aucun parent connu : {stats['aucun_parent']} individus", ln=1)
    
    if 'clusters' in analyse_genetique:
        pdf.cell(200, 10, txt="Analyse des groupes génétiques :", ln=1)
        variance = analyse_genetique['clusters']['variance_expliquee']
        pdf.cell(200, 10, txt=f"• Variance expliquée : {variance[0]:.2%}, {variance[1]:.2%}", ln=1)
    pdf.ln(10)

    # Variables et modélisation
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="2. Analyse des variables", ln=1)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt=f"Variable cible : {cible}", ln=1)
    pdf.cell(200, 10, txt=f"Variables explicatives : {', '.join(variables_exp)}", ln=1)
    pdf.cell(200, 10, txt=f"MSE : {mse:.2f}", ln=1)
    pdf.ln(5)

    # Héritabilité
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="3. Estimation de l'héritabilité (h²)", ln=1)
    pdf.set_font("Arial", size=11)
    for k, v in heritabilites.items():
        if isinstance(v, dict):
            pdf.cell(200, 10, txt=f"Caractère : {k}", ln=1)
            pdf.cell(200, 10, txt=f"• h² = {v['h2']:.3f} ± {v['se']:.3f}", ln=1)
            pdf.cell(200, 10, txt=f"• IC-95% : [{v['ci_lower']:.3f}, {v['ci_upper']:.3f}]", ln=1)
            pdf.cell(200, 10, txt=f"• Variance génétique : {v['var_genetique']:.3f}", ln=1)
            pdf.cell(200, 10, txt=f"• Variance résiduelle : {v['var_residuelle']:.3f}", ln=1)
            pdf.ln(5)
        else:
            pdf.cell(200, 10, txt=f"h²({k}) : {v}", ln=1)
    pdf.ln(5)

    # Estimation de l'héritabilité des caractères de production
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="4. Estimation de l'héritabilité des caractères de production", ln=1)
    pdf.set_font("Arial", size=11)

    # Chargement des données
    data = pd.read_csv('data/donnees_brutes.csv')

    # Modèle mixte pour Kg Lait
    model_kg_lait = mixedlm("Kg_Lait ~ 1", data, groups=data["N° SNIT"], re_formula="1")
    result_kg_lait = model_kg_lait.fit(reml=True)

    # Afficher les résultats
    pdf.cell(200, 10, txt="Résultats pour Kg Lait:", ln=1)
    pdf.multi_cell(0, 10, txt=str(result_kg_lait.summary()))

    # Modèle mixte pour % MG
    model_mg = mixedlm("% MG ~ 1", data, groups=data["N° SNIT"], re_formula="1")
    result_mg = model_mg.fit(reml=True)

    # Afficher les résultats
    pdf.cell(200, 10, txt="Résultats pour % MG:", ln=1)
    pdf.multi_cell(0, 10, txt=str(result_mg.summary()))

    # Modèle mixte pour % Prot
    model_prot = mixedlm("% Prot ~ 1", data, groups=data["N° SNIT"], re_formula="1")
    result_prot = model_prot.fit(reml=True)

    # Afficher les résultats
    pdf.cell(200, 10, txt="Résultats pour % Prot:", ln=1)
    pdf.multi_cell(0, 10, txt=str(result_prot.summary()))

    # Importance des variables
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="5. Importance des variables", ln=1)
    pdf.set_font("Arial", size=11)
    for var, imp in importances.items():
        pdf.cell(200, 10, txt=f"{var} : {imp:.4f}", ln=1)

    # Résumé automatique
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="6. Résumé automatique", ln=1)
    pdf.set_font("Arial", size=11)
    
    # Interprétation des résultats
    h2_moyen = sum(v['h2'] for v in heritabilites.values() if isinstance(v, dict)) / len(heritabilites)
    
    pdf.multi_cell(0, 10, txt=f"""
    L'analyse des données a révélé une structure génétique avec {analyse_genetique['profondeur_genealogique']} générations de profondeur. 
    L'héritabilité moyenne des caractères étudiés est de {h2_moyen:.3f}, ce qui indique {'une forte' if h2_moyen > 0.4 else 'une modérée' if h2_moyen > 0.2 else 'une faible'} influence génétique.
    
    Les variables les plus importantes pour la prédiction sont : {', '.join(list(importances.keys())[:3])}.
    
    {analyse_qualite}
    """)

    pdf.output(nom_fichier)
