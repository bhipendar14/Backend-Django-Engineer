import requests
import polyline
import numpy as np
from scipy.spatial import KDTree

def geocode(address):
    url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
    headers = {"User-Agent": "FuelRouteAPI/1.0"}
    res = requests.get(url, headers=headers).json()
    if not res:
        return None
    return float(res[0]['lat']), float(res[0]['lon'])

def get_route(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    res = requests.get(url).json()
    if res['code'] != 'Ok':
        return None
    return res['routes'][0]

start_coords = geocode("New York, NY")
finish_coords = geocode("Chicago, IL")
print(start_coords, finish_coords)

route = get_route(start_coords[0], start_coords[1], finish_coords[0], finish_coords[1])
coords = route['geometry']['coordinates'] # [lon, lat]
distance = route['distance'] / 1609.34 # meters to miles
print(f"Total distance: {distance} miles")
