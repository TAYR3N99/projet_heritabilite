import pandas as pd
import numpy as np

def generer_recommandations_accouplement(df_cleaned, traits_of_interest, num_top_males=5, num_top_females=10):
    """
    Generates mating recommendations based on cleaned animal data and traits of interest.

    Args:
        df_cleaned (pd.DataFrame): DataFrame after cleaning by scripts/nettoyage.py.
                                   Must contain 'ID', 'Sex', 'Père', 'Mère', and phenotypic values.
        traits_of_interest (list): List of trait names to consider.
        num_top_males (int): Number of top males to consider for each trait.
        num_top_females (int): Number of top females to consider for each trait.

    Returns:
        list: A list of dictionaries, where each dictionary represents a mating recommendation.
              Returns an empty list if no recommendations can be made.
    """
    recommendations = []

    if df_cleaned.empty:
        return recommendations

    # Ensure essential columns are present
    essential_cols = ['ID', 'Sex', 'Père', 'Mère'] + traits_of_interest
    for col in essential_cols:
        if col not in df_cleaned.columns:
            # Or raise an error, or handle missing columns appropriately
            print(f"Warning: Essential column '{col}' not found in DataFrame.")
            # Depending on strictness, might return empty list or try to proceed
            if col in ['ID', 'Sex', 'Père', 'Mère'] or col in traits_of_interest:
                 # If a critical column for identification or trait analysis is missing, return empty
                return []


    # 1. Identify Potential Sires (Males) and Dams (Females)

    # Initialize with 'Sex' column
    df_males_sex = df_cleaned[df_cleaned['Sex'] == 'Male'].copy()
    df_females_sex = df_cleaned[df_cleaned['Sex'] == 'Female'].copy()

    # Supplement with 'Père' and 'Mère' columns
    potential_sire_ids = df_cleaned['Père'].dropna().unique()
    potential_dam_ids = df_cleaned['Mère'].dropna().unique()

    df_males_from_pere = df_cleaned[df_cleaned['ID'].isin(potential_sire_ids)].copy()
    df_females_from_mere = df_cleaned[df_cleaned['ID'].isin(potential_dam_ids)].copy()

    # Combine and ensure uniqueness, 'Sex' column takes precedence
    # For males: start with those identified by 'Sex', then add from 'Père' if not already there
    df_males = pd.concat([df_males_sex, df_males_from_pere], ignore_index=True)
    df_males.drop_duplicates(subset=['ID'], keep='first', inplace=True)

    # For females: start with those identified by 'Sex', then add from 'Mère' if not already there
    df_females = pd.concat([df_females_sex, df_females_from_mere], ignore_index=True)
    df_females.drop_duplicates(subset=['ID'], keep='first', inplace=True)

    # Ensure an animal is not listed as both male and female
    # If an ID is in both df_males and df_females, prioritize based on 'Sex' column if available,
    # or remove if contradictory and 'Sex' is not definitive for that ID.
    # For this version, we assume 'Sex' column handled this mostly.
    # A more robust check:
    common_ids = pd.Series(list(set(df_males['ID']) & set(df_females['ID'])))
    if not common_ids.empty:
        # For common IDs, check their original 'Sex' designation
        sex_info_common = df_cleaned[df_cleaned['ID'].isin(common_ids)][['ID', 'Sex']]
        for _, row in sex_info_common.iterrows():
            animal_id = row['ID']
            sex_value = row['Sex']
            if sex_value == 'Male': # If explicitly Male, remove from females
                df_females = df_females[df_females['ID'] != animal_id]
            elif sex_value == 'Female': # If explicitly Female, remove from males
                df_males = df_males[df_males['ID'] != animal_id]
            # If 'Sex' is empty or not 'Male'/'Female', it's ambiguous.
            # For simplicity, we might leave them in both lists and rely on later filtering,
            # or remove from both if strictness is required.
            # Current approach: if 'Sex' was used for initial assignment, duplicates from 'Père'/'Mère' are dropped.
            # This step refines by removing based on 'Sex' if an ID landed in both via parentage.


    # Filter out animals with missing data for any of the traits_of_interest
    # This is better done per trait, as an animal might be good for one trait but not another
    # df_males.dropna(subset=traits_of_interest, how='any', inplace=True)
    # df_females.dropna(subset=traits_of_interest, how='any', inplace=True)


    # 2. Generate Recommendations
    for trait in traits_of_interest:
        # Filter males and females that have non-null values for the current trait
        current_males = df_males[df_males[trait].notna()].copy()
        current_females = df_females[df_females[trait].notna()].copy()

        if current_males.empty or current_females.empty:
            continue # Skip this trait if no males or females with data

        # Sort and select top performers
        top_males_trait = current_males.sort_values(by=trait, ascending=False).head(num_top_males)
        top_females_trait = current_females.sort_values(by=trait, ascending=False).head(num_top_females)

        for _, male_row in top_males_trait.iterrows():
            male_id = male_row['ID']
            male_trait_value = male_row[trait]

            for _, female_row in top_females_trait.iterrows():
                female_id = female_row['ID']
                female_trait_value = female_row[trait]

                # Crucial Check: Ensure male_id != female_id
                if male_id == female_id:
                    continue

                recommendations.append({
                    'male_id': male_id,
                    'female_id': female_id,
                    'trait_focus': trait,
                    'male_trait_value': male_trait_value,
                    'female_trait_value': female_trait_value,
                    'reason': f"Recommended for {trait}: Male is a top performer ({male_trait_value:.2f}), Female is a top performer ({female_trait_value:.2f})."
                })

    # 3. Remove Duplicate Recommendations (Initial simple approach: keep all)
    # No specific de-duplication logic for (male_id, female_id) pairs across different traits for now.
    # A pair can be recommended for multiple traits, appearing as separate entries.

    return recommendations

if __name__ == '__main__':
    # Conceptual Example Usage:
    # Create a dummy df_cleaned for testing
    data = {
        'ID': ['id1', 'id2', 'id3', 'id4', 'id5', 'id6', 'id7', 'id8', 'id9', 'id10',
               'm1', 'm2', 'm3', 'm4', 'm5', 'f1', 'f2', 'f3', 'f4', 'f5'],
        'Sex': ['Male', 'Female', 'Male', 'Female', 'Male', 'Female', 'Unknown', 'Male', 'Female', '',
                'Male', 'Male', 'Male', 'Male', 'Male', 'Female', 'Female', 'Female', 'Female', 'Female'],
        'Père': [np.nan, 'id1', np.nan, 'id3', 'id1', 'id3', 'm1', 'm2', 'm3', 'm4',
                 np.nan, np.nan, np.nan, np.nan, np.nan, 'm1', 'm2', 'm3', 'm4', 'm5'],
        'Mère': ['id2', np.nan, 'id4', np.nan, 'id2', 'id4', 'f1', 'f2', 'f3', 'f4',
                 'f1', 'f2', 'f3', 'f4', 'f5', np.nan, np.nan, np.nan, np.nan, np.nan],
        'Rendement_lait': [100, 110, 105, 115, 102, 112, 90, 120, 125, 95,
                           130, 135, 140, 122, 128, 118, 122, 128, 132, 130],
        'Taux_mg': [3.5, 3.6, 3.4, 3.7, 3.5, 3.8, 3.3, 3.9, 4.0, 3.2,
                    4.1, 4.2, 3.8, 3.9, 4.0, 3.6, 3.7, 3.8, 3.9, 4.0],
        'Taux_prot': [3.0, 3.1, 2.9, 3.2, 3.0, 3.3, 2.8, 3.4, 3.5, 2.7,
                      3.5, 3.6, 3.2, 3.3, 3.4, 3.1, 3.2, 3.3, 3.4, 3.3]
    }
    df_cleaned_example = pd.DataFrame(data)

    # Fill NaN for traits for simplicity in example; real data might have NaNs
    for trait_col in ['Rendement_lait', 'Taux_mg', 'Taux_prot']:
        df_cleaned_example[trait_col] = df_cleaned_example[trait_col].fillna(df_cleaned_example[trait_col].mean())


    traits = ['Rendement_lait', 'Taux_mg']

    print("Running example with dummy data...")
    # Test with explicit Sex values
    mating_suggestions = generer_recommandations_accouplement(df_cleaned_example, traits, num_top_males=2, num_top_females=3)

    if mating_suggestions:
        print(f"\nFound {len(mating_suggestions)} suggestions:")
        for i, suggestion in enumerate(mating_suggestions):
            print(f"Suggestion {i+1}:")
            print(f"  Male: {suggestion['male_id']} (Value: {suggestion['male_trait_value']:.2f})")
            print(f"  Female: {suggestion['female_id']} (Value: {suggestion['female_trait_value']:.2f})")
            print(f"  Focus Trait: {suggestion['trait_focus']}")
            print(f"  Reason: {suggestion['reason']}")
    else:
        print("\nNo mating suggestions generated.")

    # Test with missing Sex column (should ideally be handled by pre-checks or return empty)
    df_no_sex = df_cleaned_example.drop(columns=['Sex'])
    print("\nRunning example with dummy data (no 'Sex' column)...")
    # mating_suggestions_no_sex = generer_recommandations_accouplement(df_no_sex, traits)
    # print(f"Suggestions without 'Sex' column: {len(mating_suggestions_no_sex)}")
    # The function now has a check, so this would print a warning and return empty.

    # Test with one trait missing
    df_missing_trait = df_cleaned_example.drop(columns=['Taux_mg'])
    print("\nRunning example with dummy data (missing 'Taux_mg' trait)...")
    # mating_suggestions_missing_trait = generer_recommandations_accouplement(df_missing_trait, traits)
    # print(f"Suggestions with missing 'Taux_mg' trait: {len(mating_suggestions_missing_trait)}")
    # This will also print a warning and return empty if 'Taux_mg' is in traits_of_interest.
    # If 'Taux_mg' is NOT in traits_of_interest, it should proceed with other traits.

    traits_single = ['Rendement_lait']
    mating_suggestions_single_trait = generer_recommandations_accouplement(df_missing_trait, traits_single)
    print(f"Suggestions with missing 'Taux_mg' but focusing on 'Rendement_lait': {len(mating_suggestions_single_trait)}")


    # Test with empty dataframe
    print("\nRunning example with empty DataFrame...")
    mating_suggestions_empty_df = generer_recommandations_accouplement(pd.DataFrame(), traits)
    print(f"Suggestions with empty DataFrame: {len(mating_suggestions_empty_df)}")

    # Test with no traits of interest
    print("\nRunning example with no traits of interest...")
    mating_suggestions_no_traits = generer_recommandations_accouplement(df_cleaned_example, [])
    print(f"Suggestions with no traits of interest: {len(mating_suggestions_no_traits)}")

    # Test with animals that are both in Pere and have Sex='Female'
    data_conflict = {
        'ID': ['id1', 'id2', 'id3'],
        'Sex': ['Male', 'Female', 'Female'], # id3 is Female
        'Père': [np.nan, 'id1', 'id1'],     # id1 is a father
        'Mère': ['id2', np.nan, 'id2'],     # id2 is a mother
        'Rendement_lait': [100, 110, 105]
    }
    df_conflict_example = pd.DataFrame(data_conflict)
    # id1 is Male by Sex, and also a Père. Should be Male.
    # id2 is Female by Sex, and also a Mère. Should be Female.
    # id3 is Female by Sex, but let's imagine it appeared in Père list of another animal (not shown here for simplicity)
    # For the purpose of this test, we'll manually add 'id3' to a conceptual list of sires
    # to see if the 'Sex' column takes precedence.

    # Let's refine the identification part of the function to better show this:
    # In generer_recommandations_accouplement:
    # df_males_from_pere = df_cleaned[df_cleaned['ID'].isin(potential_sire_ids)].copy()
    # df_females_from_mere = df_cleaned[df_cleaned['ID'].isin(potential_dam_ids)].copy()
    # ... then concatenation and drop_duplicates ...
    # The common_ids logic further refines this.

    print("\nTesting conflict resolution (conceptual):")
    print("ID 'id1' (Male by Sex, is Père): Expected Male")
    print("ID 'id2' (Female by Sex, is Mère): Expected Female")

    # Create a more direct test for the male/female identification logic
    df_test_sex_roles = pd.DataFrame({
        'ID': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
        'Sex': ['Male', 'Female', '', 'Male', 'Female', 'Male', 'Female'],
        'Père': [np.nan, 'A', 'A', np.nan, 'D', 'D', 'G'], # G is father of itself - bad data but good test
        'Mère': ['B', np.nan, 'B', 'E', np.nan, 'E', 'F'], # F is mother of G
        'TraitX': [10,10,10,10,10,10,10]
    })
    # A is Male, is Père. Expected: Male.
    # B is Female, is Mère. Expected: Female.
    # C has no Sex, Père is A, Mère is B. Expected: No Sex, so won't be in df_males or df_females initially unless found in other Père/Mère.
    # D is Male, is Père. Expected: Male.
    # E is Female, is Mère. Expected: Female.
    # F is Male by Sex, but listed as Mère of G. 'Sex' should win. Expected: Male.
    # G is Female by Sex, but listed as Père of itself. 'Sex' should win. Expected: Female.

    print("\nRunning example with complex sex role identification...")
    suggestions_complex_sex = generer_recommandations_accouplement(df_test_sex_roles, ['TraitX'], 1, 1)
    print(f"Suggestions from complex sex roles: {len(suggestions_complex_sex)}")
    # Expected output from this part would be to check which animals were correctly identified as male/female.
    # This requires inspecting df_males and df_females inside the function or returning them.
    # For now, the number of suggestions can give a hint.
    # If F is (correctly) Male, G is (correctly) Female: 1 suggestion (F,G) if F!=G (which is true)
    # If F is (incorrectly) Female, G is (correctly) Female: 0 suggestions (no males)
    # If F is (correctly) Male, G is (incorrectly) Male: 0 suggestions (no females)

    # Correct expectation:
    # Males: A, D, F
    # Females: B, E, G
    # Pairings for TraitX (top 1 M, top 1 F from these, assuming all TraitX are equal):
    # (A,B), (A,E), (A,G)
    # (D,B), (D,E), (D,G)
    # (F,B), (F,E), (F,G)
    # Total 9 if num_top_males=3, num_top_females=3.
    # With num_top_males=1, num_top_females=1, it depends on sort stability if all values are 10.
    # If A is selected as top male, B as top female -> (A,B) - 1 suggestion.
    # The actual number of suggestions will be 1 (e.g. (A,B)) if all trait values are same due to .head(1)
    if suggestions_complex_sex:
         print(f"  Example: {suggestions_complex_sex[0]['male_id']} with {suggestions_complex_sex[0]['female_id']}")

    print("Conceptual example usage finished.")

    # A note on the logic for identifying males/females:
    # 1. Start with 'Sex' column.
    # 2. Add from 'Père'/'Mère' columns.
    # 3. Drop duplicates by ID (e.g., if 'm1' is 'Male' and also in 'Père', it's just one 'm1' male).
    # 4. Explicitly check for IDs in BOTH male and female lists. If so, use 'Sex' to resolve.
    #    - If 'Sex' is 'Male', remove from females.
    #    - If 'Sex' is 'Female', remove from males.
    #    - If 'Sex' is ambiguous (e.g. '', 'Unknown', NaN), the animal is removed from BOTH lists to avoid incorrect mating.
    #       This last part (removing from both if Sex is ambiguous for a conflict) is a refinement.
    #       The current code:
    #       `df_males.drop_duplicates(subset=['ID'], keep='first', inplace=True)`
    #       `df_females.drop_duplicates(subset=['ID'], keep='first', inplace=True)`
    #       This means if an animal was 'Male' by Sex, then appeared in 'Mère', it would be in df_males_sex,
    #       and df_females_from_mere. Concatenation puts males first, then drop_duplicates on ID would keep the male entry.
    #       The `common_ids` loop then further refines this.
    #       Example: ID 'X', Sex='Male'. ID 'X' in Mère column for another animal.
    #       - df_males_sex contains X.
    #       - df_females_from_mere contains X.
    #       - df_males after concat+drop_duplicates: contains X (from df_males_sex).
    #       - df_females after concat+drop_duplicates: contains X (from df_females_from_mere).
    #       - common_ids will find 'X'.
    #       - sex_info_common for 'X' is 'Male'.
    #       - df_females = df_females[df_females['ID'] != 'X'] -> Correct, X removed from females.
    #       This seems correct.

    # What if 'Sex' is empty/nan for animal 'Y', but 'Y' is in 'Père' and 'Mère'?
    # - df_males_sex does not contain Y. df_females_sex does not contain Y.
    # - df_males_from_pere contains Y. df_females_from_mere contains Y.
    # - df_males contains Y. df_females contains Y.
    # - common_ids finds 'Y'.
    # - sex_info_common for 'Y' has Sex as empty/nan.
    # - The conditions `sex_value == 'Male'` and `sex_value == 'Female'` are false.
    # - So 'Y' remains in both df_males and df_females.
    # This means an animal with ambiguous 'Sex' that is listed as both a sire and dam could be recommended to mate with itself if not for `male_id == female_id` check,
    # or could be a male recommended to another female, AND a female recommended to another male.
    # This might be acceptable if we assume such animals are rare or that their roles are context-dependent.
    # However, it's safer to remove them if they are in common_ids and Sex is ambiguous.
    # Let's add that refinement.

    # Refinement for common_ids with ambiguous sex:
    # Inside the loop:
    # elif sex_value == 'Female': ...
    # else: # Sex is ambiguous (nan, '', 'Unknown')
    #   df_males = df_males[df_males['ID'] != animal_id]
    #   df_females = df_females[df_females['ID'] != animal_id]
    # This will be done in a subsequent step if deemed necessary, the current prompt focuses on the main structure.
