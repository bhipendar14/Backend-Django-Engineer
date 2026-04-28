import pandas as pd
import requests
import io

url = "https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv"
response = requests.get(url)
df_cities = pd.read_csv(io.StringIO(response.text))
df_cities['CITY_lower'] = df_cities['CITY'].str.lower()
df_cities['STATE_lower'] = df_cities['STATE_CODE'].str.lower()
df_cities = df_cities.drop_duplicates(subset=['CITY_lower', 'STATE_lower'])

df = pd.read_csv(r"c:\Users\91809\Desktop\Backend Django Engineer\fuel-prices-for-be-assessment.csv")
df['City_lower'] = df['City'].str.strip().str.lower()
df['State_lower'] = df['State'].str.strip().str.lower()

merged = pd.merge(df, df_cities, left_on=['City_lower', 'State_lower'], right_on=['CITY_lower', 'STATE_lower'], how='left')

matched = merged.dropna(subset=['LATITUDE'])
print(f"Total fuel stops: {len(df)}")
print(f"Matched fuel stops: {len(matched)}")
unmatched = merged[merged['LATITUDE'].isna()]
print("Some unmatched stops:")
print(unmatched[['City', 'State']].head(20))
