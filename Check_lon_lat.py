from geopy.geocoders import Nominatim
import important_function as modul

def city_name_by_coords(latitude, longitude):

    # Create geocoder instance
    geolocator = Nominatim(user_agent="apartment_price_predictor")

    # Reverse geocoding
    try:
        location = geolocator.reverse((latitude, longitude), language='he')  # Hebrew results
        address = location.raw.get('address', {})
    except:
        return None, None, None, None

    city = address.get('city', address.get('town', address.get('village')))
    city = modul.keep_only_hebrew(city)
    street = address.get('road')
    house_number = address.get('house_number')

    return city, street, house_number, location.address