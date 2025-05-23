import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import streamlit as st
import unicodedata
import re # Import regex module for parsing age string

# Define essential columns at module level
ESSENTIAL_COLS = {
    'ID': str,
    'Lactation': float,
    'Age_velage': float,
    'Rendement_lait': float,
    'Taux_mg': float,
    'Taux_prot': float
}

def sanitize_column_name(col):
    # Remove accents
    col = ''.join(c for c in unicodedata.normalize('NFD', str(col)) if unicodedata.category(c) != 'Mn')
    # Replace spaces and special characters with underscores
    col = col.replace(' ', '_').replace('%', 'pct').replace('-', '_').replace('/', '_')
    # Remove any remaining non-alphanumeric characters except underscore
    col = ''.join(c for c in col if c.isalnum() or c == '_')
    # Ensure it doesn't start with a digit
    if col and col[0].isdigit():
        col = '_' + col
    return col

def parse_age_string(age_str):
    """Parses age strings like '2 a 2 m' and returns age in months or years."""
    if pd.isna(age_str) or age_str == '':
        return np.nan
    
    age_str = str(age_str).lower().strip()
    
    # Try to extract years and months using regex
    match = re.match(r'(\d+)\s*a(?:\s*(\d+)\s*m)?', age_str)
    if match:
        years = int(match.group(1)) if match.group(1) else 0
        months = int(match.group(2)) if match.group(2) else 0
        return (years * 12) + months # Return age in months
    
    # If regex fails, try direct numeric conversion (for cases like just a number)
    try:
        return pd.to_numeric(age_str)
    except:
        return np.nan # Return NaN if parsing or conversion fails

def charger_fichier_universel(fichier):
    try:
        if fichier.name.endswith(".xlsx"):
            xls = pd.ExcelFile(fichier, engine="openpyxl")
            df_dict = {}
            
            for sheet_name in xls.sheet_names:
                try:
                    df_tmp = xls.parse(sheet_name, header=0)
                    if len(df_tmp.columns) == 0 or all('Unnamed' in str(col) for col in df_tmp.columns):
                        df_tmp = xls.parse(sheet_name, header=1)
                    
                    cols_to_drop = [col for col in df_tmp.columns if str(col).strip() == 'Unnamed: 0' or str(col).strip().startswith('Unnamed:')]
                    if cols_to_drop:
                        df_tmp = df_tmp.drop(columns=cols_to_drop)
                    
                    df_dict[sheet_name] = df_tmp
                except Exception as sheet_e:
                    st.error(f"Error processing sheet '{sheet_name}': {sheet_e}")
                    continue
            
            if not df_dict:
                raise ValueError("No sheets found in the Excel file")
            
            if 'Sujet' not in df_dict:
                raise ValueError("Sheet 'Sujet' not found in the Excel file.")
            
            reference_columns = [str(col).strip() for col in df_dict['Sujet'].columns.tolist()]
            processed_df_list = []
            
            for sheet_name, df_tmp in df_dict.items():
                if len(df_tmp.columns) == len(reference_columns):
                    df_tmp.columns = reference_columns
                    df_tmp['Source_Sheet'] = sheet_name
                    processed_df_list.append(df_tmp)
            
            if not processed_df_list:
                raise ValueError("No valid sheets processed after standardizing columns")
            
            df = pd.concat(processed_df_list, ignore_index=True)
            df = df.loc[:,~df.columns.duplicated()]
            return df
            
        elif fichier.name.endswith(".csv"):
            try:
                df = pd.read_csv(fichier)
                df.columns = [str(col).strip() for col in df.columns]
                cols_to_drop = [col for col in df.columns if str(col).strip() == 'Unnamed: 0' or str(col).strip().startswith('Unnamed:')]
                if cols_to_drop:
                    df = df.drop(columns=cols_to_drop)
                return df
            except Exception as csv_e:
                raise Exception(f"Error loading CSV file: {str(csv_e)}")
        else:
            raise ValueError("Unsupported format")
            
    except Exception as e:
        raise Exception(f"Error loading file: {str(e)}")

def nettoyer_donnees(df):
    df_clean = df.copy()
    df_clean.columns = [str(col).strip() for col in df_clean.columns]
    
    column_mapping = {
        'N° SNIT': 'ID',
        'N° LACT': 'Lactation',
        'Age Vêlage': 'Age_velage',
        'Kg Lait': 'Rendement_lait',
        '% MG': 'Taux_mg',
        'Kg MG': 'Kg_MG',
        '% Prot': 'Taux_prot',
        'Kg Prot': 'Kg_Prot'
    }
    
    df_clean = df_clean.rename(columns=column_mapping)

    for col, dtype in ESSENTIAL_COLS.items():
        if col not in df_clean.columns:
            df_clean[col] = np.nan if dtype == float else ''
        else:
            try:
                if dtype == float:
                    if col == 'Age_velage':
                        df_clean[col] = df_clean[col].apply(parse_age_string)
                    else:
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                elif dtype == str:
                    df_clean[col] = df_clean[col].astype(str).replace('nan', '')
            except Exception:
                df_clean[col] = np.nan if dtype == float else ''

    numeric_cols = ['Lactation', 'Age_velage', 'Rendement_lait', 'Taux_mg', 'Taux_prot', 'Kg_MG', 'Kg_Prot']
    for col in numeric_cols:
        if col in df_clean.columns and df_clean[col].dtype in ['float64', 'int64']:
            if df_clean[col].isnull().any():
                median_value = df_clean[col].median()
                if pd.notna(median_value):
                    df_clean[col] = df_clean[col].fillna(median_value)

    production_cols = ['Rendement_lait', 'Taux_mg', 'Taux_prot', 'Kg_MG', 'Kg_Prot']
    for col in production_cols:
        if col in df_clean.columns and df_clean[col].dtype in ['float64', 'int64']:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            if pd.notna(lower_bound) and pd.notna(upper_bound):
                df_clean[col] = df_clean[col].clip(lower_bound, upper_bound)

    if df_clean.empty:
        st.error("No valid data after cleaning. Please check your file structure.")
        return pd.DataFrame(), None

    return df_clean, None

def analyser_structure_genetique(df):
    resultats = {}
    df.columns = [str(col).strip() for col in df.columns]

    genealogy_cols = ['ID', 'Père', 'Mère']
    present_cols = [col for col in genealogy_cols if col in df.columns]
    resultats['profondeur_genealogique'] = len(present_cols) - 1
    if resultats['profondeur_genealogique'] < 0: 
        resultats['profondeur_genealogique'] = 0

    if 'Père' in df.columns and 'Mère' in df.columns:
        pere_present = df.get('Père', pd.Series(dtype=str)).astype(str).replace('', np.nan).notna()
        mere_present = df.get('Mère', pd.Series(dtype=str)).astype(str).replace('', np.nan).notna()
        nb_parents_connus = pere_present.astype(int) + mere_present.astype(int)
        resultats['stats_parents'] = {
            'deux_parents': (nb_parents_connus == 2).sum(),
            'un_parent': (nb_parents_connus == 1).sum(),
            'aucun_parent': (nb_parents_connus == 0).sum()
        }
    else:
        resultats['stats_parents'] = {
            'deux_parents': 0,
            'un_parent': 0,
            'aucun_parent': len(df)
        }

    variables_pheno = [col for col in df.columns if any(x in col.lower() for x in ['lait', 'mg', 'prot'])]
    vars_present = [col for col in variables_pheno if col in df.columns and df[col].dtype in ['float64', 'int64'] and df[col].notna().any()]

    if len(vars_present) >= 2:
        X = df[vars_present].dropna()
        if len(X) > 1:
            try:
                n_components = min(len(X), len(vars_present), 2)
                if n_components > 0:
                    pca = PCA(n_components=n_components)
                    X_pca = pca.fit_transform(X)
                    n_clusters = min(len(X_pca), 3)
                    if n_clusters > 1:
                        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                        clusters = kmeans.fit_predict(X_pca)
                        resultats['clusters'] = {
                            'labels': clusters.tolist(),
                            'centres': kmeans.cluster_centers_.tolist(),
                            'variance_expliquee': pca.explained_variance_ratio_.tolist()
                        }
                    else:
                        resultats['clusters'] = None
                else:
                    resultats['clusters'] = None
            except Exception:
                resultats['clusters'] = None
        else:
            resultats['clusters'] = None
    else:
        resultats['clusters'] = None

    return resultats

def analyser_qualite_donnees(df):
    rapport = []
    rapport.append("🔎 Column Types:")
    for col in df.columns:
        rapport.append(f"  - {col} : {df[col].dtype}")

    rapport.append("\n⚠️ Missing Values:")
    for col in df.columns:
        nb_na = df[col].isnull().sum()
        if nb_na > 0:
            pct = (nb_na / len(df)) * 100
            rapport.append(f"  - {col} : {nb_na} missing values ({pct:.1f}%)")

    num_cols = df.select_dtypes(include=np.number).columns
    if len(num_cols) > 0:
        rapport.append("\n📊 Numerical Variables Statistics:")
        for col in num_cols:
            if df[col].notna().sum() > 0:
                stats_desc = df[col].describe()
                rapport.append(f"  - {col}:")
                rapport.append(f"    * Min: {stats_desc.get('min', np.nan):.2f}")
                rapport.append(f"    * Max: {stats_desc.get('max', np.nan):.2f}")
                rapport.append(f"    * Mean: {stats_desc.get('mean', np.nan):.2f}")
                rapport.append(f"    * Median: {stats_desc.get('50%', np.nan):.2f}")
            else:
                rapport.append(f"  - {col}: All values are missing or non-numeric.")

    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    mapped_numeric_cols = list(ESSENTIAL_COLS.keys())
    cat_cols = [col for col in cat_cols if col not in mapped_numeric_cols]

    if len(cat_cols) > 0:
        rapport.append("\n📑 Categorical Variables:")
        for col in cat_cols:
            if df[col].notna().sum() > 0:
                n_unique = df[col].nunique()
                value_counts = df[col].value_counts().head(5)
                rapport.append(f"  - {col}: {n_unique} unique values")
                rapport.append("    Top values:")
                for val, count in value_counts.items():
                    pct = (count / len(df)) * 100
                    rapport.append(f"    * {val} : {count} ({pct:.1f}%)")
            else:
                rapport.append(f"  - {col}: All values are missing.")

    nb_doublons = df.duplicated().sum()
    if nb_doublons > 0:
        pct_doublons = (nb_doublons / len(df)) * 100
        rapport.append(f"\n📎 Duplicates: {nb_doublons} duplicated rows ({pct_doublons:.1f}%)")

    return "\n".join(rapport)

def identifier_variables_heritabilite(df):
    df.columns = [str(col).strip() for col in df.columns]

    original_to_standard = {
        'N° SNIT': 'ID',
        'N° LACT': 'Lactation',
        'Age Vêlage': 'Age_velage',
        'Kg Lait': 'Rendement_lait',
        '% MG': 'Taux_mg',
        'Kg MG': 'Kg_MG',
        '% Prot': 'Taux_prot',
        'Kg Prot': 'Kg_Prot'
    }

    variables = {
        'id': None,
        'pere': None,
        'mere': None,
        'traits': []
    }

    if 'ID' in df.columns:
        variables['id'] = 'ID'
    elif 'N° SNIT' in df.columns:
        variables['id'] = 'ID'

    if 'Père' in df.columns:
        variables['pere'] = 'Père'

    if 'Mère' in df.columns:
        variables['mere'] = 'Mère'

    standard_trait_names = ['Rendement_lait', 'Taux_mg', 'Taux_prot', 'Kg_MG', 'Kg_Prot']
    for orig_col, std_col in original_to_standard.items():
        if std_col in standard_trait_names and orig_col in df.columns:
            if std_col not in variables['traits']:
                variables['traits'].append(std_col)

    if not variables['id']:
        st.error("ID column (N° SNIT or ID) not found.")
        return None

    if not variables['traits']:
        st.error("No production traits found (Kg Lait/% MG/% Prot or Rendement_lait/Taux_mg/Taux_prot).")
        return None

    return variables
