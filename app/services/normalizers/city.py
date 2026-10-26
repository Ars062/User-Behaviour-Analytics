# # app/services/normalizers/city.py
# from geopy.geocoders import Nominatim
# import time

# geolocator = Nominatim(user_agent="umami-city-normalizer")

# def normalize_cities(raw):
#     """
#     Normalize city data into the format:
#     {
#         "city": "Kolkata",
#         "country": "India",
#         "label": "Kolkata, India",
#         "visitors": 123
#     }

#     Similar to region normalizer, but using geolocation for country.
#     """
#     if not raw:
#         return []

#     result = []

#     for item in raw:
#         x_value = item.get("x", "Unknown")
#         visitors = item.get("y", 0)

#         city_name = x_value.strip() if x_value else "Unknown"
#         country_name = "Unknown"

#         # Try geocode city → country
#         try:
#             location = geolocator.geocode(city_name, timeout=10)
#             if location and "country" in location.raw.get("address", {}):
#                 country_name = location.raw["address"]["country"]
#         except Exception:
#             country_name = "Unknown"

#         label = f"{city_name}, {country_name}" if country_name != "Unknown" else city_name

#         result.append({
#             "city": city_name,
#             "country": country_name,
#             "label": label,
#             "visitors": int(visitors)
#         })

#         time.sleep(1)  # important to respect Nominatim rate limits

#     return result
# # app/services/normalizers/city.py
# from geopy.geocoders import Nominatim
# import time

# geolocator = Nominatim(user_agent="umami-city-normalizer")

# def normalize_cities(raw):
#     """
#     Normalize city data into the format:
#     {
#         "city": "Kolkata",
#         "country": "India",
#         "label": "Kolkata, India",
#         "visitors": 123
#     }

#     Similar to region normalizer, but using geolocation for country.
#     """
#     if not raw:
#         return []

#     result = []

#     for item in raw:
#         x_value = item.get("x", "Unknown")
#         visitors = item.get("y", 0)

#         city_name = x_value.strip() if x_value else "Unknown"
#         country_name = "Unknown"

#         # Try geocode city → country
#         try:
#             location = geolocator.geocode(city_name, timeout=10)
#             if location and "country" in location.raw.get("address", {}):
#                 country_name = location.raw["address"]["country"]
#         except Exception:
#             country_name = "Unknown"

#         label = f"{city_name}, {country_name}" if country_name != "Unknown" else city_name

#         result.append({
#             "city": city_name,
#             "country": country_name,
#             "label": label,
#             "visitors": int(visitors)
#         })

#         time.sleep(1)  # important to respect Nominatim rate limits

#     return result
# # app/services/normalizers/city.py
# from geopy.geocoders import Nominatim
# import time

# geolocator = Nominatim(user_agent="umami-city-normalizer")

# def normalize_cities(raw):
#     """
#     Normalize city data into the format:
#     {
#         "city": "Kolkata",
#         "country": "India",
#         "label": "Kolkata, India",
#         "visitors": 123
#     }

#     Similar to region normalizer, but using geolocation for country.
#     """
#     if not raw:
#         return []

#     result = []

#     for item in raw:
#         x_value = item.get("x", "Unknown")
#         visitors = item.get("y", 0)

#         city_name = x_value.strip() if x_value else "Unknown"
#         country_name = "Unknown"

#         # Try geocode city → country
#         try:
#             location = geolocator.geocode(city_name, timeout=10)
#             if location and "country" in location.raw.get("address", {}):
#                 country_name = location.raw["address"]["country"]
#         except Exception:
#             country_name = "Unknown"

#         label = f"{city_name}, {country_name}" if country_name != "Unknown" else city_name

#         result.append({
#             "city": city_name,
#             "country": country_name,
#             "label": label,
#             "visitors": int(visitors)
#         })

#         time.sleep(1)  # important to respect Nominatim rate limits

#     return result
