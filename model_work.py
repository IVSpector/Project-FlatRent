import pickle
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
import important_function as modul  # your normalization functions etc.

# === Load model, scaler, features ===
with open("model_best.pkl", "rb") as f:
    model = pickle.load(f)

with open("scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

with open("features.pkl", "rb") as f:
    features = pickle.load(f)

#
# def check_price(user_input: dict):
#
#     # --- Load training data ---
#     df_train = pd.read_csv("b_DF_for_model.csv")
#
#     # --- Fit KNN imputer ---
#     imputer = KNNImputer(n_neighbors=5)
#     imputer.fit(df_train[features])
#
#     # --- Prepare default input for min/max ---
#     defaults_min = {f: np.nan for f in features}
#     defaults_max = {f: np.nan for f in features}
#
#     # --- Fill user known values ---
#     latitude = user_input["location"]["latitude"]
#     longitude = user_input["location"]["longitude"]
#     city = modul.normalize_name(str(user_input.get("city", "")))
#     floor = user_input.get("floor")
#     rooms = user_input.get("rooms")
#     square_meters = user_input.get("square_meters")
#
#     # Example: population from city CSV
#     df_city = pd.read_csv('64edd0ee-3d5d-43ce-8562-c336c24dbc1f__2025_07_27_03_30_4_630.csv',
#                           encoding='windows-1255')
#     normalized_names = df_city['שם_ישוב'].apply(modul.normalize_name)
#     population = df_city.loc[normalized_names == city, 'סהכ'].values
#     city_code = df_city.loc[normalized_names == city, 'סמל_ישוב'].values
#
#     # --- Fill known values ---
#     defaults_min["latitude"] = latitude
#     defaults_max["latitude"] = latitude
#     defaults_min["longitude"] = longitude
#     defaults_max["longitude"] = longitude
#     defaults_min["floor"] = floor if floor is not None else 0
#     defaults_max["floor"] = floor if floor is not None else 20
#     defaults_min["rooms_count"] = rooms if rooms is not None else 1
#     defaults_max["rooms_count"] = rooms if rooms is not None else 5
#     defaults_min["square_meter"] = square_meters if square_meters is not None else 20
#     defaults_max["square_meter"] = square_meters if square_meters is not None else 120
#
#     if len(population) > 0:
#         defaults_min["population"] = int(population[0])
#         defaults_max["population"] = int(population[0])
#     else:
#         defaults_min["population"] = 100000
#         defaults_max["population"] = 1000000
#
#     if len(city_code) > 0:
#         defaults_min["cod_gov_il"] = city_code[0]
#         defaults_max["cod_gov_il"] = city_code[0]
#
#     # --- Convert to DataFrame ---
#     input_min_df = pd.DataFrame([defaults_min])[features]
#     input_max_df = pd.DataFrame([defaults_max])[features]
#
#     # --- Impute missing values while preserving known values ---
#     # For min
#     missing_mask_min = input_min_df.isna()
#     imputed_array_min = imputer.transform(pd.concat([df_train[features], input_min_df], ignore_index=True))
#     imputed_min_df = pd.DataFrame(imputed_array_min, columns=features).iloc[-1:]
#     imputed_min_df[~missing_mask_min] = input_min_df[~missing_mask_min]
#
#     # For max
#     missing_mask_max = input_max_df.isna()
#     imputed_array_max = imputer.transform(pd.concat([df_train[features], input_max_df], ignore_index=True))
#     imputed_max_df = pd.DataFrame(imputed_array_max, columns=features).iloc[-1:]
#     imputed_max_df[~missing_mask_max] = input_max_df[~missing_mask_max]
#
#     # --- Scale ---
#     input_scaled_min = scaler.transform(imputed_min_df)
#     input_scaled_max = scaler.transform(imputed_max_df)
#     print(imputed_min_df)
#
#     # --- Predict ---
#     predicted_price_min = model.predict(input_scaled_min)[0]
#     predicted_price_max = model.predict(input_scaled_max)[0]
#
#     return round(predicted_price_min), round(predicted_price_max)


def check_price(user_input: dict):
    # --- Load training data ---
    df_train = pd.read_csv("b_DF_for_model.csv")

    # --- Define features used for imputation ---
    geo_features = ["lat", "lon", "population", "neighborhood_id", "cod_gov_il"]

    # --- Fit KNN imputer ---
    imputer = KNNImputer(n_neighbors=5)
    imputer.fit(df_train[geo_features])

    # --- Prepare defaults ---
    defaults_min = {f: np.nan for f in features}
    defaults_max = {f: np.nan for f in features}

    # --- Fill known values from user ---
    latitude = user_input["location"]["latitude"]
    longitude = user_input["location"]["longitude"]
    city = modul.normalize_name(str(user_input.get("city", "")))
    floor = user_input.get("floor")
    rooms = user_input.get("rooms")
    square_meters = user_input.get("square_meters")

    df_city = pd.read_csv(
        "64edd0ee-3d5d-43ce-8562-c336c24dbc1f__2025_07_27_03_30_4_630.csv",
        encoding="windows-1255"
    )
    normalized_names = df_city["שם_ישוב"].apply(modul.normalize_name)
    population = df_city.loc[normalized_names == city, "סהכ"].values

    defaults_min["lat"] = latitude
    defaults_max["lat"] = latitude
    defaults_min["lon"] = longitude
    defaults_max["lon"] = longitude
    defaults_min["floor"] = floor if floor is not None else 0
    defaults_max["floor"] = floor if floor is not None else 20
    defaults_min["rooms_count"] = rooms if rooms is not None else 1
    defaults_max["rooms_count"] = rooms if rooms is not None else 5
    defaults_min["square_meter"] = square_meters if square_meters is not None else 20
    defaults_max["square_meter"] = square_meters if square_meters is not None else 120

    # Population handling
    if len(population) > 0:
        defaults_min["population"] = population[0]
        defaults_max["population"] = population[0]
    else:
        defaults_min["population"] = np.nan
        defaults_max["population"] = np.nan

    # --- Create input DataFrames ---
    input_min_df = pd.DataFrame([defaults_min])[features]
    input_max_df = pd.DataFrame([defaults_max])[features]

    # --- Impute missing geo-based values ---
    def knn_impute(input_df):
        geo_part = input_df[geo_features]
        combined = pd.concat([df_train[geo_features], geo_part], ignore_index=True)
        imputed_geo = imputer.transform(combined)[-1:]
        imputed_geo_df = pd.DataFrame(imputed_geo, columns=geo_features)

        filled = input_df.copy()
        for col in geo_features:
            if pd.isna(filled.at[0, col]):
                filled.at[0, col] = imputed_geo_df.at[0, col]
        return filled

    imputed_min_df = knn_impute(input_min_df)
    imputed_max_df = knn_impute(input_max_df)

    # --- Scale ---
    input_scaled_min = scaler.transform(imputed_min_df[features])
    input_scaled_max = scaler.transform(imputed_max_df[features])

    # --- Predict ---
    predicted_price_min = model.predict(input_scaled_min)[0]
    predicted_price_max = model.predict(input_scaled_max)[0]

    return round(predicted_price_min), round(predicted_price_max)


# === Example usage ===
user_input = {
    "city": None,
    "floor": 4,
    "rooms": 2,
    "square_meters": 85,
    "location": {
        "latitude": 32.086076,
        "longitude": 34.787396
    }
}



min_price, max_price = check_price(user_input)
print(f"Predicted price range: ₪ {min_price:,} – ₪ {max_price:,}")
