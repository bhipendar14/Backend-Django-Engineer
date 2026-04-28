# Fuel Routing API

This Django application provides an API to calculate the optimal fuel stops for a vehicle traveling between two locations in the USA. It calculates the most cost-effective fueling strategy assuming the vehicle achieves 10 miles per gallon and has a maximum range of 500 miles.

## Demonstration

**Watch the API in action!**
- 🎥 **[Watch the Loom/Demo Video](https://drive.google.com/file/d/1zIrJMAq-t3lOnJocagZQ1CaHKnERHF_6/view?usp=sharing)**
- 📸 **[View the Postman Output Image](https://drive.google.com/file/d/1oc2Prb16-cHlCi8DshCP7aKcrDw8cPB1/view?usp=sharing)**

![Postman Output](https://drive.google.com/uc?id=1oc2Prb16-cHlCi8DshCP7aKcrDw8cPB1)

## Approach & Algorithm

The system geocodes the `start` and `finish` locations and requests a driving route from the free OpenRouteService (OSRM) API. It then identifies all fuel stations within ~10 miles of the route by projecting their coordinates onto the route polyline.

To calculate the **optimal fuel stops**, the application uses a highly efficient continuous sliding-window sweep-line algorithm:
1. Every station can provide fuel for a 500-mile segment starting from its location.
2. At any given point along the route, the vehicle uses fuel purchased from the *cheapest available station* within the preceding 500 miles.
3. The algorithm sweeps along the route, computing exactly how much fuel needs to be bought at each optimal stop to minimize the total cost.

## Setup & Running Locally

1. **Navigate to the API folder**
   ```bash
   cd fuel_api
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install django djangorestframework pandas requests polyline scipy shapely
   ```

4. **Run Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Load Fuel Stations Data**
   Run the custom management command to download US Cities coordinates, merge them with the provided `fuel-prices-for-be-assessment.csv`, and populate the SQLite database. Ensure the CSV is in the root directory (parent of `fuel_api`).
   ```bash
   python manage.py load_data
   ```

6. **Start the Django Development Server**
   ```bash
   python manage.py runserver
   ```

## Testing the API

You can use Postman, `curl`, or your browser to test the API endpoint.

**Endpoint:** `GET /api/route`
**Parameters:**
- `start`: The starting location (e.g. "New York, NY")
- `finish`: The destination (e.g. "Chicago, IL")

**Example Request:**
```
http://127.0.0.1:8000/api/route?start=New+York,+NY&finish=Chicago,+IL
```

**Example Response:**
```json
{
  "start": "New York, NY",
  "finish": "Chicago, IL",
  "total_distance_miles": 794.73,
  "total_cost": 241.61,
  "fuel_stops": [
    {
      "station": {
        "id": 62790,
        "name": "7-ELEVEN #40084",
        "city": "Palisades Park",
        "state": "NJ",
        "price": 3.099,
        "lat": 40.846238,
        "lon": -73.995436,
        "route_dist": 7.56
      },
      "fuel_purchased_gallons": 5.9,
      "cost": 18.27
    },
    ...
  ],
  "route_geojson": { ... }
}
```

You can plot the returned `route_geojson` on any mapping tool (like geojson.io) to visualize the exact path!
