from statsmodels.regression.mixed_linear_model import MixedLM
import pandas as pd
import numpy as np
import streamlit as st # Import streamlit for st.write in debug

def modele_mixtes(df, caractere):
    """
    Estimation de l'héritabilité par modèle linéaire mixte
    
    Paramètres:
    - df: DataFrame contenant les données nettoyées et préparées
    - caractere: Nom de la variable de production à analyser (e.g., 'Rendement_lait')
    
    Retourne:
    - Résultats du modèle avec estimation de l'héritabilité
    """
    # Debug: Print columns and info of the input DataFrame
    # print("DEBUG: DataFrame columns in modele_mixtes:", df.columns.tolist())
    # print("DEBUG: DataFrame info in modele_mixtes:")
    # df.info()

    df_model = df.copy()
    
    # Préparation des effets fixes
    fixed_effects = []
    
    # Add fixed effects if available and are in the DataFrame
    if 'Lactation' in df_model.columns:
        fixed_effects.append('Lactation')
        
    if 'Age_velage' in df_model.columns:
        fixed_effects.append('Age_velage')
    
    # Ensure the dependent variable (caractere) and group variable (ID) are present
    if caractere not in df_model.columns:
        raise ValueError(f"La colonne du caractère '{caractere}' n'est pas trouvée dans le DataFrame.")
    if 'ID' not in df_model.columns:
        raise ValueError("La colonne d'identification 'ID' n'est pas trouvée dans le DataFrame.")
        
    # Select only necessary columns for the model to avoid issues with other dtypes/data
    model_cols = ['ID', caractere] + fixed_effects
    df_model = df_model[model_cols].copy()

    # --- Data Cleaning and Validation for Model ---START
    
    # Ensure ID is of type object/string for grouping and strip whitespace
    if df_model['ID'].dtype != 'object':
         df_model['ID'] = df_model['ID'].astype(str)
    df_model['ID'] = df_model['ID'].str.strip()

    # Ensure dependent variable is numeric (float64) and handle non-finite values
    df_model[caractere] = pd.to_numeric(df_model[caractere], errors='coerce').astype(np.float64)
    df_model = df_model.replace([np.inf, -np.inf], np.nan) # Replace inf with NaN

    # Ensure fixed effects are numeric (float64) and handle non-finite values
    for fe in fixed_effects:
        df_model[fe] = pd.to_numeric(df_model[fe], errors='coerce').astype(np.float64)
        df_model = df_model.replace([np.inf, -np.inf], np.nan) # Replace inf with NaN

    # Drop rows with NaNs in the necessary columns AFTER conversions
    subset_cols = [caractere, 'ID'] + fixed_effects
    df_model = df_model.dropna(subset=subset_cols)
    
    # Ensure there's still data after dropping NaNs
    if df_model.empty:
        raise ValueError(f"No valid data remaining for trait '{caractere}' or its fixed effects after handling missing values.")
        
    # Ensure enough unique groups for the mixed model
    if df_model['ID'].nunique() < 2:
        raise ValueError(f"Not enough unique IDs ({df_model['ID'].nunique()}) for mixed model for trait '{caractere}'. Need at least 2.")

    # --- Data Cleaning and Validation for Model ---END

    # Construction de la formule
    formule = f"{caractere} ~ 1"
    if fixed_effects:
        formule += " + " + " + ".join(fixed_effects)

    # Debug prints before model fitting
    # print("DEBUG: Formula before model fit:", formule)
    # print("DEBUG: DataFrame columns before model fit:", df_model.columns.tolist())
    # print("DEBUG: DataFrame info before model fit:")
    # df_model.info()
    # print("DEBUG: DataFrame head before model fit:", df_model.head())
    # print("DEBUG: Unique IDs before model fit:", df_model['ID'].nunique())
    # print("DEBUG: DataFrame size before model fit:", len(df_model))

    try:
        # Fit the mixed model
        # Using REML=True is generally recommended for variance component estimation
        # Add more detailed error logging here
        st.info(f"Attempting to fit mixed model for {caractere}...") # Add a user-facing status message
        print(f"DEBUG: Fitting model for trait: {caractere} with formula: {formule}")
        
        model = MixedLM.from_formula(formule, groups=df_model['ID'], data=df_model)
        result = model.fit(reml=True)
        st.success(f"Mixed model for {caractere} fitted successfully.") # Add success message
        print(f"DEBUG: Model fitted successfully for {caractere}.")

        # Recalculate h2 and variances from results
        # Ensure cov_re exists and has expected shape (1, 1) for a simple random intercept model
        if hasattr(result, 'cov_re') and result.cov_re is not None and result.cov_re.shape == (1, 1):
            var_genetique = result.cov_re.iloc[0, 0]
            # print("DEBUG: Genetic variance found:", var_genetique)
        else:
            # print("DEBUG: result.cov_re is None or has unexpected shape. Cannot calculate genetic variance. Shape:", getattr(result, 'cov_re', None))
            # If cov_re is not available or incorrect, assume genetic variance is not estimated
            var_genetique = np.nan # Use NaN instead of 0 to indicate failure to estimate

        var_residuelle = result.scale if hasattr(result, 'scale') else np.nan
        # print("DEBUG: Residual variance found:", var_residuelle)
        
        # Only calculate h2 if both variance components are available and total variance > 0
        if np.isfinite(var_genetique) and np.isfinite(var_residuelle) and (var_genetique + var_residuelle) > 0:
             var_tot = var_genetique + var_residuelle
             h2 = var_genetique / var_tot
             # print("DEBUG: h2 calculated:", h2)
        else:
             h2 = np.nan # Cannot calculate h2 if variances are missing or total variance is zero/negative
             var_tot = np.nan
             # print("DEBUG: Cannot calculate h2. Genetic variance:", var_genetique, "Residual variance:", var_residuelle)

        # Attempt to get standard error and confidence intervals from summary if available
        se = np.nan
        ci_lower = np.nan
        ci_upper = np.nan
        try:
            # The summary table can be parsed to get these values if the model output includes them
            # This is a simplification; actual parsing might be more complex depending on statsmodels version and model results structure
            # For MixedLM, SE and CI for variance components might require result.summary() parsing or specific methods if they exist
            # As a placeholder, we can't reliably get SE/CI for h2 directly without more advanced techniques or output parsing.
            pass # Keep as NaN for now
        except Exception as sum_e:
            # print(f"DEBUG: Error parsing summary for SE/CI: {sum_e}")
            pass

        # Returning variances and h2 (potentially NaN if model issues)
        results = {
            'h2': h2,
            'se': se, # Placeholder for SE of h2
            'ci_lower': ci_lower, # Placeholder for CI lower bound
            'ci_upper': ci_upper, # Placeholder for CI upper bound
            'var_genetique': var_genetique,
            'var_residuelle': var_residuelle,
            'model': result # Include model result for potential further inspection
        }

        return results

    except Exception as model_e:
        print(f"DEBUG: Detailed error during model fitting for trait {caractere}: {model_e}")
        st.error(f"Error during model fitting for trait {caractere}: {model_e}")
        raise Exception(f"Erreur de modélisation pour le caractère '{caractere}' : {model_e}")
