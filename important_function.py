import psycopg2
from geopy.geocoders import Nominatim
import time
import re
from datetime import datetime

# Clear text
def keep_only_hebrew(text):
    # Match only Hebrew letters (exclude Hebrew punctuation)
    return re.sub(r'[^\u05D0-\u05EA]', ' ', text)

def normalize_name(name: str) -> str:
    name = str(name)
    name = name.replace('-', ' ')        # Replace dashes with space
    name = re.sub(r'\s+', ' ', name)     # Replace multiple spaces with one
    return name.strip()


def get_text_field(obj, *keys):
    for key in keys:
        if key in obj and isinstance(obj[key], dict):
            return normalize_name(obj[key].get('text', ''))
    return ''

# Fill Data Base
def get_or_create_addresses(conn, adress_obj):
    city_name = get_text_field(adress_obj, 'city')
    city_id = get_or_create_city(conn, city_name)

    area_name = get_text_field(adress_obj, 'area', 'city')
    area_id = get_or_create_area(conn, city_id, area_name)

    neighborhood_name = get_text_field(adress_obj, 'neighborhood', 'area', 'city')
    neighborhood_id = get_or_create_neighborhood(conn, area_id, neighborhood_name)

    street_name = get_text_field(adress_obj, 'street', 'neighborhood', 'area', 'city')
    street_id = get_or_create_street(conn, neighborhood_id, street_name)

    house_number = adress_obj.get('house', {}).get('number')
    floor = adress_obj.get('house', {}).get('floor')
    house_lon = adress_obj.get('coords', {}).get('lon')
    house_lat = adress_obj.get('coords', {}).get('lat')
    house_id = get_or_create_house(conn, street_id, house_number, house_lat, house_lon)

    # Check if address already exists
    cur = conn.cursor()
    cur.execute("""
        SELECT id 
        FROM addresses 
        WHERE house_id = %s AND floor=%s
    """, (house_id,floor))

    result = cur.fetchone()
    if result:
        print(f'Addresses "{house_id}, {floor}" already exists.')
        return result[0]

    # If not addresses, insert new addresses
    cur.execute("""
        INSERT INTO addresses (house_id, floor, apartment_number)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (house_id, floor, 'A'))

    address_id = cur.fetchone()[0]
    conn.commit()
    print(f'Addresses "{house_id}, {floor}" has been created.')
    return address_id


def get_or_create_city(conn, city_name):
    cur = conn.cursor()

    # Check if city already exists
    cur.execute("""
        SELECT id FROM cities WHERE name_he = %s
    """, (city_name,))

    result = cur.fetchone()

    if result:
        print(f'City "{city_name}" already exists.')
        return result[0]

    # If not exists, insert new city
    cur.execute("""
        INSERT INTO cities (name_he, name_en, cod_gov_il, population)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (city_name, city_name, 99999, 1))

    city_id = cur.fetchone()[0]
    conn.commit()
    print(f'City "{city_name}" has been created.')
    return city_id


def get_or_create_area(conn, city_id, area_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT id 
        FROM areas 
        WHERE city_id = %s AND name = %s
    """, (city_id, area_name))

    result = cur.fetchone()
    if result:
        print(f"Area '{area_name}' already exists.")
        return result[0]

    cur.execute("""
        INSERT INTO areas (city_id, name)
        VALUES (%s, %s)
        RETURNING id
    """, (city_id, area_name))

    area_id = cur.fetchone()[0]
    conn.commit()
    print(f"Area '{area_name}' has been created.")
    return area_id


def get_or_create_neighborhood(conn, area_id, neighborhood_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT id 
        FROM neighborhoods 
        WHERE area_id = %s AND name = %s
    """, (area_id, neighborhood_name))

    result = cur.fetchone()
    if result:
        print(f"Neighborhood '{neighborhood_name}' already exists.")
        return result[0]

    cur.execute("""
        INSERT INTO neighborhoods (area_id, name)
        VALUES (%s, %s)
        RETURNING id
    """, (area_id, neighborhood_name))

    neighborhood_id = cur.fetchone()[0]
    conn.commit()
    print(f"Neighborhood '{neighborhood_name}' has been created.")
    return neighborhood_id


def get_or_create_street(conn, neighborhood_id, street_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT id 
        FROM streets 
        WHERE neighborhood_id = %s AND name = %s
    """, (neighborhood_id, street_name))

    result = cur.fetchone()
    if result:
        print(f"Street '{street_name}' already exists.")
        return result[0]

    cur.execute("""
        INSERT INTO streets (neighborhood_id, name)
        VALUES (%s, %s)
        RETURNING id
    """, (neighborhood_id, street_name))

    street_id = cur.fetchone()[0]
    conn.commit()
    print(f"Street '{street_name}' has been created.")
    return street_id


def get_or_create_house(conn, street_id, house_number='O', lat=100, lon=100):
    try:
        house_number = str(house_number)
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        print(f"Invalid input for house: number={house_number}, lat={lat}, lon={lon}")
        return None

    cur = conn.cursor()
    cur.execute("""
        SELECT id 
        FROM house 
        WHERE street_id=%s AND number=%s AND lat=%s AND lon=%s
    """, (street_id, house_number, lat, lon))
    result = cur.fetchone()

    if result:
        print(f'House {house_number} already exist.')
        return result[0]

    # Insert new house
    cur.execute("""
        INSERT INTO house (street_id, number, lat, lon)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (street_id, house_number, lat, lon))
    house_id = cur.fetchone()[0]
    conn.commit()
    print(f'House {house_number} has been created.')
    return house_id


def check_or_update_apartment(conn, address_id, token: str):
    """
    Check if apartment with the given token exists.
    """
    with conn.cursor() as cur:
        # Check if apartment exists
        cur.execute("SELECT id FROM apartments WHERE token = %s", (token,))
        row = cur.fetchone()
        if row:
            apartment_id = row[0]
            # Update the updated_at field
            cur.execute("""
                UPDATE apartments
                SET updated_at = NOW()
                WHERE id = %s
            """, (apartment_id,))
            conn.commit()
            print(f"Apartment with token '{token}' exists. Updated 'updated_at'.")
            return apartment_id

        # If not exists, insert new apartment
        cur.execute("""
            INSERT INTO apartments (source, token, created_at, updated_at, actual_flg, status_id, address_id)
            VALUES (%s, %s, NOW(), NOW(), %s, %s, %s)
            RETURNING id
        """, ('yad2', token, True, 1, address_id))

        apartment_id = cur.fetchone()[0]
        conn.commit()
        print(f'Apartment "{apartment_id}" has been created.')
        return apartment_id


def check_or_update_price(conn, apartment_id, price):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO price_history (apartment_id, price, created_date)
            VALUES (%s, %s, NOW())
            RETURNING id
        """, (apartment_id, price))
        conn.commit()
        print(f'Price "{apartment_id}" has been created.')
        return apartment_id


def check_or_update_apartment_tags(conn, apartment_id, tags: list):
    with conn.cursor() as cur:
        # Check if apartment_tag already exists
        for tag in tags:
            one_tag = tag.get('name')
            cur.execute("""
                SELECT id FROM tags WHERE name = %s
            """, (one_tag,))

            result = cur.fetchone()

            if result:
                tag_id = result[0]
            else:
                tag_id = update_tags(conn, one_tag)

            cur.execute("""
                SELECT id FROM apartment_tags WHERE apartment_id = %s AND tag_id = %s
            """, (apartment_id,tag_id))

            result = cur.fetchone()

            if result:
                print(f'Apartment and tags already exist')
            else:
                cur.execute("""
                    INSERT INTO apartment_tags (apartment_id, tag_id)
                    VALUES (%s, %s)
                    RETURNING id
                """, (apartment_id, tag_id))

                conn.commit()
                print(f'Tag "{one_tag}" with id={tag_id} has been created for apartment{apartment_id}.')


def update_tags(conn, one_tag):
    with conn.cursor() as cur:
        # Insert new tag
        cur.execute("""
            INSERT INTO tags (name)
            VALUES (%s)
            RETURNING id
        """, (one_tag,))

        tag_id = cur.fetchone()[0]
        conn.commit()
        print(f'Tag "{one_tag}" has been created.')
        return tag_id


def check_or_update_apartment_features(conn, apartment_id, additionalDetails: dict):
    with conn.cursor() as cur:
        features_list_amount = {}

        property_type = additionalDetails.get('property', {}).get('text')
        property_type_id = update_feature_list(conn, 'property')
        features_list_amount[property_type_id] = property_type

        rooms_count = additionalDetails.get('roomsCount')
        roomsCount_id = update_feature_list(conn, 'roomsCount')
        features_list_amount[roomsCount_id] = rooms_count

        square_meter = additionalDetails.get('squareMeter')
        squareMeter_id = update_feature_list(conn, 'squareMeter')
        features_list_amount[squareMeter_id] = square_meter

        condition = additionalDetails.get('propertyCondition', {}).get('id')
        propertyCondition_id = update_feature_list(conn, 'propertyCondition')
        features_list_amount[propertyCondition_id] = condition

        # Check if apartment and features already exists
        for feature_id, amount in features_list_amount.items():
            cur.execute("""
            SELECT id FROM main_features WHERE apartment_id = %s AND features_id = %s
            """, (apartment_id, feature_id))

            result = cur.fetchone()
            if result:
                main_feature_id = result[0]
            else:
                cur.execute("""
                INSERT INTO main_features (apartment_id, features_id)
                VALUES (%s, %s)
                RETURNING id
                """, (apartment_id, feature_id))
                main_feature_id = cur.fetchone()[0]
                conn.commit()

            cur.execute("""
            UPDATE main_features
            SET amount = %s
            WHERE id = %s
            RETURNING id
            """, (amount, main_feature_id))
            print(f'Insert {amount} as {main_feature_id}')
            conn.commit()


def update_feature_list(conn, feature):
    with conn.cursor() as cur:
        # Check id feature
        cur.execute("""
        SELECT id FROM features_list WHERE name = %s
        """, (feature, ))

        result = cur.fetchone()
        if result:
            feature_id = result[0]
            return feature_id

        # Insert new tag
        cur.execute("""
            INSERT INTO features_list (name)
            VALUES (%s)
            RETURNING id
        """, (feature,))

        feature_id = cur.fetchone()[0]
        conn.commit()
        return feature_id


# Load Data Frame from Data Base
def remove_columns(df, columns):
    mask = [c not in columns for c in df.columns]
    df = df.loc[:, mask]

    df = df.loc[:, ~df.columns.duplicated()]
    return df

def remove_outliers_iqr(df):
    columns = ['price', 'rooms_count', 'square_meter']
    df_clean = df.copy()
    for column in columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df_clean = df_clean[(df_clean[column] >= lower_bound) & (df_clean[column] <= upper_bound)]
    return df_clean


############################################################################################################
############################################################################################################
def find_token_paths(obj, path=""):
    results = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            if key == 'private':
                results.append((new_path, value))
            results.extend(find_token_paths(value, new_path))

    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            new_path = f"{path}[{idx}]"
            results.extend(find_token_paths(item, new_path))

    return results



def insert_apartment_if_not_exists(conn, token):
    cur = conn.cursor()
    now = datetime.now()

    cur.execute("""
        INSERT INTO apartments (token, created_at, updated_at)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (token, now, now))

    apartment_id = cur.fetchone()[0]
    print(f"Inserted apartment with ID {apartment_id}")
    conn.commit()
    cur.close()
    return apartment_id




def get_address_from_coords(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")  # You can name it anything
    # Sleep to respect usage policy of OSM (1 request per second)
    time.sleep(1)
    location = geolocator.reverse((lat, lon), language='he')  # Use 'he' for Hebrew if you prefer
    return location.address if location else None


def get_or_create_full_house(conn, city_name, area_name, neighborhood_name, street_name, house_number, lat, lon):
    cur = conn.cursor()

    # Clause 1: Check house
    cur.execute("""
        SELECT id FROM house 
        WHERE number = %s AND lat = %s AND lon = %s
    """, (house_number, lat, lon))
    house = cur.fetchone()
    if house:
        print(f'Found existing house: {house[0]}')
        return house[0]

    # Clause 2: Check street
    cur.execute("SELECT id, neighborhood_id FROM streets WHERE name = %s", (street_name,))
    street = cur.fetchone()
    if street:
        street_id = street[0]
        print(f'Found existing street: {street_id}')
        house_id = get_or_create_house(conn, street_id, house_number, lat, lon)
        return house_id

    # Clause 3: Check neighborhood
    cur.execute("SELECT id, area_id FROM neighborhoods WHERE name = %s", (neighborhood_name,))
    neighborhood = cur.fetchone()
    if neighborhood:
        neighborhood_id = neighborhood[0]
        print(f'Found existing neighborhood: {neighborhood_id}')
        street_id = get_or_create_street(conn, neighborhood_id, street_name)
        house_id = get_or_create_house(conn, street_id, house_number, lat, lon)
        return house_id

    # Clause 4: Check area
    cur.execute("SELECT id, city_id FROM areas WHERE name = %s", (area_name,))
    area = cur.fetchone()
    if area:
        area_id = area[0]
        print(f'Found existing area: {area_id}')
        neighborhood_id = get_or_create_neighborhood(conn, area_id, neighborhood_name)
        street_id = get_or_create_street(conn, neighborhood_id, street_name)
        house_id = get_or_create_house(conn, street_id, house_number, lat, lon)
        return house_id

    # Clause 5: Check city
    cur.execute("SELECT id FROM cities WHERE name = %s", (city_name,))
    city = cur.fetchone()
    if city:
        city_id = city[0]
        print(f'Found existing city: {city_id}')
    else:
        # Clause 6: Create city
        city_id = get_or_create_city(conn, city_name)

    # Clause 6 → 7 → 8 → 9
    area_id = get_or_create_area(conn, city_id, area_name)
    neighborhood_id = get_or_create_neighborhood(conn, area_id, neighborhood_name)
    street_id = get_or_create_street(conn, neighborhood_id, street_name)
    house_id = get_or_create_house(conn, street_id, house_number, lat, lon)
    return house_id




################################################################################
################################################################################
#
# conn = psycopg2.connect(
#     dbname="ApartmentProject",
#     user="ilia",
#     password="securepassword",
#     host="localhost",
#     port="5432"
# )
# cursor = conn.cursor()

# token = "qirant5g"  # from JSON
# if not check_or_update_apartment(conn, token):
#     print("We should insert this apartment.")
#     apartment_id = insert_apartment_if_not_exists(conn=conn, token=token)
#     print(apartment_id)

#
# city_name = "תל אביב יפו"
# # city_id = get_or_create_city(conn, city_name)
# #
# area_name = "אזור תל אביב יפו"
# # area_id = get_or_create_area(conn, city_id, area_name)
# #
# neighborhood_name = "נווה שרת"
# # neighborhood_id = get_or_create_neighborhood(conn, area_id, neighborhood_name)
# #
# street_name = "בית אל"
# # street_id = get_or_create_street(conn, neighborhood_id, street_name)
# #
# house_number = '2A'
# lon = 34.838291
# lat = 32.117562
# get_or_create_house(conn, street_id, house_number, lat, lon)
#
#
# longitude = 34.557246
# latitude = 31.678494
# address = get_address_from_coords(latitude, longitude)
# print("Full address:", address)
# longitude = 34.838291
# latitude = 32.117562
# address = get_address_from_coords(latitude, longitude)
# print("Full address:", address)


# house_id = get_or_create_full_house(
#     conn,
#     city_name=city_name,
#     area_name=area_name,
#     neighborhood_name=neighborhood_name,
#     street_name=street_name,
#     house_number=house_number,
#     lat=lat,
#     lon=lon
# )
#
# conn.close()
