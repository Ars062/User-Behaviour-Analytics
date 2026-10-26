import pycountry

def normalize_countries(raw):
    """
    Normalize country data from Umami API
    
    Args:
        raw: List of country objects from Umami API (or None)
        
    Returns:
        List of normalized country objects with full names and ISO codes
    """
    #  FIX: Handle None or invalid input
    if raw is None or not isinstance(raw, list):
        return []
    
    result = []
    for c in raw:
        # Skip if not a dict
        if not isinstance(c, dict):
            continue
        
        code = c.get("x", "")
        visitors = c.get("y", 0)
        
        try:
            country = pycountry.countries.get(alpha_2=code)
            result.append({
                "code": code,
                "name": country.name,
                "iso3": country.alpha_3,
                "visitors": visitors
            })
        except:
            result.append({
                "code": code,
                "name": code,
                "iso3": None,
                "visitors": visitors
            })
    
    return result