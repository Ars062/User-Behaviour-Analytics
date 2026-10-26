import pycountry
from geopy.geocoders import Nominatim
import time

geolocator = Nominatim(user_agent="umami-geo")

def normalize_regions(raw):
    if not raw or not isinstance(raw, list):
        return []

    rows = []

    for r in raw:
        if not isinstance(r, dict):
            continue

        x = r.get("x")
        visitors = r.get("y", 0)

        if not x:
            continue

        country_code = None
        region_name = None

        # Case: IN-WB
        if "-" in x:
            country_code, sub_code = x.split("-", 1)
            subdivision = pycountry.subdivisions.get(code=x)
            if subdivision:
                region_name = subdivision.name
        else:
            country_code = x

        country = pycountry.countries.get(alpha_2=country_code)
        country_name = country.name if country else country_code

        if not region_name:
            continue  # skip invalid regions

        # Optional geocoding
        lat = lon = None
        try:
            location = geolocator.geocode(f"{region_name}, {country_name}", timeout=10)
            if location:
                lat = location.latitude
                lon = location.longitude
        except:
            pass

        rows.append({
            "region": region_name,
            "country": country_name,
            "lat": lat,
            "lon": lon,
            "visitors": visitors
        })

        time.sleep(0.5)

    return rows
