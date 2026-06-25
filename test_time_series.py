from solar_calculator import build_generation_timeseries

result = build_generation_timeseries(area_sqft=300, lat=26.8467, lon=80.9462)

print("Is real data:", result["is_real_data"])
print("Yearly total:", result["yearly_total"])
print("\nMonthly view:")
for month, val in result["monthly_view"].items():
    print(f"  {month}: {val}")
print("\nNumber of weekly buckets:", len(result["weekly_view"]))
print("Number of days in daily view:", len(result["daily_view"]))