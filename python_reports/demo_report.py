"""
Quick demo script to generate VEM report with sample data
"""

from generate_vem_report import VEMReportGenerator
from datetime import datetime

print("="*70)
print("🎯 VEM REPORT DEMO - GENERATING SAMPLE REPORT")
print("="*70)
print()

# Configuration
CSV_PATH = 'demo_energy_data.csv'
BASELINE_START = '2024-01-01'
BASELINE_END = '2024-01-15'
REPORT_START = '2024-01-16'
REPORT_END = '2024-01-31'
COST_PER_KWH = 0.15  # $0.15 per kWh

print(f"📁 Using data: {CSV_PATH}")
print(f"📅 Baseline Period: {BASELINE_START} to {BASELINE_END}")
print(f"📅 Report Period: {REPORT_START} to {REPORT_END}")
print(f"💰 Cost per kWh: ${COST_PER_KWH}")
print()
print("🔄 Generating report...")
print()

try:
    # Initialize generator
    generator = VEMReportGenerator(
        csv_path=CSV_PATH,
        baseline_start=BASELINE_START,
        baseline_end=BASELINE_END,
        report_start=REPORT_START,
        report_end=REPORT_END,
        cost_per_kwh=COST_PER_KWH
    )
    
    # Generate report
    output_file = f"Demo_VEM_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    generator.generate_pdf_report(output_file)
    
    # Print summary
    print("="*70)
    print("📊 REPORT SUMMARY")
    print("="*70)
    stats = generator.summary_stats
    print(f"Total Baseline Energy:    {stats['total_baseline_kwh']:>12,.1f} kWh")
    print(f"Total Actual Energy:      {stats['total_actual_kwh']:>12,.1f} kWh")
    print(f"Total Savings:            {stats['total_savings_kwh']:>12,.1f} kWh")
    print(f"Cost Impact:              ${stats['total_savings_dollars']:>11,.2f}")
    print(f"Percent Reduction:        {stats['percent_reduction']:>12.1f}%")
    print(f"Days Analyzed:            {stats['num_days']:>12}")
    print(f"Average Daily Savings:    {stats['avg_daily_savings_kwh']:>12,.1f} kWh")
    print("="*70)
    print()
    print(f"✅ Report successfully generated: {output_file}")
    print()
    print("📄 The PDF includes:")
    print("   • Page 1: Executive Scorecard with key metrics")
    print("   • Page 2: Savings Chart and Day of Week Profile")
    print("   • Page 3: Hourly Heatmap")
    print("   • Page 4: Asset-level Granular Data Table")
    print()
    print("="*70)
    
except FileNotFoundError as e:
    print(f"❌ Error: Could not find {CSV_PATH}")
    print(f"   {str(e)}")
    print("Please ensure the CSV file exists with columns: Timestamp, Usage_kWh, Asset_Name")
except Exception as e:
    print(f"❌ Error generating report: {str(e)}")
    import traceback
    traceback.print_exc()

