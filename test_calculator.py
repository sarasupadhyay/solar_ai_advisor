from solar_calculator import running_financial_analysis  # replace YOUR_FILENAME_HERE

result = running_financial_analysis(
    area_sqft=300,
    lat=26.8467,
    lon=80.9462,
    monthly_units=250
)

for key, value in result.items():
    print(f"{key}: {value}")