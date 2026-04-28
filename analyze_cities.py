import pandas as pd

df = pd.read_csv(r"c:\Users\91809\Desktop\Backend Django Engineer\fuel-prices-for-be-assessment.csv")
print(f"Total rows: {len(df)}")
unique_cities = df[['City', 'State']].drop_duplicates()
print(f"Unique City/State combinations: {len(unique_cities)}")
