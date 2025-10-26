
from geopy.geocoders import Nominatim
from utils.llm import LLMProfile
def address_geo_code(address) -> dict:
    LLMProfile.dev_llm()
    geolocator = Nominatim(user_agent="map_test")
    location = geolocator.geocode(address)
    
    return {"latitude": location.latitude, "longitude": location.longitude}
