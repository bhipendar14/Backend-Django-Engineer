import requests
import json

url = "http://127.0.0.1:8000/api/route?start=New+York,+NY&finish=Chicago,+IL"
res = requests.get(url)
print(res.status_code)
data = res.json()
if 'route_geojson' in data:
    del data['route_geojson']
print(json.dumps(data, indent=2))
