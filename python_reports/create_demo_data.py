"""
Create comprehensive demo data for VEM report
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set random seed for reproducibility
np.random.seed(42)

# Date range: Full month for baseline + report period
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 31, 23, 0, 0)

# Generate hourly timestamps
timestamps = pd.date_range(start=start_date, end=end_date, freq='H')

# Assets
assets = ['RTU-1', 'RTU-2', 'Kitchen Panel', 'Lighting', '1st Floor Panel']

# Generate realistic energy patterns
data = []

for asset in assets:
    # Base load depends on asset type
    if 'RTU' in asset:
        base_load = 120  # HVAC units
        peak_variation = 80
    elif 'Kitchen' in asset:
        base_load = 50
        peak_variation = 60
    elif 'Lighting' in asset:
        base_load = 30
        peak_variation = 20
    else:
        base_load = 40
        peak_variation = 30
    
    for ts in timestamps:
        hour = ts.hour
        weekday = ts.weekday()
        
        # Create patterns:
        # - Higher usage during business hours (8am-6pm)
        # - Lower usage on weekends
        # - Higher usage in first half of month (baseline)
        # - Lower usage in second half (report period - showing savings)
        
        # Time of day pattern
        if 8 <= hour <= 18:
            time_multiplier = 1.4  # Peak hours
        elif 6 <= hour < 8 or 18 < hour <= 22:
            time_multiplier = 1.0  # Shoulder hours
        else:
            time_multiplier = 0.6  # Off hours
        
        # Day of week pattern
        if weekday >= 5:  # Weekend
            dow_multiplier = 0.7
        else:  # Weekday
            dow_multiplier = 1.0
        
        # Baseline vs Report period (report shows improvement)
        if ts.day <= 15:  # Baseline period
            period_multiplier = 1.0
        else:  # Report period - showing 15-20% savings
            period_multiplier = 0.82  # 18% reduction
        
        # Calculate usage with some randomness
        usage = base_load * time_multiplier * dow_multiplier * period_multiplier
        usage += np.random.normal(0, peak_variation * 0.15)  # Add noise
        usage = max(5, usage)  # Ensure positive
        
        data.append({
            'Timestamp': ts,
            'Usage_kWh': round(usage, 2),
            'Asset_Name': asset
        })

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
output_file = 'demo_energy_data.csv'
df.to_csv(output_file, index=False)

print(f"✅ Created demo data: {output_file}")
print(f"📊 Total records: {len(df):,}")
print(f"📅 Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
print(f"🏢 Assets: {', '.join(df['Asset_Name'].unique())}")
print(f"📈 Total energy: {df['Usage_kWh'].sum():,.1f} kWh")
print()
print("Sample data:")
print(df.head(10))
print()
print(f"Baseline period (Jan 1-15): {len(df[df['Timestamp'] <= '2024-01-15']):,} records")
print(f"Report period (Jan 16-31): {len(df[df['Timestamp'] > '2024-01-15']):,} records")

