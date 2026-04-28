from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from shapely.geometry import Point, LineString
from .models import Station

class FuelRouteView(APIView):
    def get(self, request):
        start = request.query_params.get('start')
        finish = request.query_params.get('finish')
        
        if not start or not finish:
            return Response({"error": "Please provide start and finish locations."}, status=status.HTTP_400_BAD_REQUEST)
            
        def geocode(address):
            url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
            headers = {"User-Agent": "FuelRouteAPI/1.0"}
            res = requests.get(url, headers=headers).json()
            if not res:
                return None
            return float(res[0]['lat']), float(res[0]['lon'])

        start_coords = geocode(start)
        finish_coords = geocode(finish)
        
        if not start_coords or not finish_coords:
            return Response({"error": "Could not geocode start or finish location."}, status=status.HTTP_400_BAD_REQUEST)
            
        url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{finish_coords[1]},{finish_coords[0]}?overview=full&geometries=geojson"
        res = requests.get(url).json()
        if res['code'] != 'Ok':
            return Response({"error": "Could not calculate route."}, status=status.HTTP_400_BAD_REQUEST)
            
        route = res['routes'][0]
        coords = route['geometry']['coordinates'] # [lon, lat]
        total_distance = route['distance'] / 1609.34 # meters to miles
        
        line = LineString(coords)
        
        stations = Station.objects.all()
        nearby_stations = []
        
        # 1 degree is approx 69 miles. We look within ~10 miles.
        threshold = 10 / 69.0
        
        for station in stations:
            pt = Point(station.longitude, station.latitude)
            dist = line.distance(pt)
            if dist < threshold:
                fraction = line.project(pt, normalized=True)
                route_dist = fraction * total_distance
                nearby_stations.append({
                    "id": station.opis_truckstop_id,
                    "name": station.name,
                    "city": station.city,
                    "state": station.state,
                    "price": station.retail_price,
                    "lat": station.latitude,
                    "lon": station.longitude,
                    "route_dist": route_dist
                })
                
        # Sort by distance along route
        nearby_stations.sort(key=lambda x: x['route_dist'])
        
        # Algorithm to find optimal stops
        # We start at dist=0, and we want to cover up to total_distance.
        # We can carry up to 500 miles of fuel.
        
        events = []
        # Add a dummy start station if there's no station at 0.
        # We will assume we can get fuel at the start for the price of the nearest station to the start.
        start_price = nearby_stations[0]['price'] if nearby_stations else 3.0
        nearby_stations.insert(0, {
            "id": 0, "name": "Start Location", "city": "Start", "state": "", "price": start_price,
            "lat": start_coords[0], "lon": start_coords[1], "route_dist": 0.0
        })
        
        for idx, s in enumerate(nearby_stations):
            events.append((s['route_dist'], 'enter', s, idx))
            events.append((s['route_dist'] + 500, 'exit', s, idx))
            
        events.sort(key=lambda x: x[0])
        
        active_stations = {} # idx -> station
        
        current_x = 0.0
        total_cost = 0.0
        stops_used = {} # idx -> fuel_bought
        
        for x, event_type, station, idx in events:
            if current_x >= total_distance:
                break
                
            if x > current_x:
                # the interval from current_x to x was powered by the CHEAPEST active station
                if not active_stations:
                    return Response({"error": "Route cannot be completed, distance between stations > 500 miles."}, status=status.HTTP_400_BAD_REQUEST)
                
                cheapest_idx = min(active_stations.keys(), key=lambda k: active_stations[k]['price'])
                cheapest = active_stations[cheapest_idx]
                
                segment_len = min(x, total_distance) - current_x
                fuel_needed = segment_len / 10.0
                cost = fuel_needed * cheapest['price']
                
                total_cost += cost
                stops_used[cheapest_idx] = stops_used.get(cheapest_idx, 0) + fuel_needed
                
                current_x = min(x, total_distance)
                
            if event_type == 'enter':
                active_stations[idx] = station
            elif event_type == 'exit':
                if idx in active_stations:
                    del active_stations[idx]
                    
        if current_x < total_distance:
            return Response({"error": "Route cannot be completed."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Format optimal fuel stops
        fuel_stops = []
        for idx, fuel in stops_used.items():
            if fuel > 0 and nearby_stations[idx]['id'] != 0:
                fuel_stops.append({
                    "station": nearby_stations[idx],
                    "fuel_purchased_gallons": round(fuel, 2),
                    "cost": round(fuel * nearby_stations[idx]['price'], 2)
                })
                
        return Response({
            "start": start,
            "finish": finish,
            "total_distance_miles": round(total_distance, 2),
            "total_cost": round(total_cost, 2),
            "fuel_stops": fuel_stops,
            "route_geojson": route['geometry']
        })
