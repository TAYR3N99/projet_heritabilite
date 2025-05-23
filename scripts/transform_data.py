import pandas as pd
import numpy as np

def transform_excel_data(input_file):
    # Read all sheets
    xl = pd.ExcelFile(input_file)
    sheet_names = xl.sheet_names
    print(f"Available sheets: {sheet_names}")
    
    # Read each sheet
    dfs = {}
    for sheet in sheet_names:
        df = pd.read_excel(input_file, sheet_name=sheet)
        print(f"\nColumns in {sheet}:")
        print(df.columns.tolist())
        dfs[sheet] = df
    
    # Create the transformed dataframe
    transformed_data = []
    
    # Process each row in the first sheet
    main_sheet = dfs[sheet_names[0]]  # Use first sheet as main data
    
    for _, row in main_sheet.iterrows():
        # Create new row with mapped columns
        new_row = {
            'ID': row['N SNIT'],
            'Père': 0,  # Default to 0 if not available
            'Mère': 0,  # Will be updated if found in other sheets
            'Rendement_lait': row['Kg Lait'],
            'Taux_mg': row['% MG'],
            'Taux_prot': row['% Prot'],
            'Saison': 'Été' if row['N LACT'] % 2 == 0 else 'Hiver',  # Example season assignment
            'Elevage': 'A'  # Default farm
        }
        transformed_data.append(new_row)
    
    # Create final dataframe
    final_df = pd.DataFrame(transformed_data)
    
    # Save to new Excel file
    output_file = 'data/transformed_data.xlsx'
    final_df.to_excel(output_file, index=False)
    print(f"\nTransformed data saved to {output_file}")
    
    return final_df

if __name__ == "__main__":
    input_file = "data/Fiche animal Sujet.xlsx"
    transformed_data = transform_excel_data(input_file)
    print("\nFirst few rows of transformed data:")
    print(transformed_data.head()) 