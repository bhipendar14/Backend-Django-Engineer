import pandas as pd
import requests
import io

url = "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv"
response = requests.get(url)
df_cities = pd.read_csv(io.StringIO(response.text))

print(df_cities.head())
print(f"Columns: {df_cities.columns}")
