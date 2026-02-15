"""
Electrical Health Screening Report — PDF Generator

Generates a professional Argo-branded PDF report covering voltage stability,
current peaks, frequency excursions, neutral current, and THD analysis.

Following Argo governance: Stage 4 (Deliver — Presentation)
Charts via matplotlib, PDF assembly via fpdf2.
"""

import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from fpdf import FPDF

# Chart style
plt.style.use('seaborn-v0_8-darkgrid')

# Argo brand palette
ARGO_BLUE = (37, 99, 235)
ARGO_DARK = (31, 41, 55)
ARGO_GREEN = (16, 185, 129)
ARGO_RED = (239, 68, 68)
ARGO_AMBER = (245, 158, 11)
ARGO_GRAY = (107, 114, 128)
WHITE = (255, 255, 255)


# ═══════════════════════════════════════════════════════════════════════
# Chart Generation
# ═══════════════════════════════════════════════════════════════════════

def _parse_dates(trend: List[Dict], key: str = 'date'):
    """Convert date strings to datetime objects for plotting."""
    from datetime import date as _date
    dates = []
    for entry in trend:
        d = entry[key]
        if isinstance(d, str):
            dates.append(datetime.strptime(d, '%Y-%m-%d'))
        elif isinstance(d, _date):
            dates.append(datetime.combine(d, datetime.min.time()))
        else:
            dates.append(d)
    return dates


def generate_voltage_chart(voltage_data: Dict, chart_dir: str) -> Optional[str]:
    """Daily voltage trend with nominal band shaded."""
    trend = voltage_data.get('daily_trend', [])
    if not trend:
        return None

    path = os.path.join(chart_dir, 'voltage_trend.png')
    dates = _parse_dates(trend)
    min_v = [t['min_v'] for t in trend]
    max_v = [t['max_v'] for t in trend]
    avg_v = [t['avg_v'] for t in trend]

    nominal = voltage_data.get('nominal_voltage', 120)
    low = voltage_data.get('low_limit', nominal * 0.95)
    high = voltage_data.get('high_limit', nominal * 1.05)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(dates, low, high, alpha=0.15, color='green', label=f'Nominal +/-5% ({low:.0f}-{high:.0f}V)')
    ax.plot(dates, avg_v, color='#2563eb', linewidth=2, label='Avg Voltage')
    ax.fill_between(dates, min_v, max_v, alpha=0.2, color='#2563eb', label='Min-Max Range')
    ax.axhline(nominal, color='gray', linestyle='--', alpha=0.5, label=f'Nominal ({nominal}V)')

    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Voltage (V)', fontsize=11, fontweight='bold')
    ax.set_title('Daily Voltage Stability', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight')
    plt.close()
    return path


def generate_current_chart(current_data: Dict, chart_dir: str) -> Optional[str]:
    """Daily peak current bar chart."""
    trend = current_data.get('daily_peak_trend', [])
    if not trend:
        return None

    path = os.path.join(chart_dir, 'current_peaks.png')
    dates = _parse_dates(trend)
    peaks = [t['peak_a'] for t in trend]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(dates, peaks, color='#f59e0b', alpha=0.8, width=0.8)
    avg_peak = np.mean(peaks)
    ax.axhline(avg_peak, color='#ef4444', linestyle='--', linewidth=1.5, label=f'Avg Peak ({avg_peak:.1f}A)')

    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Peak Current (A)', fontsize=11, fontweight='bold')
    ax.set_title('Daily Peak Current', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight')
    plt.close()
    return path


def generate_frequency_chart(freq_data: Dict, chart_dir: str) -> Optional[str]:
    """Daily frequency trend with acceptable band."""
    if not freq_data.get('data_available'):
        return None

    trend = freq_data.get('daily_trend', [])
    if not trend:
        return None

    path = os.path.join(chart_dir, 'frequency_trend.png')
    dates = _parse_dates(trend)
    min_hz = [t['min_hz'] for t in trend]
    max_hz = [t['max_hz'] for t in trend]
    avg_hz = [t['avg_hz'] for t in trend]

    band_low = freq_data.get('band_low', 59.95)
    band_high = freq_data.get('band_high', 60.05)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(dates, band_low, band_high, alpha=0.15, color='green', label=f'Acceptable ({band_low}-{band_high} Hz)')
    ax.plot(dates, avg_hz, color='#8b5cf6', linewidth=2, label='Avg Frequency')
    ax.fill_between(dates, min_hz, max_hz, alpha=0.2, color='#8b5cf6', label='Min-Max Range')

    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Frequency (Hz)', fontsize=11, fontweight='bold')
    ax.set_title('Daily Frequency Stability', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight')
    plt.close()
    return path


def generate_neutral_chart(neutral_data: Dict, chart_dir: str) -> Optional[str]:
    """Daily neutral current trend."""
    if not neutral_data.get('data_available'):
        return None

    trend = neutral_data.get('daily_trend', [])
    if not trend:
        return None

    path = os.path.join(chart_dir, 'neutral_current_trend.png')
    dates = _parse_dates(trend)
    avg_a = [t['avg_a'] for t in trend]
    max_a = [t['max_a'] for t in trend]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, avg_a, color='#2563eb', linewidth=2, label='Avg Neutral Current')
    ax.plot(dates, max_a, color='#ef4444', linewidth=1.5, linestyle='--', label='Max Neutral Current')

    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('Current (A)', fontsize=11, fontweight='bold')
    ax.set_title('Daily Neutral Current', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight')
    plt.close()
    return path


def generate_thd_chart(thd_data: Dict, chart_dir: str) -> Optional[str]:
    """Daily current THD trend with IEEE 519 reference."""
    if not thd_data.get('data_available'):
        return None

    trend = thd_data.get('daily_trend', [])
    if not trend:
        return None

    path = os.path.join(chart_dir, 'thd_current_trend.png')
    dates = _parse_dates(trend)
    avg_thd = [t['avg_thd'] for t in trend]
    max_thd = [t['max_thd'] for t in trend]
    limit = thd_data.get('thd_limit_pct', 5.0)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, avg_thd, color='#2563eb', linewidth=2, label='Avg Current THD')
    ax.plot(dates, max_thd, color='#ef4444', linewidth=1.5, linestyle='--', label='Max Current THD')
    ax.axhline(limit, color='#f59e0b', linestyle=':', linewidth=2, label=f'IEEE 519 Limit ({limit}%)')

    ax.set_xlabel('Date', fontsize=11, fontweight='bold')
    ax.set_ylabel('THD (%)', fontsize=11, fontweight='bold')
    ax.set_title('Daily Current Total Harmonic Distortion', fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight')
    plt.close()
    return path


# ═══════════════════════════════════════════════════════════════════════
# PDF Class
# ═══════════════════════════════════════════════════════════════════════

class ElectricalHealthPDF(FPDF):
    """Argo-branded PDF for Electrical Health Screening reports."""

    def header(self):
        if self.page_no() == 1:
            return  # Cover page has its own layout
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*ARGO_BLUE)
        self.cell(0, 8, 'Electrical Health Screening', 0, 0, 'L')
        self.set_font('Arial', '', 8)
        self.set_text_color(*ARGO_GRAY)
        self.cell(0, 8, 'Argo Energy Solutions', 0, 1, 'R')
        self.set_draw_color(*ARGO_BLUE)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*ARGO_GRAY)
        self.cell(0, 10, 'CONFIDENTIAL', 0, 0, 'L')
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')

    # ── Cover Page ──────────────────────────────────────────────────

    def add_cover_page(self, site_name: str, start_date: str, end_date: str):
        self.add_page()
        # Blue header bar
        self.set_fill_color(*ARGO_BLUE)
        self.rect(0, 0, 210, 80, 'F')

        # Title text
        self.set_y(20)
        self.set_font('Arial', 'B', 28)
        self.set_text_color(*WHITE)
        self.cell(0, 14, 'Electrical Health', 0, 1, 'C')
        self.cell(0, 14, 'Screening', 0, 1, 'C')
        self.set_font('Arial', '', 14)
        self.cell(0, 10, 'Monthly Power Quality Assessment', 0, 1, 'C')

        # Argo branding
        self.set_y(95)
        self.set_text_color(*ARGO_DARK)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Argo Energy Solutions', 0, 1, 'C')
        self.ln(15)

        # Site and date info
        self.set_font('Arial', '', 13)
        self.set_text_color(*ARGO_DARK)
        self.cell(0, 10, f'Site: {site_name}', 0, 1, 'C')
        self.cell(0, 10, f'Report Period: {start_date} to {end_date}', 0, 1, 'C')
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')

        # Footer bar
        self.set_fill_color(*ARGO_BLUE)
        self.rect(0, 270, 210, 27, 'F')
        self.set_y(275)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(*WHITE)
        self.cell(0, 8, 'Facilities | Electrical | Monthly Report', 0, 1, 'C')

    # ── Section Helpers ─────────────────────────────────────────────

    def _section_header(self, title: str):
        self.set_fill_color(*ARGO_BLUE)
        self.set_text_color(*WHITE)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f'  {title}', 0, 1, 'L', fill=True)
        self.set_text_color(*ARGO_DARK)
        self.ln(4)

    def _metric_table(self, headers: List[str], rows: List[List[str]], col_widths: List[int]):
        # Header row
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(243, 244, 246)
        self.set_text_color(*ARGO_DARK)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, 1, 0, 'C', fill=True)
        self.ln()

        # Data rows
        self.set_font('Arial', '', 9)
        for row in rows:
            for i, val in enumerate(row):
                self.cell(col_widths[i], 6, str(val), 1, 0, 'C')
            self.ln()
        self.ln(3)

    def _score_badge(self, score: str, numeric: int):
        """Draw a colored health score badge."""
        colors = {'Good': ARGO_GREEN, 'Fair': ARGO_AMBER, 'Poor': ARGO_RED}
        color = colors.get(score, ARGO_GRAY)
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(*color)
        self.rect(x, y, 50, 20, 'F')
        self.set_xy(x, y + 2)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*WHITE)
        self.cell(50, 8, score, 0, 2, 'C')
        self.set_font('Arial', '', 10)
        self.cell(50, 6, f'Score: {numeric}/100', 0, 0, 'C')
        self.set_text_color(*ARGO_DARK)
        self.set_xy(x + 55, y)

    def _no_data_placeholder(self, message: str):
        self.set_font('Arial', 'I', 10)
        self.set_text_color(*ARGO_GRAY)
        self.ln(5)
        self.multi_cell(0, 7, message)
        self.set_text_color(*ARGO_DARK)
        self.ln(3)

    # ── Report Sections ─────────────────────────────────────────────

    def add_executive_summary(self, data: Dict):
        self.add_page()
        self._section_header('Executive Summary')

        health = data.get('health_score', {})
        self._score_badge(health.get('score', 'N/A'), health.get('score_numeric', 0))

        # Component scores
        components = health.get('component_scores', {})
        if components:
            self.set_font('Arial', '', 10)
            self.ln(2)
            parts = []
            for comp, score in components.items():
                parts.append(f'{comp.capitalize()}: {score}/100')
            self.cell(0, 7, '   '.join(parts), 0, 1)

        # Key findings
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 7, 'Key Findings', 0, 1)
        self.set_font('Arial', '', 10)
        findings = health.get('findings', [])
        for f in findings:
            self.cell(5)
            self.cell(0, 6, f'- {f}', 0, 1)

        # Summary metrics table
        self.ln(5)
        voltage = data.get('voltage_stability', {})
        current = data.get('current_peaks', {})
        freq = data.get('frequency_excursions', {})
        thd = data.get('thd_analysis', {})

        headers = ['Metric', 'Value', 'Status']
        rows = []

        if voltage.get('meters'):
            avg_outside = np.mean([m['pct_outside_band'] for m in voltage['meters']])
            status = 'Good' if avg_outside < 2 else ('Fair' if avg_outside < 10 else 'Poor')
            rows.append(['Voltage Stability', f'{avg_outside:.1f}% outside band', status])

        if current.get('meters'):
            max_peak = max(m['peak_current_a'] for m in current['meters'])
            rows.append(['Peak Current', f'{max_peak:.1f} A', 'Recorded'])

        if freq.get('data_available'):
            rows.append(['Frequency Excursions', str(freq.get('excursion_count', 0)),
                        'Good' if freq.get('excursion_count', 0) < 5 else 'Review'])
        else:
            rows.append(['Frequency', 'Awaiting data', '--'])

        if thd.get('data_available') and thd.get('meters'):
            avg_thd = np.mean([m['avg_thd'] for m in thd['meters']])
            rows.append(['Current THD', f'{avg_thd:.1f}%', 'Good' if avg_thd < 5 else 'Review'])
        else:
            rows.append(['Current THD', 'Awaiting data', '--'])

        self._metric_table(headers, rows, [65, 65, 60])

    def add_voltage_section(self, voltage: Dict, chart_path: Optional[str]):
        self.add_page()
        self._section_header('Voltage Stability')

        nominal = voltage.get('nominal_voltage', 120)
        self.set_font('Arial', '', 10)
        self.cell(0, 7, f'Nominal Voltage: {nominal}V    Tolerance: +/-{voltage.get("high_limit", nominal*1.05) - nominal:.0f}V ({voltage.get("low_limit", nominal*0.95):.0f}V - {voltage.get("high_limit", nominal*1.05):.0f}V)', 0, 1)
        self.ln(3)

        meters = voltage.get('meters', [])
        if meters:
            headers = ['Meter', 'Min V', 'Max V', 'Avg V', '% Outside', 'Sags', 'Swells']
            rows = []
            for m in meters:
                name = m['meter_name'][:25] if len(m['meter_name']) > 25 else m['meter_name']
                rows.append([
                    name, str(m['min_voltage']), str(m['max_voltage']),
                    str(m['avg_voltage']), f"{m['pct_outside_band']}%",
                    str(m['sag_count']), str(m['swell_count']),
                ])
            self._metric_table(headers, rows, [42, 20, 20, 20, 25, 20, 20])

        if chart_path and os.path.exists(chart_path):
            self.image(chart_path, x=10, w=190)

    def add_current_section(self, current: Dict, chart_path: Optional[str]):
        self.add_page()
        self._section_header('Max Current Events')

        meters = current.get('meters', [])
        if meters:
            headers = ['Meter', 'Peak (A)', 'Avg (A)', 'Peak Time']
            rows = []
            for m in meters:
                name = m['meter_name'][:30] if len(m['meter_name']) > 30 else m['meter_name']
                ts = m['peak_timestamp'][:16] if len(m['peak_timestamp']) > 16 else m['peak_timestamp']
                rows.append([name, str(m['peak_current_a']), str(m['avg_current_a']), ts])
            self._metric_table(headers, rows, [50, 25, 25, 55])

        # Top events
        top = current.get('top_events', [])
        if top:
            self.set_font('Arial', 'B', 11)
            self.cell(0, 7, f'Top {len(top)} Peak Events', 0, 1)
            self.set_font('Arial', '', 9)
            for evt in top[:10]:
                name = evt['meter_name'][:25]
                self.cell(0, 5, f"  {evt['current_a']}A at {evt['timestamp'][:16]} ({name})", 0, 1)
            self.ln(3)

        if chart_path and os.path.exists(chart_path):
            self.image(chart_path, x=10, w=190)

    def add_frequency_section(self, freq: Dict, chart_path: Optional[str]):
        self.add_page()
        self._section_header('Frequency Excursions')

        if not freq.get('data_available'):
            self._no_data_placeholder(
                freq.get('message', 'Frequency data not yet available. '
                          'Will populate after next ingestion cycle with expanded field capture.')
            )
            return

        self.set_font('Arial', '', 10)
        self.cell(0, 7, f"Average: {freq['avg_frequency']} Hz    "
                       f"Min: {freq['min_frequency']} Hz    "
                       f"Max: {freq['max_frequency']} Hz", 0, 1)
        self.cell(0, 7, f"Excursions outside {freq['band_low']}-{freq['band_high']} Hz: "
                       f"{freq['excursion_count']} ({freq['excursion_pct']}%)", 0, 1)
        self.ln(5)

        if chart_path and os.path.exists(chart_path):
            self.image(chart_path, x=10, w=190)

    def add_neutral_section(self, neutral: Dict, chart_path: Optional[str]):
        self.add_page()
        self._section_header('Neutral Current Indicators')

        if not neutral.get('data_available'):
            self._no_data_placeholder(
                neutral.get('message', 'Neutral current data not yet available. Will populate '
                             'after next ingestion cycle with expanded field capture.')
            )
            self.ln(5)
            self.set_font('Arial', 'B', 10)
            self.cell(0, 7, 'Why Monitor Neutral Current?', 0, 1)
            self.set_font('Arial', '', 10)
            self.multi_cell(0, 6,
                'Elevated neutral current in three-phase systems can indicate load imbalance '
                'between phases, harmonic distortion from non-linear loads, or wiring issues. '
                'Excessive neutral current increases energy losses, can overheat conductors, '
                'and may indicate power quality problems that affect equipment reliability.')
            return

        meters = neutral.get('meters', [])
        if meters:
            headers = ['Meter', 'Avg (A)', 'Max (A)', 'Elevated Events']
            rows = []
            for m in meters:
                name = m['meter_name'][:35] if len(m['meter_name']) > 35 else m['meter_name']
                rows.append([name, str(m['avg_neutral_a']), str(m['max_neutral_a']),
                            str(m['elevated_count'])])
            self._metric_table(headers, rows, [55, 30, 30, 40])

        if chart_path and os.path.exists(chart_path):
            self.image(chart_path, x=10, w=190)

    def add_thd_section(self, thd: Dict, chart_path: Optional[str]):
        self.add_page()
        self._section_header('Current THD Analysis')

        self.set_font('Arial', 'I', 9)
        self.set_text_color(*ARGO_GRAY)
        self.cell(0, 6, 'Note: Only current THD is available from Eniscope hardware. '
                       'Voltage THD is not provided.', 0, 1)
        self.set_text_color(*ARGO_DARK)
        self.ln(2)

        if not thd.get('data_available'):
            self._no_data_placeholder(
                thd.get('message', 'Current THD data not yet available. '
                         'Will populate after next ingestion cycle with expanded field capture.')
            )
            return

        meters = thd.get('meters', [])
        if meters:
            limit = thd.get('thd_limit_pct', 5.0)
            self.set_font('Arial', '', 10)
            self.cell(0, 7, f'IEEE 519 Reference Limit: {limit}%', 0, 1)
            self.ln(2)

            headers = ['Meter', 'Avg THD %', 'Max THD %', 'Above Limit']
            rows = []
            for m in meters:
                name = m['meter_name'][:35] if len(m['meter_name']) > 35 else m['meter_name']
                rows.append([name, str(m['avg_thd']), str(m['max_thd']),
                            str(m['above_limit_count'])])
            self._metric_table(headers, rows, [55, 30, 30, 35])

        if chart_path and os.path.exists(chart_path):
            self.image(chart_path, x=10, w=190)


# ═══════════════════════════════════════════════════════════════════════
# Report Generator (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════

class ElectricalHealthReportGenerator:
    """Orchestrates data fetching, chart generation, and PDF assembly.

    This is Stage 4 (Deliver) — it calls Stage 3 (Analyze) functions
    and formats the output into a professional PDF.
    """

    def __init__(self, conn, site_id: str, start_date: str, end_date: str,
                 nominal_voltage: Optional[int] = None,
                 output_dir: str = 'reports'):
        self.conn = conn
        self.site_id = site_id
        self.start_date = start_date
        self.end_date = end_date
        self.nominal_voltage = nominal_voltage
        self.output_dir = output_dir

    def _get_site_name(self) -> str:
        """Fetch site name from v_sites (Layer 3)."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT site_name FROM v_sites WHERE site_id = %s",
                        (str(self.site_id),))
            row = cur.fetchone()
            return row[0] if row else f'Site {self.site_id}'

    def generate(self) -> str:
        """Main generation pipeline. Returns output PDF path."""
        # Import here to avoid circular imports
        import sys
        from pathlib import Path
        pkg_root = Path(__file__).resolve().parent.parent.parent
        if str(pkg_root / 'python_scripts') not in sys.path:
            sys.path.insert(0, str(pkg_root / 'python_scripts'))

        from analyze.electrical_health import generate_electrical_health_data

        with tempfile.TemporaryDirectory() as chart_dir:
            # 1. Fetch analytics data (Stage 3)
            data = generate_electrical_health_data(
                self.conn, self.site_id, self.start_date, self.end_date,
                self.nominal_voltage,
            )

            # 2. Fetch site name
            site_name = self._get_site_name()

            # 3. Generate charts into per-run isolated directory
            voltage_chart = generate_voltage_chart(data['voltage_stability'], chart_dir)
            current_chart = generate_current_chart(data['current_peaks'], chart_dir)
            frequency_chart = generate_frequency_chart(data['frequency_excursions'], chart_dir)
            neutral_chart = generate_neutral_chart(data['neutral_current'], chart_dir)
            thd_chart = generate_thd_chart(data['thd_analysis'], chart_dir)

            # 4. Assemble PDF
            pdf = ElectricalHealthPDF()
            pdf.set_auto_page_break(auto=True, margin=20)

            pdf.add_cover_page(site_name, self.start_date, self.end_date)
            pdf.add_executive_summary(data)
            pdf.add_voltage_section(data['voltage_stability'], voltage_chart)
            pdf.add_current_section(data['current_peaks'], current_chart)
            pdf.add_frequency_section(data['frequency_excursions'], frequency_chart)
            pdf.add_neutral_section(data['neutral_current'], neutral_chart)
            pdf.add_thd_section(data['thd_analysis'], thd_chart)

            # 5. Save (output_dir is persistent; charts live only in chart_dir)
            filename = f"electrical-health-{self.site_id}-{self.start_date}-to-{self.end_date}.pdf"
            output_path = os.path.join(self.output_dir, filename)
            os.makedirs(self.output_dir, exist_ok=True)
            pdf.output(output_path)

        print(f"Report generated: {output_path}")
        return output_path
