from geopy.geocoders import Nominatim

# def get_lat_lon(address):
#     geolocator = Nominatim(user_agent="apartment_model")
#     location = geolocator.geocode(address)
#     if location:
#         return location.latitude, location.longitude
#     else:
#         return None, None
#
# # Example
# address = "Tel Aviv, Dizengoff 100"
# lat, lon = get_lat_lon(address)
# print("Latitude:", lat, "Longitude:", lon)

#
#
# import pandas as pd
# from geopy.geocoders import Nominatim
#
# # === Load CSVs ===
# cities_df = pd.read_csv("merged_city_population.csv", encoding="windows-1255")
# streets_df = pd.read_csv("9ad3862c-8391-4b2f-84a4-2d4c68625f4b__2025_07_27_03_30_4_661.csv", encoding="windows-1255")
#
# # === Step 1: Choose a city ===
# cities = sorted(cities_df['שם_ישוב'].unique())
# print("\nAvailable Cities:")
# for i, city in enumerate(cities):
#     print(f"{i}. {city}")
#
# city_idx = int(input("\nSelect a city (enter number): "))
# selected_city = cities[city_idx]
# print(f"Selected City: {selected_city}")
#
# # === Step 2: Choose a street from that city ===
# streets_in_city = streets_df[streets_df['שם_ישוב'] == selected_city]["שם_רחוב"].unique()
# streets_in_city = sorted(streets_in_city)
#
# print("\nAvailable Streets:")
# for i, street in enumerate(streets_in_city):
#     print(f"{i}. {street}")
#
# street_idx = int(input("\nSelect a street (enter number): "))
# selected_street = streets_in_city[street_idx]
# print(f"Selected Street: {selected_street}")
#
# # === Step 3: Ask for house number ===
# house_number = input("Enter house number: ")
#
# # === Step 4: Geocode address ===
# address = f"{selected_street} {house_number}, {selected_city}, Israel"
# geolocator = Nominatim(user_agent="apartment_price_model")
# location = geolocator.geocode(address)
#
# if location:
#     lat, lon = location.latitude, location.longitude
#     print(f"\nLatitude: {lat}, Longitude: {lon}")
# else:
#     print("\n⚠️ Address not found.")
#     lat, lon = None, None
#
#

def city_name_by_coords(latitude, longitude):
    from geopy.geocoders import Nominatim

    # Create geocoder instance
    geolocator = Nominatim(user_agent="apartment_price_predictor")

    # # Example coordinates
    # latitude = 31.678494
    # longitude = 34.557246

    # Reverse geocoding
    location = geolocator.reverse((latitude, longitude), language='he')  # Hebrew results

    address = location.raw.get('address', {})

    city = address.get('city', address.get('town', address.get('village')))
    street = address.get('road')
    house_number = address.get('house_number')

    return city, street, house_number,location.address



    # # Print address
    # if location:
    #     print("📍 Full address:", location.address)
    #
    #     # Extract structured data
    #     address = location.raw.get('address', {})
    #     print("City:", address.get('city', address.get('town', address.get('village'))))
    #     print("Street:", address.get('road'))
    #     print("House number:", address.get('house_number'))
    # else:
    #     print("Address not found")