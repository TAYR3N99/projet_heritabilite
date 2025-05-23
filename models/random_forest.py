from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def entrainer_random_forest(df, cible, variables_exp):
    df_clean = df.dropna(subset=[cible] + variables_exp)
    X = df_clean[variables_exp]
    y = df_clean[cible]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modele = RandomForestRegressor(n_estimators=100, random_state=42)
    modele.fit(X_train, y_train)
    predictions = modele.predict(X_test)

    mse = mean_squared_error(y_test, predictions)
    importances = modele.feature_importances_

    return modele, mse, dict(zip(variables_exp, importances))
