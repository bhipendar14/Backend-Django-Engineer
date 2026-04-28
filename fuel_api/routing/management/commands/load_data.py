import os
import io
import pandas as pd
import requests
from django.core.management.base import BaseCommand
from routing.models import Station
from django.conf import settings

class Command(BaseCommand):
    help = 'Loads station data from CSVs'

    def handle(self, *args, **kwargs):
        self.stdout.write("Downloading US cities database...")
        url = "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv"
        response = requests.get(url)
        df_cities = pd.read_csv(io.StringIO(response.text))
        
        df_cities['CITY_lower'] = df_cities['CITY'].str.lower()
        df_cities['STATE_lower'] = df_cities['STATE_CODE'].str.lower()
        # Keep first occurrence
        df_cities = df_cities.drop_duplicates(subset=['CITY_lower', 'STATE_lower'])

        self.stdout.write("Loading fuel prices CSV...")
        csv_path = os.path.join(settings.BASE_DIR.parent, "fuel-prices-for-be-assessment.csv")
        df = pd.read_csv(csv_path)
        
        df['City_lower'] = df['City'].astype(str).str.strip().str.lower()
        df['State_lower'] = df['State'].astype(str).str.strip().str.lower()
        
        # Sort by retail price to keep the cheapest one when dropping duplicates
        df = df.sort_values('Retail Price').drop_duplicates(subset=['OPIS Truckstop ID'])

        merged = pd.merge(df, df_cities, left_on=['City_lower', 'State_lower'], right_on=['CITY_lower', 'STATE_lower'], how='left')
        matched = merged.dropna(subset=['LATITUDE'])

        self.stdout.write(f"Found {len(matched)} valid stations with coordinates. Inserting to DB...")
        
        Station.objects.all().delete()
        stations = []
        for index, row in matched.iterrows():
            stations.append(Station(
                opis_truckstop_id=row['OPIS Truckstop ID'],
                name=row['Truckstop Name'],
                address=row['Address'],
                city=row['City'],
                state=row['State'],
                rack_id=row['Rack ID'] if pd.notnull(row['Rack ID']) else None,
                retail_price=row['Retail Price'],
                latitude=row['LATITUDE'],
                longitude=row['LONGITUDE']
            ))
            if len(stations) >= 1000:
                Station.objects.bulk_create(stations)
                stations = []
        
        if stations:
            Station.objects.bulk_create(stations)

        self.stdout.write(self.style.SUCCESS('Successfully loaded station data'))
