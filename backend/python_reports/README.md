# VEM (Verification of Energy Management) Report Generator

Professional Python script for generating energy savings verification reports in PDF format with Best.Energy API integration.

## Features

- ✅ **Best.Energy API Integration** - Fetch data directly from API
- ✅ Baseline vs. Actual Usage Comparison
- ✅ Day-of-Week Analysis
- ✅ Savings Calculation with Green/Red Fill
- ✅ Hourly Heatmap
- ✅ Asset-Specific Breakdown
- ✅ Professional PDF Output
- ✅ Weather Normalization Placeholder
- ✅ Mock Data Generation for Testing
- ✅ Full Pipeline (API → CSV → PDF)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start (Recommended)

### Option 1: Full Pipeline (API to PDF in one command)

```bash
# With real API data
python full_pipeline.py \
  --customer-id wilson-center \
  --baseline-start 2024-01-01 \
  --baseline-end 2024-01-31 \
  --report-start 2024-11-01 \
  --report-end 2024-11-30 \
  --cost-per-kwh 0.12

# With mock data (for testing)
python full_pipeline.py \
  --mock \
  --baseline-start 2024-01-01 \
  --baseline-end 2024-01-31 \
  --report-start 2024-11-01 \
  --report-end 2024-11-30
```

This will:
1. Fetch data from Best.Energy API
2. Format it as CSV
3. Generate VEM report PDF
4. All in one command!

## CSV Format Required

Your `energy_data.csv` should have these columns:

```csv
Timestamp,Usage_kWh,Asset_Name
2024-01-01 00:00:00,125.5,RTU-1
2024-01-01 01:00:00,110.3,RTU-1
2024-01-01 00:00:00,45.2,Kitchen Panel
```

## Usage

### Basic Usage

```bash
python generate_vem_report.py
```

### Custom Configuration

Edit the `main()` function in the script:

```python
CSV_PATH = 'your_data.csv'
BASELINE_START = '2024-01-01'
BASELINE_END = '2024-01-31'
REPORT_START = '2024-11-01'
REPORT_END = '2024-11-30'
COST_PER_KWH = 0.12  # dollars per kWh
```

### Programmatic Usage

```python
from generate_vem_report import VEMReportGenerator

generator = VEMReportGenerator(
    csv_path='energy_data.csv',
    baseline_start='2024-01-01',
    baseline_end='2024-01-31',
    report_start='2024-11-01',
    report_end='2024-11-30',
    cost_per_kwh=0.12
)

# Generate full report
generator.generate_pdf_report('MyReport.pdf')

# Or generate individual charts
generator.generate_savings_chart('savings.png')
generator.generate_day_of_week_chart('dow.png')
generator.generate_heatmap('heatmap.png')

# Access calculated data
print(generator.summary_stats)
print(generator.savings_df)
```

## Report Structure

### Page 1: Executive Scorecard
- **Total Savings (kWh)** - Bold metric box
- **Cost Savings ($)** - Bold metric box
- **Percent Reduction** - Bold metric box
- Summary narrative
- Additional metrics (days analyzed, averages, etc.)

### Page 2: Visual Analysis
- **Savings Chart** - Line chart with green/red fill between baseline and actual
- **Day of Week Profile** - Bar chart comparing baseline vs actual by day

### Page 3: Detailed Analysis
- **Hourly Heatmap** - Day of week vs. hour of day usage patterns
- **Asset Table** - Top 15 assets with variance from baseline

## Baseline Calculation Logic

The script uses day-of-week matching:

1. **Calculate Baseline Average**: For each day of the week (Mon-Sun), calculate the average usage from the baseline period
2. **Match Report Days**: For each day in the report period, use the corresponding day-of-week baseline
3. **Calculate Savings**: `Savings = Baseline - Actual`
   - Positive = Energy saved (green)
   - Negative = Over baseline (red)

Example:
- Report date: Monday, Nov 1st
- Baseline: Average of all Mondays in Jan 2024
- Savings: Baseline Monday avg - Nov 1st actual

## Weather Normalization

Placeholder function included for future enhancement:

```python
def calculate_degree_days(self, temperature_data: pd.DataFrame = None):
    # TODO: Implement HDD/CDD normalization
    pass
```

To implement:
1. Add temperature data column to CSV
2. Calculate Heating/Cooling Degree Days
3. Normalize baseline by degree days

## Output

The script generates:
- `VEM_Replication_Report.pdf` - Main report
- `charts/savings_chart.png` - Savings visualization
- `charts/day_of_week.png` - Day-of-week comparison
- `charts/heatmap.png` - Hourly usage heatmap

## Customization

### Change Colors

Edit the hex colors in the code:

```python
# In generate_savings_chart()
color='#10b981'  # Green for savings
color='#ef4444'  # Red for waste
color='#2563eb'  # Blue for baseline
```

### Add More Charts

Extend the `VEMReportGenerator` class:

```python
def generate_monthly_trend(self):
    monthly = self.report_data.resample('M', on='Timestamp')['Usage_kWh'].sum()
    # ... create chart
```

### Modify PDF Layout

Extend the `VEMPDF` class:

```python
def add_custom_page(self):
    self.add_page()
    # ... add content
```

## Troubleshooting

### Error: File not found
- Ensure `energy_data.csv` is in the same directory as the script
- Or provide full path: `CSV_PATH = '/full/path/to/energy_data.csv'`

### Error: No module named 'fpdf'
- Run: `pip install fpdf2` (not `fpdf`)

### Charts look weird
- Ensure data has consistent timestamps
- Check for missing values in Usage_kWh
- Verify Asset_Name column exists

### Negative savings
- This is normal! It means you used MORE than baseline
- The report will show red fill and mark it appropriately

## Example Output

```
🔄 Generating VEM Report...
📁 Loading data from: energy_data.csv
📅 Baseline Period: 2024-01-01 to 2024-01-31
📅 Report Period: 2024-11-01 to 2024-11-30

============================================================
📊 REPORT SUMMARY
============================================================
Total Savings: 2,450 kWh ($294.00)
Percent Reduction: 12.5%
Days Analyzed: 30
Average Daily Savings: 81.7 kWh
============================================================

✅ Report successfully generated: VEM_Replication_Report.pdf
```

## Advanced Features

### Batch Processing

Process multiple sites:

```python
sites = ['Site_A', 'Site_B', 'Site_C']
for site in sites:
    site_data = df[df['Site'] == site]
    site_data.to_csv(f'{site}_data.csv')
    
    generator = VEMReportGenerator(
        csv_path=f'{site}_data.csv',
        # ... other params
    )
    generator.generate_pdf_report(f'{site}_VEM_Report.pdf')
```

### Compare Multiple Periods

```python
periods = [
    ('2024-Q1', '2024-01-01', '2024-03-31'),
    ('2024-Q2', '2024-04-01', '2024-06-30'),
]

for name, start, end in periods:
    # ... generate report for each period
```

## License

MIT License - Feel free to modify and use for your projects

## Support

For issues or questions:
1. Check the CSV format matches requirements
2. Verify date formats are correct (YYYY-MM-DD)
3. Ensure all required packages are installed

