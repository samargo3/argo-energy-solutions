"""
Complete Pipeline: Fetch data from Best.Energy API and generate VEM Report
One-command solution to go from API to PDF report
"""

from fetch_bestenergy_data import BestEnergyDataFetcher
from generate_vem_report import VEMReportGenerator
from datetime import datetime


def run_full_pipeline(
    customer_id: str = 'wilson-center',
    baseline_start: str = '2024-01-01',
    baseline_end: str = '2024-01-31',
    report_start: str = '2024-11-01',
    report_end: str = '2024-11-30',
    cost_per_kwh: float = 0.12,
    use_mock: bool = False
):
    """
    Complete pipeline from API fetch to PDF report generation
    
    Args:
        customer_id: Customer/Site ID
        baseline_start: Baseline period start
        baseline_end: Baseline period end
        report_start: Report period start
        report_end: Report period end
        cost_per_kwh: Electricity cost per kWh
        use_mock: Use mock data instead of API (for testing)
    """
    print("="*70)
    print("🚀 FULL VEM REPORT PIPELINE")
    print("="*70)
    print(f"Customer: {customer_id}")
    print(f"Baseline: {baseline_start} to {baseline_end}")
    print(f"Report: {report_start} to {report_end}")
    print("="*70)
    print()
    
    # Step 1: Fetch data from API
    print("STEP 1: Fetching energy data from Best.Energy API")
    print("-"*70)
    
    fetcher = BestEnergyDataFetcher()
    
    # Fetch all data (both baseline and report periods)
    earliest_date = min(baseline_start, report_start)
    latest_date = max(baseline_end, report_end)
    
    if use_mock:
        print("📝 Using mock data for testing...")
        df = fetcher.generate_mock_data(
            customer_id=customer_id,
            start_date=earliest_date,
            end_date=latest_date,
            output_csv='energy_data.csv'
        )
    else:
        df = fetcher.fetch_customer_data(
            customer_id=customer_id,
            start_date=earliest_date,
            end_date=latest_date,
            output_csv='energy_data.csv'
        )
    
    if df.empty:
        print("\n❌ No data fetched. Pipeline stopped.")
        print("💡 Try running with --mock flag for testing:")
        print("   python full_pipeline.py --mock")
        return None
    
    print("\n" + "="*70)
    
    # Step 2: Generate VEM Report
    print("\nSTEP 2: Generating VEM Report")
    print("-"*70)
    
    try:
        generator = VEMReportGenerator(
            csv_path='energy_data.csv',
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            report_start=report_start,
            report_end=report_end,
            cost_per_kwh=cost_per_kwh
        )
        
        # Generate the report
        report_file = f"VEM_Report_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        generator.generate_pdf_report(report_file)
        
        # Print summary
        print("\n" + "="*70)
        print("📊 REPORT SUMMARY")
        print("="*70)
        stats = generator.summary_stats
        print(f"Total Savings: {stats['total_savings_kwh']:,.0f} kWh")
        print(f"Cost Savings: ${stats['total_savings_dollars']:,.2f}")
        print(f"Percent Reduction: {stats['percent_reduction']:.1f}%")
        print(f"Days Analyzed: {stats['num_days']}")
        print(f"Average Daily Savings: {stats['avg_daily_savings_kwh']:,.1f} kWh")
        print("="*70)
        
        print(f"\n✅ PIPELINE COMPLETE!")
        print(f"📄 Report: {report_file}")
        print(f"📊 Data: energy_data.csv")
        print("="*70)
        
        return report_file
        
    except Exception as e:
        print(f"\n❌ Error generating report: {str(e)}")
        raise


def main():
    """Command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Complete pipeline: Fetch Best.Energy data and generate VEM report'
    )
    
    # Data fetch arguments
    parser.add_argument('--customer-id', default='wilson-center', 
                       help='Customer/Site ID (default: wilson-center)')
    parser.add_argument('--mock', action='store_true', 
                       help='Use mock data for testing')
    
    # Report period arguments
    parser.add_argument('--baseline-start', required=True, 
                       help='Baseline start date (YYYY-MM-DD)')
    parser.add_argument('--baseline-end', required=True, 
                       help='Baseline end date (YYYY-MM-DD)')
    parser.add_argument('--report-start', required=True, 
                       help='Report start date (YYYY-MM-DD)')
    parser.add_argument('--report-end', required=True, 
                       help='Report end date (YYYY-MM-DD)')
    
    # Cost argument
    parser.add_argument('--cost-per-kwh', type=float, default=0.12,
                       help='Cost per kWh (default: 0.12)')
    
    args = parser.parse_args()
    
    # Run the full pipeline
    run_full_pipeline(
        customer_id=args.customer_id,
        baseline_start=args.baseline_start,
        baseline_end=args.baseline_end,
        report_start=args.report_start,
        report_end=args.report_end,
        cost_per_kwh=args.cost_per_kwh,
        use_mock=args.mock
    )


if __name__ == "__main__":
    main()

