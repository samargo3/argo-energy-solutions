"""
Use existing Wilson Center data files to generate VEM report
Since API data is not yet available, use the JSON files you already have
"""

import json
import pandas as pd
from datetime import datetime
from generate_vem_report import VEMReportGenerator


def load_wilson_data_from_json(json_path: str) -> pd.DataFrame:
    """
    Load Wilson Center data from existing JSON file
    
    Args:
        json_path: Path to wilson-center-analysis.json
        
    Returns:
        DataFrame in VEM format (Timestamp, Usage_kWh, Asset_Name)
    """
    print(f"📂 Loading data from: {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    records = []
    
    # Extract channels data
    channels = data.get('channels', [])
    
    for channel in channels:
        asset_name = channel.get('channel', 'Unknown')
        raw_readings = channel.get('rawReadings', [])
        
        print(f"  📊 Processing: {asset_name} ({len(raw_readings)} readings)")
        
        for reading in raw_readings:
            # Unix timestamp to datetime
            ts = reading.get('ts')
            if ts:
                timestamp = pd.to_datetime(ts, unit='s')
                
                # E field is energy in Wh, convert to kWh
                energy_wh = reading.get('E', 0)
                usage_kwh = energy_wh / 1000.0
                
                records.append({
                    'Timestamp': timestamp,
                    'Usage_kWh': usage_kwh,
                    'Asset_Name': asset_name
                })
    
    df = pd.DataFrame(records)
    
    if not df.empty:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values(['Timestamp', 'Asset_Name'])
    
    print(f"✅ Loaded {len(df)} data points")
    print(f"📅 Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    print(f"🏢 Assets: {df['Asset_Name'].nunique()}")
    
    return df


def generate_wilson_vem_report(
    json_path: str = '../data/wilson-center-analysis.json',
    baseline_start: str = '2025-12-01',
    baseline_end: str = '2025-12-15',
    report_start: str = '2025-12-16',
    report_end: str = '2025-12-31',
    cost_per_kwh: float = 0.15
):
    """
    Generate VEM report using existing Wilson Center JSON data
    
    Args:
        json_path: Path to wilson-center-analysis.json
        baseline_start: Baseline period start
        baseline_end: Baseline period end
        report_start: Report period start
        report_end: Report period end
        cost_per_kwh: Cost per kWh ($0.15 from your data)
    """
    print("="*70)
    print("🏢 WILSON CENTER VEM REPORT GENERATOR")
    print("="*70)
    print()
    
    # Step 1: Load and transform data
    df = load_wilson_data_from_json(json_path)
    
    if df.empty:
        print("❌ No data loaded")
        return
    
    # Save to CSV for VEM report generator
    csv_output = 'wilson_center_energy_data.csv'
    df.to_csv(csv_output, index=False)
    print(f"💾 Saved to: {csv_output}")
    print()
    
    # Step 2: Generate VEM Report
    print("="*70)
    print("📊 Generating VEM Report")
    print("="*70)
    print(f"Baseline Period: {baseline_start} to {baseline_end}")
    print(f"Report Period: {report_start} to {report_end}")
    print(f"Cost per kWh: ${cost_per_kwh}")
    print()
    
    try:
        generator = VEMReportGenerator(
            csv_path=csv_output,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            report_start=report_start,
            report_end=report_end,
            cost_per_kwh=cost_per_kwh
        )
        
        # Generate report
        report_file = f"VEM_Report_WilsonCenter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        generator.generate_pdf_report(report_file)
        
        # Print summary
        print()
        print("="*70)
        print("📊 REPORT SUMMARY")
        print("="*70)
        stats = generator.summary_stats
        print(f"Total Baseline Energy: {stats['total_baseline_kwh']:,.2f} kWh")
        print(f"Total Actual Energy: {stats['total_actual_kwh']:,.2f} kWh")
        print(f"Total Savings: {stats['total_savings_kwh']:,.2f} kWh")
        print(f"Cost Impact: ${stats['total_savings_dollars']:,.2f}")
        print(f"Percent Change: {stats['percent_reduction']:.1f}%")
        print(f"Days Analyzed: {stats['num_days']}")
        print()
        print(f"✅ Report generated: {report_file}")
        print("="*70)
        
        return report_file
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate VEM report from existing Wilson Center JSON data'
    )
    parser.add_argument('--json', default='../data/wilson-center-analysis.json',
                       help='Path to wilson-center-analysis.json')
    parser.add_argument('--baseline-start', default='2025-12-01',
                       help='Baseline start (YYYY-MM-DD)')
    parser.add_argument('--baseline-end', default='2025-12-15',
                       help='Baseline end (YYYY-MM-DD)')
    parser.add_argument('--report-start', default='2025-12-16',
                       help='Report start (YYYY-MM-DD)')
    parser.add_argument('--report-end', default='2025-12-31',
                       help='Report end (YYYY-MM-DD)')
    parser.add_argument('--cost', type=float, default=0.15,
                       help='Cost per kWh (default: 0.15)')
    
    args = parser.parse_args()
    
    generate_wilson_vem_report(
        json_path=args.json,
        baseline_start=args.baseline_start,
        baseline_end=args.baseline_end,
        report_start=args.report_start,
        report_end=args.report_end,
        cost_per_kwh=args.cost
    )


if __name__ == "__main__":
    main()

