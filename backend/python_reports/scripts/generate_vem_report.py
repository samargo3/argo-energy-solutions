"""
VEM (Verification of Energy Management) Report Generator
Generates professional PDF reports comparing baseline vs actual energy usage
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from fpdf import FPDF
import os
from typing import Tuple, Dict

# Set style for plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class VEMReportGenerator:
    """Generate Verification of Energy Management reports"""
    
    def __init__(self, csv_path: str, 
                 baseline_start: str, baseline_end: str,
                 report_start: str, report_end: str,
                 cost_per_kwh: float = 0.12):
        """
        Initialize the VEM report generator
        
        Args:
            csv_path: Path to CSV file (Timestamp, Usage_kWh, Asset_Name)
            baseline_start: Baseline period start (YYYY-MM-DD)
            baseline_end: Baseline period end (YYYY-MM-DD)
            report_start: Report period start (YYYY-MM-DD)
            report_end: Report period end (YYYY-MM-DD)
            cost_per_kwh: Cost per kWh for savings calculation
        """
        self.csv_path = csv_path
        self.baseline_start = pd.to_datetime(baseline_start)
        self.baseline_end = pd.to_datetime(baseline_end)
        self.report_start = pd.to_datetime(report_start)
        self.report_end = pd.to_datetime(report_end)
        self.cost_per_kwh = cost_per_kwh
        
        # Load and prepare data
        self.df = self._load_data()
        self.baseline_data = self._filter_period(self.baseline_start, self.baseline_end)
        self.report_data = self._filter_period(self.report_start, self.report_end)
        
        # Calculate baseline curve and savings
        self.baseline_curve = self._calculate_baseline_curve()
        self.savings_df = self._calculate_savings()
        self.summary_stats = self._calculate_summary_stats()
        
    def _load_data(self) -> pd.DataFrame:
        """Load and prepare the energy data"""
        df = pd.read_csv(self.csv_path)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Date'] = df['Timestamp'].dt.date
        df['Day_of_Week'] = df['Timestamp'].dt.day_name()
        df['Hour'] = df['Timestamp'].dt.hour
        df['Weekday'] = df['Timestamp'].dt.weekday  # 0=Monday, 6=Sunday
        return df
    
    def _filter_period(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        """Filter data for a specific period"""
        mask = (self.df['Timestamp'] >= start) & (self.df['Timestamp'] <= end)
        return self.df[mask].copy()
    
    def _calculate_baseline_curve(self) -> pd.DataFrame:
        """
        Calculate the baseline curve: average usage per day of week
        For each day in the report period, find the baseline value
        """
        # Calculate average usage per day of week from baseline period
        baseline_avg_by_dow = self.baseline_data.groupby('Weekday')['Usage_kWh'].mean()
        
        # Create baseline curve for report period
        report_dates = pd.date_range(self.report_start, self.report_end, freq='D')
        baseline_curve = []
        
        for date in report_dates:
            weekday = date.weekday()
            baseline_value = baseline_avg_by_dow.get(weekday, 0)
            baseline_curve.append({
                'Date': date.date(),
                'Weekday': weekday,
                'Baseline_kWh': baseline_value
            })
        
        return pd.DataFrame(baseline_curve)
    
    def _calculate_savings(self) -> pd.DataFrame:
        """Calculate daily savings comparing actual to baseline"""
        # Aggregate report period data by date
        daily_actual = self.report_data.groupby('Date')['Usage_kWh'].sum().reset_index()
        daily_actual.columns = ['Date', 'Actual_kWh']
        
        # Merge with baseline curve
        savings_df = self.baseline_curve.merge(daily_actual, on='Date', how='left')
        savings_df['Actual_kWh'] = savings_df['Actual_kWh'].fillna(0)
        
        # Calculate savings
        savings_df['Savings_kWh'] = savings_df['Baseline_kWh'] - savings_df['Actual_kWh']
        savings_df['Savings_Dollars'] = savings_df['Savings_kWh'] * self.cost_per_kwh
        savings_df['Savings_Percent'] = (savings_df['Savings_kWh'] / savings_df['Baseline_kWh'] * 100).fillna(0)
        
        return savings_df
    
    def _calculate_summary_stats(self) -> Dict:
        """Calculate summary statistics for the report"""
        total_baseline = self.savings_df['Baseline_kWh'].sum()
        total_actual = self.savings_df['Actual_kWh'].sum()
        total_savings_kwh = self.savings_df['Savings_kWh'].sum()
        total_savings_dollars = total_savings_kwh * self.cost_per_kwh
        percent_reduction = (total_savings_kwh / total_baseline * 100) if total_baseline > 0 else 0
        
        # Asset-specific savings
        asset_savings = self._calculate_asset_savings()
        
        return {
            'total_baseline_kwh': total_baseline,
            'total_actual_kwh': total_actual,
            'total_savings_kwh': total_savings_kwh,
            'total_savings_dollars': total_savings_dollars,
            'percent_reduction': percent_reduction,
            'asset_savings': asset_savings,
            'num_days': len(self.savings_df),
            'avg_daily_savings_kwh': total_savings_kwh / len(self.savings_df) if len(self.savings_df) > 0 else 0
        }
    
    def _calculate_asset_savings(self) -> pd.DataFrame:
        """Calculate savings by asset"""
        # Baseline by asset and day of week
        baseline_by_asset = self.baseline_data.groupby(['Asset_Name', 'Weekday'])['Usage_kWh'].mean()
        
        # Actual usage by asset
        report_with_weekday = self.report_data.copy()
        report_by_asset = report_with_weekday.groupby('Asset_Name').agg({
            'Usage_kWh': 'sum',
            'Weekday': lambda x: x.mode()[0] if len(x) > 0 else 0  # Most common weekday
        }).reset_index()
        
        asset_list = []
        for _, row in report_by_asset.iterrows():
            asset_name = row['Asset_Name']
            actual_kwh = row['Usage_kWh']
            
            # Get baseline for this asset
            try:
                baseline_kwh = baseline_by_asset[asset_name].mean() * len(self.savings_df)
            except KeyError:
                baseline_kwh = 0
            
            savings_kwh = baseline_kwh - actual_kwh
            variance_percent = (savings_kwh / baseline_kwh * 100) if baseline_kwh > 0 else 0
            
            asset_list.append({
                'Asset': asset_name,
                'Baseline_kWh': baseline_kwh,
                'Actual_kWh': actual_kwh,
                'Savings_kWh': savings_kwh,
                'Variance_%': variance_percent
            })
        
        if not asset_list:
            # Return empty DataFrame with correct columns if no assets
            return pd.DataFrame(columns=['Asset', 'Baseline_kWh', 'Actual_kWh', 'Savings_kWh', 'Variance_%'])
        
        return pd.DataFrame(asset_list).sort_values('Savings_kWh', ascending=False)
    
    def calculate_degree_days(self, temperature_data: pd.DataFrame = None) -> float:
        """
        Placeholder for weather normalization
        
        Args:
            temperature_data: DataFrame with Date and Temperature columns
            
        Returns:
            Normalized savings value
        """
        # TODO: Implement degree-day normalization
        # For now, return raw savings
        return self.summary_stats['total_savings_kwh']
    
    def generate_savings_chart(self, output_path: str = 'charts/savings_chart.png'):
        """Generate the main savings chart with fill between"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = pd.to_datetime(self.savings_df['Date'])
        baseline = self.savings_df['Baseline_kWh']
        actual = self.savings_df['Actual_kWh']
        
        # Plot lines
        ax.plot(dates, baseline, label='Baseline', color='#2563eb', linewidth=2)
        ax.plot(dates, actual, label='Actual Usage', color='#1f2937', linewidth=2)
        
        # Fill between - GREEN for savings, RED for waste
        ax.fill_between(dates, baseline, actual, 
                         where=(actual < baseline), 
                         color='#10b981', alpha=0.3, label='Savings')
        ax.fill_between(dates, baseline, actual, 
                         where=(actual >= baseline), 
                         color='#ef4444', alpha=0.3, label='Over Baseline')
        
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Energy Usage (kWh)', fontsize=12, fontweight='bold')
        ax.set_title('Energy Savings Verification\nBaseline vs. Actual Usage', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_day_of_week_chart(self, output_path: str = 'charts/day_of_week.png'):
        """Generate day of week profile chart"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Calculate averages
        baseline_dow = self.baseline_data.groupby('Day_of_Week')['Usage_kWh'].mean()
        report_dow = self.report_data.groupby('Day_of_Week')['Usage_kWh'].mean()
        
        # Order days
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        baseline_dow = baseline_dow.reindex(days_order, fill_value=0)
        report_dow = report_dow.reindex(days_order, fill_value=0)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(len(days_order))
        width = 0.35
        
        ax.bar(x - width/2, baseline_dow, width, label='Baseline', color='#2563eb', alpha=0.8)
        ax.bar(x + width/2, report_dow, width, label='Report Period', color='#10b981', alpha=0.8)
        
        ax.set_xlabel('Day of Week', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average Usage (kWh)', fontsize=12, fontweight='bold')
        ax.set_title('Average Energy Usage by Day of Week', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(days_order, rotation=45, ha='right')
        ax.legend(fontsize=10)
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_heatmap(self, output_path: str = 'charts/heatmap.png'):
        """Generate hourly usage heatmap"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create pivot table for heatmap
        heatmap_data = self.report_data.groupby(['Weekday', 'Hour'])['Usage_kWh'].mean().reset_index()
        heatmap_pivot = heatmap_data.pivot(index='Weekday', columns='Hour', values='Usage_kWh')
        
        # Order by weekday
        day_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        heatmap_pivot = heatmap_pivot.reindex(range(7), fill_value=0)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.heatmap(heatmap_pivot, cmap='YlOrRd', annot=False, fmt='.0f', 
                    cbar_kws={'label': 'kWh'}, ax=ax)
        
        ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
        ax.set_ylabel('Day of Week', fontsize=12, fontweight='bold')
        ax.set_title('Energy Usage Heatmap\nHour of Day vs. Day of Week', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.set_yticklabels(day_labels, rotation=0)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_pdf_report(self, output_path: str = 'VEM_Replication_Report.pdf'):
        """Generate the complete PDF report"""
        # Generate all charts first
        savings_chart = self.generate_savings_chart()
        dow_chart = self.generate_day_of_week_chart()
        heatmap = self.generate_heatmap()
        
        # Create PDF
        pdf = VEMPDF()
        
        # Page 1: Executive Summary
        pdf.add_page()
        pdf.add_executive_summary(
            self.summary_stats,
            self.baseline_start,
            self.baseline_end,
            self.report_start,
            self.report_end
        )
        
        # Page 2: Visual Analysis
        pdf.add_page()
        pdf.add_visual_analysis(savings_chart, dow_chart)
        
        # Page 3: Detailed Breakdown
        pdf.add_page()
        pdf.add_detailed_breakdown(heatmap, self.summary_stats['asset_savings'])
        
        # Save PDF
        pdf.output(output_path)
        print(f"✅ Report generated: {output_path}")
        
        return output_path


class VEMPDF(FPDF):
    """Custom PDF class for VEM reports"""
    
    def header(self):
        """Add header to each page"""
        self.set_font('Arial', 'B', 16)
        self.set_text_color(37, 99, 235)  # Blue
        self.cell(0, 10, 'Verification of Energy Management (VEM) Report', 0, 1, 'C')
        self.set_text_color(0, 0, 0)
        self.ln(5)
    
    def footer(self):
        """Add footer to each page"""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def add_executive_summary(self, stats: Dict, 
                             baseline_start, baseline_end,
                             report_start, report_end):
        """Add executive summary page"""
        self.set_font('Arial', 'B', 18)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'Executive Scorecard', 0, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.ln(10)
        
        # Period information
        self.set_font('Arial', '', 11)
        self.cell(0, 8, f'Baseline Period: {baseline_start.strftime("%Y-%m-%d")} to {baseline_end.strftime("%Y-%m-%d")}', 0, 1)
        self.cell(0, 8, f'Report Period: {report_start.strftime("%Y-%m-%d")} to {report_end.strftime("%Y-%m-%d")}', 0, 1)
        self.ln(10)
        
        # Key Metrics - Large boxes
        metrics = [
            ('Total Savings', f"{stats['total_savings_kwh']:,.0f} kWh", '#10b981'),
            ('Cost Savings', f"${stats['total_savings_dollars']:,.2f}", '#10b981'),
            ('Reduction', f"{stats['percent_reduction']:.1f}%", '#10b981')
        ]
        
        x_start = 20
        box_width = 55
        box_height = 30
        
        for i, (label, value, color) in enumerate(metrics):
            x = x_start + (i * (box_width + 5))
            self.set_xy(x, self.get_y())
            
            # Draw colored box
            rgb = self._hex_to_rgb(color)
            self.set_fill_color(*rgb)
            self.rect(x, self.get_y(), box_width, box_height, 'F')
            
            # Add text
            self.set_xy(x, self.get_y() + 5)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(255, 255, 255)
            self.cell(box_width, 8, label, 0, 0, 'C')
            
            self.set_xy(x, self.get_y() + 10)
            self.set_font('Arial', 'B', 14)
            self.cell(box_width, 10, value, 0, 0, 'C')
        
        self.set_text_color(0, 0, 0)
        self.ln(box_height + 15)
        
        # Summary text
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 8, 
            f"Energy usage during the report period was {abs(stats['percent_reduction']):.1f}% "
            f"{'lower' if stats['percent_reduction'] > 0 else 'higher'} than the baseline period, "
            f"resulting in {abs(stats['total_savings_kwh']):,.0f} kWh of "
            f"{'savings' if stats['total_savings_kwh'] > 0 else 'additional consumption'}. "
            f"This translates to ${abs(stats['total_savings_dollars']):,.2f} in "
            f"{'cost savings' if stats['total_savings_dollars'] > 0 else 'additional costs'}."
        )
        self.ln(10)
        
        # Additional stats
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'Additional Metrics:', 0, 1)
        self.set_font('Arial', '', 11)
        self.cell(0, 7, f"- Total Days Analyzed: {stats['num_days']}", 0, 1)
        self.cell(0, 7, f"- Average Daily Savings: {stats['avg_daily_savings_kwh']:,.1f} kWh", 0, 1)
        self.cell(0, 7, f"- Baseline Total: {stats['total_baseline_kwh']:,.0f} kWh", 0, 1)
        self.cell(0, 7, f"- Actual Total: {stats['total_actual_kwh']:,.0f} kWh", 0, 1)
    
    def add_visual_analysis(self, savings_chart_path: str, dow_chart_path: str):
        """Add visual analysis page"""
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'Visual Analysis', 0, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.ln(10)
        
        # Savings chart
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'Baseline vs. Actual Usage Over Time', 0, 1)
        self.image(savings_chart_path, x=10, w=190)
        self.ln(10)
        
        # Day of week chart
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'Usage Profile by Day of Week', 0, 1)
        self.image(dow_chart_path, x=10, w=190)
    
    def add_detailed_breakdown(self, heatmap_path: str, asset_savings: pd.DataFrame):
        """Add detailed breakdown page"""
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(37, 99, 235)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, 'Detailed Analysis', 0, 1, 'C', 1)
        self.set_text_color(0, 0, 0)
        self.ln(10)
        
        # Heatmap
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'Operational Hours Heatmap', 0, 1)
        self.image(heatmap_path, x=10, w=190)
        self.ln(10)
        
        # Asset-specific table
        self.set_font('Arial', 'B', 12)
        self.cell(0, 8, 'Asset-Specific Variance from Baseline', 0, 1)
        self.ln(5)
        
        # Table header
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(200, 220, 255)
        col_widths = [55, 30, 30, 30, 30]
        headers = ['Asset', 'Baseline (kWh)', 'Actual (kWh)', 'Savings (kWh)', 'Variance (%)']
        
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 7, header, 1, 0, 'C', 1)
        self.ln()
        
        # Table data
        self.set_font('Arial', '', 8)
        for _, row in asset_savings.head(15).iterrows():  # Top 15 assets
            self.cell(col_widths[0], 6, str(row['Asset'])[:30], 1, 0, 'L')
            self.cell(col_widths[1], 6, f"{row['Baseline_kWh']:,.0f}", 1, 0, 'R')
            self.cell(col_widths[2], 6, f"{row['Actual_kWh']:,.0f}", 1, 0, 'R')
            
            # Color code savings
            savings = row['Savings_kWh']
            if savings > 0:
                self.set_text_color(16, 185, 129)  # Green
            else:
                self.set_text_color(239, 68, 68)  # Red
            
            self.cell(col_widths[3], 6, f"{savings:,.0f}", 1, 0, 'R')
            self.cell(col_widths[4], 6, f"{row['Variance_%']:.1f}%", 1, 0, 'R')
            self.set_text_color(0, 0, 0)
            self.ln()
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def main():
    """Main function to generate the report"""
    # Configuration
    CSV_PATH = 'energy_data.csv'
    BASELINE_START = '2024-01-01'
    BASELINE_END = '2024-01-31'
    REPORT_START = '2024-11-01'
    REPORT_END = '2024-11-30'
    COST_PER_KWH = 0.12
    
    print("🔄 Generating VEM Report...")
    print(f"📁 Loading data from: {CSV_PATH}")
    print(f"📅 Baseline Period: {BASELINE_START} to {BASELINE_END}")
    print(f"📅 Report Period: {REPORT_START} to {REPORT_END}")
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
        output_file = generator.generate_pdf_report('VEM_Replication_Report.pdf')
        
        # Print summary
        print("\n" + "="*60)
        print("📊 REPORT SUMMARY")
        print("="*60)
        stats = generator.summary_stats
        print(f"Total Savings: {stats['total_savings_kwh']:,.0f} kWh (${stats['total_savings_dollars']:,.2f})")
        print(f"Percent Reduction: {stats['percent_reduction']:.1f}%")
        print(f"Days Analyzed: {stats['num_days']}")
        print(f"Average Daily Savings: {stats['avg_daily_savings_kwh']:,.1f} kWh")
        print("="*60)
        print(f"\n✅ Report successfully generated: {output_file}")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find {CSV_PATH}")
        print("Please ensure the CSV file exists with columns: Timestamp, Usage_kWh, Asset_Name")
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        raise


if __name__ == "__main__":
    main()

