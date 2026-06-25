import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_nasa_irradiance(lat, lon):
    """
    Fetches real historical solar irradiance (kWh/m²/day) from NASA POWER API
    for the exact GPS coordinates provided.
    Returns a tuple: (irradiance_value, is_real_data)
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": "20240101",
        "end": "20241231",
        "format": "JSON"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            features = data.get("properties", {}).get("parameter", {}).get("ALLSKY_SFC_SW_DWN", {})
            valid_values = [v for v in features.values() if v >= 0]
            if valid_values:
                return (sum(valid_values) / len(valid_values), True)
        print(f"⚠️ NASA API returned status {response.status_code}, using fallback estimate.")
    except Exception as e:
        print(f"⚠️ NASA API call failed ({e}), using fallback estimate.")
    return (5.0, False)  # Clearly flagged fallback, not silent

def calculate_uppcl_bill(units):
    """
    Applies the actual structural tier slabs from the UPPCL Tariff Order 
    to calculate what the user should be paying for their consumption.
    """
    cost = 0
    remaining_units = units
    
    # Standard UPPCL Domestic Slabs
    slabs = [
        (100, 5.50),  # First 100 units at ₹5.50
        (200, 6.00),  # Next 200 units at ₹6.00
        (200, 6.50),  # Next 200 units at ₹6.50
        (float('inf'), 7.00) # Above 500 units at ₹7.00
    ]
    
    for limit, rate in slabs:
        if remaining_units <= 0:
            break
        chunk = min(remaining_units, limit)
        cost += chunk * rate
        remaining_units -= chunk
        
    # Add minor estimated fixed charges & electricity duty (~10%)
    return round(cost * 1.10, 2)

def running_financial_analysis(area_sqft, lat, lon, monthly_units):
    """
    Computes commercial setup costs, pulls direct dynamic solar physics yields,
    maps real dynamic government subsidies, and evaluates the break-even investment lifecycle.
    """
    # 1. Fetch live location-specific irradiance
# 1. Fetch live location-specific irradiance
    g_irradiance, is_real_data = get_nasa_irradiance(lat, lon)    
    # 2. Map structural system sizing (Standard formula: 100 sqft approx = 1 kWp system)
    system_size_kw = round(float(area_sqft) / 100.0, 1)
    if system_size_kw < 1.0: system_size_kw = 1.0
    
    # 3. Apply core physics equation for generation
    area_sq_meters = float(area_sqft) * 0.092903
    panel_efficiency = 0.18
    performance_ratio = 0.75
    
    daily_generation = area_sq_meters * g_irradiance * panel_efficiency * performance_ratio
    monthly_generation = daily_generation * 30
    yearly_generation = daily_generation * 365
    
    # 4. Calculate actual financial installation costs and PM Surya Ghar subsidies
    cost_per_kw = 55000  # Standard market rate in INR per kW
    total_installation_cost = system_size_kw * cost_per_kw
    
    # Official PM Surya Ghar subsidy math rules: ₹30,000/kW up to 2kW, then ₹18,000/kW for 3rd kW. Max cap ₹78,000
    if system_size_kw >= 3.0:
        subsidy = 78000
    elif system_size_kw == 2.0:
        subsidy = 60000
    else:
        subsidy = 30000 * min(system_size_kw, 2.0)
        
    net_investment = total_installation_cost - subsidy
    
    # 5. Compare current grid cost against solar generation offsets
    current_monthly_cost = calculate_uppcl_bill(monthly_units)
    
    # Calculate what happens to their bill after solar offsets units
    offset_remaining_units = max(0, monthly_units - monthly_generation)
    new_monthly_cost = calculate_uppcl_bill(offset_remaining_units)
    
    monthly_savings = current_monthly_cost - new_monthly_cost
    yearly_savings = monthly_savings * 12
    
    # 6. Payback period analysis
    payback_years = round(net_investment / yearly_savings, 2) if yearly_savings > 0 else float('inf')
    return {
        "irradiance": round(g_irradiance, 2),
        "irradiance_is_real": is_real_data,
        "system_size_kw": system_size_kw,
        "daily_units": round(daily_generation, 2),
        "monthly_units": round(monthly_generation, 2),
        "setup_cost": total_installation_cost,
        "subsidy": subsidy,
        "net_investment": net_investment,
        "current_bill": current_monthly_cost,
        "new_bill": new_monthly_cost,
        "yearly_savings": round(yearly_savings, 2),
        "payback_years": payback_years,
        "excess_units_generated": round(max(0, monthly_generation - monthly_units), 2),
        }


def get_nasa_daily_series(lat, lon):
    """
    Fetches a full year of real daily solar irradiance values from NASA POWER API.
    Returns a tuple: (dict of {date_string: irradiance_value}, is_real_data)
    """
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": "20240101",
        "end": "20241231",
        "format": "JSON"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            features = data.get("properties", {}).get("parameter", {}).get("ALLSKY_SFC_SW_DWN", {})
            clean_series = {date: val for date, val in features.items() if val >= 0}
            if clean_series:
                return (clean_series, True)
        print(f"NASA API returned status {response.status_code}, using fallback series.")
    except Exception as e:
        print(f"NASA API call failed ({e}), using fallback series.")

    # Fallback: synthetic but clearly-labeled seasonal pattern for India
    import datetime
    fallback = {}
    start = datetime.date(2024, 1, 1)
    for i in range(365):
        d = start + datetime.timedelta(days=i)
        month = d.month
        seasonal_factor = {1: 0.75, 2: 0.85, 3: 1.05, 4: 1.25, 5: 1.30, 6: 1.10,
                            7: 0.80, 8: 0.85, 9: 0.95, 10: 1.05, 11: 0.90, 12: 0.70}[month]
        fallback[d.strftime("%Y%m%d")] = round(5.0 * seasonal_factor, 2)
    return (fallback, False)


def build_generation_timeseries(area_sqft, lat, lon):
    """
    Builds daily, weekly, monthly, and yearly generation views from one real
    year of NASA daily irradiance data. All views are derived from the same
    real dataset, not independently estimated.
    """
    import datetime

    daily_irradiance, is_real = get_nasa_daily_series(lat, lon)

    area_sq_meters = float(area_sqft) * 0.092903
    panel_efficiency = 0.18
    performance_ratio = 0.75

    # Real daily generation for every day of the year
    daily_generation = {}
    for date_str, irradiance in sorted(daily_irradiance.items()):
        generation = area_sq_meters * irradiance * panel_efficiency * performance_ratio
        daily_generation[date_str] = round(generation, 2)

    # Last 30 real days, for the "daily view" chart
    last_30_days = dict(list(daily_generation.items())[-30:])

    # Group into weeks (7-day real averages across the year)
    dates_sorted = sorted(daily_generation.keys())
    weekly_generation = {}
    for i in range(0, len(dates_sorted), 7):
        week_dates = dates_sorted[i:i+7]
        week_label = f"Week {i//7 + 1}"
        week_total = sum(daily_generation[d] for d in week_dates)
        weekly_generation[week_label] = round(week_total, 2)

    # Group into real calendar months
    monthly_generation = {}
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for date_str, gen in daily_generation.items():
        month_index = int(date_str[4:6]) - 1
        month_label = month_names[month_index]
        monthly_generation[month_label] = monthly_generation.get(month_label, 0) + gen
    monthly_generation = {k: round(v, 2) for k, v in monthly_generation.items()}

    # Yearly total, real
    yearly_total = round(sum(daily_generation.values()), 2)

    return {
        "is_real_data": is_real,
        "daily_view": last_30_days,
        "weekly_view": weekly_generation,
        "monthly_view": monthly_generation,
        "yearly_total": yearly_total,
    }
