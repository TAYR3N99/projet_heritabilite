from fpdf import FPDF
import datetime
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

def generer_rapport_pdf(nom_fichier, mse, importances, cible, variables_exp, analyse_qualite, heritabilites, analyse_genetique, user, mating_recommendations):
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

    # Importance des variables
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="4. Importance des variables", ln=1) # Renumbered from 5 to 4
    pdf.set_font("Arial", size=11)
    for var, imp in importances.items():
        pdf.cell(200, 10, txt=f"{var} : {imp:.4f}", ln=1)
    pdf.ln(10) # Add some space before the new section

    # Section 5: Mating Recommendations
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="5. Recommandations d'Accouplement", ln=1)
    pdf.set_font("Arial", size=10)

    if mating_recommendations:
        # Table Header
        pdf.set_font("Arial", style='B', size=10)
        col_width_id = 30
        col_width_trait = 40
        col_width_value = 25
        # col_width_reason = 190 - (2*col_width_id + col_width_trait + 2*col_width_value) # Reason will be on a new line

        pdf.cell(col_width_id, 7, txt="Mâle ID", border=1, ln=0, align='C')
        pdf.cell(col_width_id, 7, txt="Femelle ID", border=1, ln=0, align='C')
        pdf.cell(col_width_trait, 7, txt="Focus Caractère", border=1, ln=0, align='C')
        pdf.cell(col_width_value, 7, txt="Valeur Mâle", border=1, ln=0, align='C')
        pdf.cell(col_width_value, 7, txt="Valeur Femelle", border=1, ln=1, align='C')

        pdf.set_font("Arial", size=9)
        for reco in mating_recommendations:
            male_id = str(reco.get('male_id', 'N/A'))
            female_id = str(reco.get('female_id', 'N/A'))
            trait_focus = str(reco.get('trait_focus', 'N/A'))

            male_val = reco.get('male_trait_value')
            female_val = reco.get('female_trait_value')

            male_trait_value_str = f"{male_val:.2f}" if isinstance(male_val, (int, float)) and not np.isnan(male_val) else "N/A"
            female_trait_value_str = f"{female_val:.2f}" if isinstance(female_val, (int, float)) and not np.isnan(female_val) else "N/A"

            reason = str(reco.get('reason', 'N/A'))

            if pdf.get_y() + 14 > pdf.page_break_trigger: # Estimate height for table row + reason
                 pdf.add_page()
                 pdf.set_font("Arial", style='B', size=10)
                 pdf.cell(col_width_id, 7, txt="Mâle ID", border=1, ln=0, align='C')
                 pdf.cell(col_width_id, 7, txt="Femelle ID", border=1, ln=0, align='C')
                 pdf.cell(col_width_trait, 7, txt="Focus Caractère", border=1, ln=0, align='C')
                 pdf.cell(col_width_value, 7, txt="Valeur Mâle", border=1, ln=0, align='C')
                 pdf.cell(col_width_value, 7, txt="Valeur Femelle", border=1, ln=1, align='C')
                 pdf.set_font("Arial", size=9)

            current_x = pdf.get_x()
            current_y = pdf.get_y()
            pdf.multi_cell(col_width_id, 7, txt=male_id, border=1, align='C', new_x="RIGHT", new_y="TOP", max_line_height=7)
            pdf.set_xy(current_x + col_width_id, current_y)
            pdf.multi_cell(col_width_id, 7, txt=female_id, border=1, align='C', new_x="RIGHT", new_y="TOP", max_line_height=7)
            pdf.set_xy(current_x + 2*col_width_id, current_y)
            pdf.multi_cell(col_width_trait, 7, txt=trait_focus, border=1, align='C', new_x="RIGHT", new_y="TOP", max_line_height=7)
            pdf.set_xy(current_x + 2*col_width_id + col_width_trait, current_y)
            pdf.multi_cell(col_width_value, 7, txt=male_trait_value_str, border=1, align='C', new_x="RIGHT", new_y="TOP", max_line_height=7)
            pdf.set_xy(current_x + 2*col_width_id + col_width_trait + col_width_value, current_y)
            pdf.multi_cell(col_width_value, 7, txt=female_trait_value_str, border=1, align='C', new_x="RIGHT", new_y="TOP", max_line_height=7)
            pdf.ln(7)

            pdf.set_fill_color(240, 240, 240)
            pdf.multi_cell(190, 5, txt=f"Raison: {reason}", border=0, align='L', ln=1, fill=True)
            pdf.ln(2)
    else:
        pdf.cell(200, 10, txt="Aucune recommandation d'accouplement générée.", ln=1)
    pdf.ln(10)

    # Résumé automatique
    pdf.ln(10)
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, txt="6. Résumé automatique", ln=1) # Renumbered from 6 to 6 (no change here, but good to be explicit)
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
