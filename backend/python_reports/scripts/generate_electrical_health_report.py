"""
Electrical Health Screening Report - PDF Generator

Executive-focused PDF: traffic-light health indicators, plain-language
summaries, specific actionable recommendations, charts for visual context.
Detailed per-meter tables moved to appendix.

Following Argo governance: Stage 4 (Deliver - Presentation)
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

plt.style.use('seaborn-v0_8-darkgrid')

# Argo brand palette (logo-matched)
ARGO_NAVY = (26, 37, 52)       # Dark navy from "ARGO" logo text
ARGO_BLUE = (37, 99, 235)      # Kept for chart line colors only
ARGO_DARK = (31, 41, 55)       # Body text / dark neutral
ARGO_GREEN = (57, 208, 43)     # Bright lime green from "ENERGY SOLUTIONS" logo text
ARGO_RED = (239, 68, 68)
ARGO_AMBER = (245, 158, 11)
ARGO_GRAY = (107, 114, 128)
ARGO_LIGHT_GRAY = (243, 244, 246)
WHITE = (255, 255, 255)

# Traffic-light colors
TL_GREEN = (34, 197, 94)
TL_YELLOW = (234, 179, 8)
TL_RED = (220, 38, 38)


# ═══════════════════════════════════════════════════════════════════════
# Recommendation Engine
# ═══════════════════════════════════════════════════════════════════════

def _generate_recommendations(data: Dict) -> List[Dict[str, str]]:
    """Produce specific, actionable recommendations from analysis data.

    Each recommendation has:
      priority: 'High' | 'Medium' | 'Low'
      category: section name
      finding: what was observed
      action: what to do about it
    """
    recs: List[Dict[str, str]] = []
    voltage = data.get('voltage_stability', {})
    current = data.get('current_peaks', {})
    freq = data.get('frequency_excursions', {})
    neutral = data.get('neutral_current', {})
    thd = data.get('thd_analysis', {})

    # ── Voltage ──
    for m in voltage.get('meters', []):
        if m['pct_outside_band'] >= 10:
            recs.append({
                'priority': 'High',
                'category': 'Voltage',
                'finding': f"{m['meter_name']} voltage outside tolerance {m['pct_outside_band']:.1f}% of the time.",
                'action': 'Schedule a power quality audit with your electrician. Check transformer tap settings and upstream utility feed stability.',
            })
        elif m['pct_outside_band'] >= 2:
            recs.append({
                'priority': 'Medium',
                'category': 'Voltage',
                'finding': f"{m['meter_name']} showed minor voltage deviations ({m['pct_outside_band']:.1f}% outside band).",
                'action': 'Monitor over the next billing cycle. If trend continues, request utility voltage review.',
            })
        if m['sag_count'] > 20:
            recs.append({
                'priority': 'Medium',
                'category': 'Voltage',
                'finding': f"{m['meter_name']} recorded {m['sag_count']} voltage sag events.",
                'action': 'Investigate whether large motor starts (HVAC compressors, elevators) are causing dips. Consider soft-start installations.',
            })

    # ── Current ──
    for m in current.get('meters', []):
        if m['avg_current_a'] > 0:
            ratio = m['peak_current_a'] / m['avg_current_a']
            if ratio >= 5:
                recs.append({
                    'priority': 'High',
                    'category': 'Current',
                    'finding': f"{m['meter_name']} peak demand is {ratio:.1f}x its average - large demand spikes detected.",
                    'action': f"Review scheduling of high-draw equipment on this circuit. Peak event at {m['peak_timestamp'][:16]}. "
                              'Staggering startups can reduce demand charges.',
                })
            elif ratio >= 3:
                recs.append({
                    'priority': 'Medium',
                    'category': 'Current',
                    'finding': f"{m['meter_name']} peak-to-average ratio is {ratio:.1f}x.",
                    'action': 'Consider load scheduling adjustments to flatten demand peaks and reduce demand charges.',
                })

    # ── Frequency ──
    if freq.get('data_available'):
        freq_band_low = freq.get('band_low', 59.95)
        freq_band_high = freq.get('band_high', 60.05)
        freq_high_exc_th = freq.get('high_excursion_threshold', 20)
        freq_low_exc_th = freq.get('low_excursion_threshold', 5)
        exc = freq.get('excursion_count', 0)
        if exc >= freq_high_exc_th:
            recs.append({
                'priority': 'High',
                'category': 'Frequency',
                'finding': f"{exc} frequency excursions outside the {freq_band_low:.2f}-{freq_band_high:.2f} Hz band detected.",
                'action': 'Contact your utility provider - excessive frequency variation may indicate grid instability in your service area.',
            })
        elif exc >= freq_low_exc_th:
            recs.append({
                'priority': 'Low',
                'category': 'Frequency',
                'finding': f"{exc} minor frequency excursions detected.",
                'action': 'No immediate action needed. Continue monitoring; this is informational.',
            })

    # ── Neutral Current ──
    if neutral.get('data_available'):
        for m in neutral.get('meters', []):
            if m['elevated_count'] > 10:
                recs.append({
                    'priority': 'Medium',
                    'category': 'Neutral Current',
                    'finding': f"{m['meter_name']} showed {m['elevated_count']} elevated neutral current events.",
                    'action': 'Elevated neutral current suggests phase imbalance or harmonic distortion. '
                              'Have an electrician check load distribution across phases.',
                })

    # ── THD ──
    if thd.get('data_available'):
        thd_limit = thd.get('limit', 5.0)
        thd_warn_th = thd.get('warning_threshold', thd_limit + 3.0)
        for m in thd.get('meters', []):
            if m['avg_thd'] >= thd_warn_th:
                recs.append({
                    'priority': 'High',
                    'category': 'Harmonics',
                    'finding': f"{m['meter_name']} average current THD is {m['avg_thd']:.1f}% (above the configured limit of {thd_limit:.1f}%).",
                    'action': 'Schedule a harmonic assessment with a power quality specialist. '
                              'Consider harmonic filters or isolation transformers for non-linear loads.',
                })
            elif m['avg_thd'] >= thd_limit:
                recs.append({
                    'priority': 'Medium',
                    'category': 'Harmonics',
                    'finding': f"{m['meter_name']} current THD is {m['avg_thd']:.1f}%, near the configured limit of {thd_limit:.1f}%.",
                    'action': 'Monitor trend. If THD rises further, plan harmonic mitigation to prevent equipment overheating.',
                })

    # Sort by priority
    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    recs.sort(key=lambda r: priority_order.get(r['priority'], 3))

    if not recs:
        recs.append({
            'priority': 'Low',
            'category': 'Overall',
            'finding': 'No significant electrical health concerns detected during this reporting period.',
            'action': 'Continue routine monitoring. Next report will track trends over time.',
        })

    return recs


# ═══════════════════════════════════════════════════════════════════════
# Chart Generation
# ═══════════════════════════════════════════════════════════════════════

def _parse_dates(trend: List[Dict], key: str = 'date'):
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
    trend = voltage_data.get('daily_trend', [])
    if not trend:
        return None
    path = os.path.join(chart_dir, 'voltage_trend.png')
    dates = _parse_dates(trend)
    nominal = voltage_data.get('nominal_voltage', 120)
    low = voltage_data.get('low_limit', nominal * 0.95)
    high = voltage_data.get('high_limit', nominal * 1.05)

    _, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(dates, low, high, alpha=0.15, color='green', label=f'Acceptable ({low:.0f}-{high:.0f}V)')
    ax.plot(dates, [t['avg_v'] for t in trend], color='#2563eb', linewidth=2, label='Daily Avg')
    ax.fill_between(dates, [t['min_v'] for t in trend], [t['max_v'] for t in trend],
                    alpha=0.15, color='#2563eb', label='Daily Min-Max')
    ax.axhline(nominal, color='gray', linestyle='--', alpha=0.4)
    ax.set_ylabel('Voltage (V)', fontsize=10)
    ax.legend(loc='best', fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight')
    plt.close()
    return path


def generate_current_chart(current_data: Dict, chart_dir: str) -> Optional[str]:
    trend = current_data.get('daily_peak_trend', [])
    if not trend:
        return None
    path = os.path.join(chart_dir, 'current_peaks.png')
    dates = _parse_dates(trend)
    peaks = [t['peak_a'] for t in trend]

    _, ax = plt.subplots(figsize=(10, 4))
    ax.bar(dates, peaks, color='#f59e0b', alpha=0.8, width=0.8)
    avg_peak = np.mean(peaks)
    ax.axhline(avg_peak, color='#ef4444', linestyle='--', linewidth=1.5, label=f'Period Avg ({avg_peak:.0f}A)')
    ax.set_ylabel('Peak Current (A)', fontsize=10)
    ax.legend(loc='best', fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight')
    plt.close()
    return path


def generate_frequency_chart(freq_data: Dict, chart_dir: str) -> Optional[str]:
    if not freq_data.get('data_available'):
        return None
    trend = freq_data.get('daily_trend', [])
    if not trend:
        return None
    path = os.path.join(chart_dir, 'frequency_trend.png')
    dates = _parse_dates(trend)
    band_low = freq_data.get('band_low', 59.95)
    band_high = freq_data.get('band_high', 60.05)

    _, ax = plt.subplots(figsize=(10, 4))
    ax.fill_between(dates, band_low, band_high, alpha=0.15, color='green', label=f'Normal ({band_low}-{band_high} Hz)')
    ax.plot(dates, [t['avg_hz'] for t in trend], color='#8b5cf6', linewidth=2, label='Daily Avg')
    ax.fill_between(dates, [t['min_hz'] for t in trend], [t['max_hz'] for t in trend],
                    alpha=0.15, color='#8b5cf6')
    ax.set_ylabel('Frequency (Hz)', fontsize=10)
    ax.legend(loc='best', fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight')
    plt.close()
    return path


def generate_thd_chart(thd_data: Dict, chart_dir: str) -> Optional[str]:
    if not thd_data.get('data_available'):
        return None
    trend = thd_data.get('daily_trend', [])
    if not trend:
        return None
    path = os.path.join(chart_dir, 'thd_current_trend.png')
    dates = _parse_dates(trend)
    limit = thd_data.get('thd_limit_pct', 5.0)

    _, ax = plt.subplots(figsize=(10, 4))
    ax.plot(dates, [t['avg_thd'] for t in trend], color='#2563eb', linewidth=2, label='Daily Avg THD')
    ax.plot(dates, [t['max_thd'] for t in trend], color='#ef4444', linewidth=1, linestyle='--',
            alpha=0.6, label='Daily Max THD')
    ax.axhline(limit, color='#f59e0b', linestyle=':', linewidth=2, label=f'IEEE 519 Limit ({limit}%)')
    ax.set_ylabel('THD (%)', fontsize=10)
    ax.legend(loc='best', fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight')
    plt.close()
    return path


# ═══════════════════════════════════════════════════════════════════════
# PDF Class
# ═══════════════════════════════════════════════════════════════════════

class ElectricalHealthPDF(FPDF):
    """Executive-focused Argo-branded PDF."""

    def header(self):
        if self.page_no() == 1:
            return
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.jpg')
        has_logo = os.path.exists(logo_path)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*ARGO_NAVY)
        # Leave right margin for logo if present, otherwise show text
        title_w = 170 if has_logo else 0
        self.cell(title_w, 8, 'Electrical Health Screening', 0, 0, 'L')
        if not has_logo:
            self.set_font('Arial', '', 8)
            self.set_text_color(*ARGO_GRAY)
            self.cell(0, 8, 'Argo Energy Solutions', 0, 1, 'R')
        else:
            self.ln()
            self.image(logo_path, x=182, y=3, w=18)
        self.set_draw_color(*ARGO_NAVY)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*ARGO_GRAY)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*ARGO_GRAY)
        self.cell(0, 10, 'CONFIDENTIAL - Argo Energy Solutions', 0, 0, 'L')
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'R')

    # ── Helpers ───────────────────────────────────────────────────────

    def _traffic_light(self, status: str, x: float, y: float, w: float = 40, h: float = 18):
        """Draw a traffic-light badge at (x, y)."""
        colors = {'Green': TL_GREEN, 'Yellow': TL_YELLOW, 'Red': TL_RED}
        labels = {'Green': 'GOOD', 'Yellow': 'ATTENTION', 'Red': 'ACTION NEEDED'}
        color = colors.get(status, ARGO_GRAY)
        label = labels.get(status, status)

        self.set_fill_color(*color)
        self.rect(x, y, w, h, 'F')
        self.set_xy(x, y + 3)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*WHITE)
        self.cell(w, h - 6, label, 0, 0, 'C')
        self.set_text_color(*ARGO_DARK)

    def _section_header(self, title: str, status: Optional[str] = None):
        self.set_fill_color(*ARGO_NAVY)
        self.set_text_color(*WHITE)
        self.set_font('Arial', 'B', 14)
        if status:
            # Draw title in left portion, fill right portion, then overlay badge
            self.cell(140, 10, f'  {title}', 0, 0, 'L', fill=True)
            badge_x = self.get_x()
            badge_y = self.get_y()
            self.cell(50, 10, '', 0, 1, 'L', fill=True)  # Fill rest of bar
            self._traffic_light(status, badge_x + 1, badge_y, w=48, h=10)
        else:
            self.cell(0, 10, f'  {title}', 0, 1, 'L', fill=True)
        self.set_text_color(*ARGO_DARK)
        self.ln(4)

    def _write_paragraph(self, text: str, size: int = 10, bold: bool = False):
        style = 'B' if bold else ''
        self.set_font('Arial', style, size)
        self.set_text_color(*ARGO_DARK)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def _metric_row(self, label: str, value: str, indent: float = 15):
        self.set_x(indent)
        self.set_font('Arial', '', 10)
        self.set_text_color(*ARGO_GRAY)
        self.cell(60, 6, label, 0, 0)
        self.set_text_color(*ARGO_DARK)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 6, value, 0, 1)

    def _metric_table(self, headers: List[str], rows: List[List[str]], col_widths: List[int]):
        # Header row: navy fill, white text, 9pt bold
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(*ARGO_NAVY)
        self.set_text_color(*WHITE)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, 1, 0, 'C', fill=True)
        self.ln()
        # Data rows: alternating fill, column 0 left-aligned
        self.set_font('Arial', '', 9)
        self.set_text_color(*ARGO_DARK)
        STRIPE = (230, 234, 242)  # Subtle blue-gray for odd rows
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(*WHITE)
            else:
                self.set_fill_color(*STRIPE)
            for i, val in enumerate(row):
                align = 'L' if i == 0 else 'C'
                self.cell(col_widths[i], 7, str(val), 1, 0, align, fill=True)
            self.ln()
        self.ln(3)

    def _no_data_placeholder(self, message: str):
        self.set_font('Arial', 'I', 10)
        self.set_text_color(*ARGO_GRAY)
        self.ln(3)
        self.multi_cell(0, 7, message)
        self.set_text_color(*ARGO_DARK)
        self.ln(2)

    def _divider(self, top_margin: float = 3, bottom_margin: float = 3):
        """Draw a subtle light-gray horizontal rule between subsections."""
        self.ln(top_margin)
        self.set_draw_color(*ARGO_LIGHT_GRAY)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(bottom_margin)

    def _metric_callout_row(self, label: str, value: str, indent: float = 15):
        """Draw a highlighted label+value row with a light-gray background box."""
        row_h = 7
        box_w = 180
        self.set_fill_color(*ARGO_LIGHT_GRAY)
        self.set_draw_color(*ARGO_LIGHT_GRAY)
        self.rect(indent, self.get_y(), box_w, row_h, 'F')
        self.set_x(indent + 3)
        self.set_font('Arial', '', 10)
        self.set_text_color(*ARGO_GRAY)
        self.cell(62, row_h, label, 0, 0)
        self.set_text_color(*ARGO_DARK)
        self.set_font('Arial', 'B', 10)
        self.cell(0, row_h, value, 0, 1)
        self.ln(1)

    def _chart_caption(self, text: str):
        """Write a small italic caption below a chart image."""
        if not hasattr(self, '_figure_counter'):
            self._figure_counter = 0
        self._figure_counter += 1
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*ARGO_GRAY)
        self.cell(0, 5, f'Figure {self._figure_counter}: {text}', 0, 1, 'C')
        self.set_text_color(*ARGO_DARK)
        self.ln(2)

    def _trend_sentence(self, trend: list, value_key: str, lower_is_better: bool = True) -> Optional[str]:
        """Return a plain-English trend sentence based on first-half vs second-half averages."""
        if not trend or len(trend) < 4:
            return None
        mid = len(trend) // 2
        first_vals = [t[value_key] for t in trend[:mid] if t.get(value_key) is not None]
        second_vals = [t[value_key] for t in trend[mid:] if t.get(value_key) is not None]
        if not first_vals or not second_vals:
            return None
        first_avg = sum(first_vals) / len(first_vals)
        second_avg = sum(second_vals) / len(second_vals)
        pct_change = abs(second_avg - first_avg) / (first_avg + 1e-9) * 100
        if pct_change < 5:
            return 'Readings are stable across the reporting period.'
        improving = (second_avg < first_avg) if lower_is_better else (second_avg > first_avg)
        if improving:
            return 'Trend is improving over the reporting period - conditions are getting better.'
        else:
            return 'Trend is worsening over the reporting period - this warrants attention.'

    # ── Cover Page ────────────────────────────────────────────────────

    def add_cover_page(self, site_name: str, start_date: str, end_date: str):
        self.add_page()

        # Primary navy header band
        self.set_fill_color(*ARGO_NAVY)
        self.rect(0, 0, 210, 80, 'F')

        # Secondary accent band (slightly lighter) just below header
        self.set_fill_color(44, 52, 68)
        self.rect(0, 80, 210, 8, 'F')

        # Title text in header band
        self.set_y(18)
        self.set_font('Arial', 'B', 28)
        self.set_text_color(*WHITE)
        self.cell(0, 14, 'Electrical Health', 0, 1, 'C')
        self.cell(0, 14, 'Screening', 0, 1, 'C')
        self.set_font('Arial', '', 13)
        self.cell(0, 9, 'Monthly Power Quality Assessment', 0, 1, 'C')

        # Logo centered below header band
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.jpg')
        if os.path.exists(logo_path):
            self.image(logo_path, x=70, y=94, w=70)
            content_y = 175
        else:
            # Fallback: text branding block
            self.set_y(100)
            self.set_text_color(*ARGO_DARK)
            self.set_font('Arial', 'B', 18)
            self.cell(0, 10, 'Argo Energy Solutions', 0, 1, 'C')
            content_y = 125

        # Format dates for display
        try:
            dt_start = datetime.strptime(start_date, '%Y-%m-%d')
            dt_end = datetime.strptime(end_date, '%Y-%m-%d')
            fmt_start = dt_start.strftime('%B %-d, %Y')
            fmt_end = dt_end.strftime('%B %-d, %Y')
            period_str = f'{fmt_start} - {fmt_end}'
        except ValueError:
            period_str = f'{start_date} - {end_date}'

        # Report metadata block
        self.set_y(content_y)
        self.set_text_color(*ARGO_DARK)
        self.set_font('Arial', '', 13)
        self.cell(0, 10, f'Prepared for: {site_name}', 0, 1, 'C')
        self.cell(0, 10, f'Report Period: {period_str}', 0, 1, 'C')
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%B %-d, %Y")}', 0, 1, 'C')

        # Footer band: two lines
        self.set_fill_color(*ARGO_NAVY)
        self.rect(0, 265, 210, 32, 'F')
        self.set_y(270)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*WHITE)
        self.cell(0, 8, 'Argo Energy Solutions', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 7, 'Facilities | Electrical | Monthly Report', 0, 1, 'C')

    # ── Executive Summary ─────────────────────────────────────────────

    def add_executive_summary(self, data: Dict, recommendations: List[Dict]):
        self.add_page()
        health = data.get('health_score', {})
        score = health.get('score', 'N/A')
        numeric = health.get('score_numeric', 0)
        tl = 'Green' if score == 'Good' else ('Yellow' if score == 'Fair' else 'Red')

        self._section_header('Executive Summary')

        # Large centered traffic-light badge
        badge_w = 60
        badge_x = (210 - badge_w) / 2
        self._traffic_light(tl, badge_x, self.get_y(), w=badge_w, h=22)
        self.ln(28)

        # Score callout box: centered bordered rectangle
        score_box_w = 90
        score_box_h = 18
        score_box_x = (210 - score_box_w) / 2
        score_box_y = self.get_y()
        self.set_draw_color(*ARGO_NAVY)
        self.set_fill_color(*ARGO_LIGHT_GRAY)
        self.rect(score_box_x, score_box_y, score_box_w, score_box_h, 'FD')
        self.set_xy(score_box_x, score_box_y + 2)
        self.set_font('Arial', '', 9)
        self.set_text_color(*ARGO_GRAY)
        self.cell(score_box_w, 5, 'Overall Electrical Health Score', 0, 1, 'C')
        self.set_x(score_box_x)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*ARGO_NAVY)
        self.cell(score_box_w, 9, f'{numeric} / 100', 0, 1, 'C')
        self.set_text_color(*ARGO_DARK)
        self.ln(6)

        # Category status rows
        self.set_font('Arial', 'B', 11)
        self.cell(0, 7, 'Category Status', 0, 1)
        self.ln(1)

        voltage = data.get('voltage_stability', {})
        current_data = data.get('current_peaks', {})
        freq = data.get('frequency_excursions', {})
        thd = data.get('thd_analysis', {})

        categories = []
        if voltage.get('meters'):
            avg_outside = np.mean([m['pct_outside_band'] for m in voltage['meters']])
            st = 'Green' if avg_outside < 2 else ('Yellow' if avg_outside < 10 else 'Red')
            sm = 'Stable' if avg_outside < 2 else f'{avg_outside:.1f}% outside tolerance'
            categories.append(('Voltage Stability', st, sm))
        if current_data.get('meters'):
            ratios = [m['peak_current_a'] / m['avg_current_a'] for m in current_data['meters'] if m['avg_current_a'] > 0]
            avg_ratio = np.mean(ratios) if ratios else 1
            st = 'Green' if avg_ratio < 3 else ('Yellow' if avg_ratio < 5 else 'Red')
            sm = 'Normal demand profile' if avg_ratio < 3 else f'Peak/avg ratio {avg_ratio:.1f}x'
            categories.append(('Peak Current', st, sm))
        if freq.get('data_available'):
            exc = freq.get('excursion_count', 0)
            st = 'Green' if exc < 5 else ('Yellow' if exc < 20 else 'Red')
            sm = 'Stable' if exc < 5 else f'{exc} excursions detected'
            categories.append(('Grid Frequency', st, sm))
        else:
            categories.append(('Grid Frequency', 'Green', 'Data collection in progress'))
        if thd.get('data_available') and thd.get('meters'):
            avg_thd = np.mean([m['avg_thd'] for m in thd['meters']])
            st = 'Green' if avg_thd < 5 else ('Yellow' if avg_thd < 8 else 'Red')
            sm = f'{avg_thd:.0f}% avg - within limits' if avg_thd < 5 else f'{avg_thd:.0f}% avg - elevated'
            categories.append(('Harmonic Distortion', st, sm))
        else:
            categories.append(('Harmonic Distortion', 'Green', 'Data collection in progress'))

        for cat_name, cat_status, cat_summary in categories:
            y = self.get_y()
            colors = {'Green': TL_GREEN, 'Yellow': TL_YELLOW, 'Red': TL_RED}
            color = colors.get(cat_status, ARGO_GRAY)
            self.set_fill_color(*color)
            # 8x6mm solid square badge (replaces tiny 4mm circle)
            self.rect(15, y + 0.5, 8, 6, 'F')
            self.set_x(26)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*ARGO_DARK)
            self.cell(50, 7, cat_name, 0, 0)
            self.set_font('Arial', '', 10)
            self.cell(0, 7, cat_summary, 0, 1)
            self.ln(1)

        # Top recommendations preview
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 7, 'Priority Actions', 0, 1)
        self.ln(1)

        top_recs = [r for r in recommendations if r['priority'] in ('High', 'Medium')][:3]
        if not top_recs:
            top_recs = recommendations[:1]

        for rec in top_recs:
            priority_colors = {'High': TL_RED, 'Medium': TL_YELLOW, 'Low': TL_GREEN}
            pc = priority_colors.get(rec['priority'], ARGO_GRAY)
            y = self.get_y()
            self.set_fill_color(*pc)
            self.set_text_color(*WHITE)
            self.set_font('Arial', 'B', 8)
            self.rect(15, y, 18, 5, 'F')
            self.set_xy(15, y)
            self.cell(18, 5, rec['priority'].upper(), 0, 0, 'C')
            self.set_text_color(*ARGO_DARK)
            self.set_xy(36, y)
            self.set_font('Arial', 'B', 9)
            self.cell(0, 5, rec['finding'][:90], 0, 1)
            self.set_x(36)
            self.set_font('Arial', '', 9)
            self.set_text_color(*ARGO_GRAY)
            self.multi_cell(160, 5, rec['action'])
            self.set_text_color(*ARGO_DARK)
            self.ln(2)

        if len(recommendations) > 3:
            self.set_font('Arial', 'I', 9)
            self.set_text_color(*ARGO_GRAY)
            self.cell(0, 5, f'+ {len(recommendations) - 3} more - see Recommended Actions page', 0, 1)
            self.set_text_color(*ARGO_DARK)

    # ── Section Pages (summary + chart, no inline tables) ────────────

    def add_voltage_section(self, voltage: Dict, chart_path: Optional[str]):
        self.add_page()
        meters = voltage.get('meters', [])
        if meters:
            avg_outside = np.mean([m['pct_outside_band'] for m in meters])
            status = 'Green' if avg_outside < 2 else ('Yellow' if avg_outside < 10 else 'Red')
        else:
            avg_outside = 0
            status = 'Green'
        self._section_header('Voltage Stability', status)

        nominal = voltage.get('nominal_voltage', 120)
        low = voltage.get('low_limit', nominal * 0.95)
        high = voltage.get('high_limit', nominal * 1.05)

        self._write_paragraph(
            f'This section assesses whether facility voltage stays within the acceptable '
            f'range of {low:.0f}V to {high:.0f}V (nominal {nominal}V \u00b15%). '
            f'Voltage sags can cause motors to stall, computers to restart, and sensitive '
            f'equipment to malfunction. Swells can damage insulation and shorten equipment life.'
        )

        if meters:
            total_sags = sum(m['sag_count'] for m in meters)
            total_swells = sum(m['swell_count'] for m in meters)
            worst = max(meters, key=lambda m: m['pct_outside_band'])

            self._metric_row('Meters Monitored:', str(len(meters)))
            self._metric_row('Voltage Sag Events:', str(total_sags))
            self._metric_row('Voltage Swell Events:', str(total_swells))
            if avg_outside >= 2:
                self._metric_callout_row('Most Affected:', f"{worst['meter_name']} ({worst['pct_outside_band']:.1f}% outside tolerance)")

            # Trend direction
            trend_sent = self._trend_sentence(voltage.get('daily_trend', []), 'avg_v', lower_is_better=False)
            if trend_sent:
                self._write_paragraph(trend_sent, size=9)

            self._divider(top_margin=2, bottom_margin=2)

            if avg_outside < 2:
                self._write_paragraph(
                    'Conclusion: Voltage is stable across all monitored circuits. No action required.',
                    bold=True)
            elif avg_outside < 10:
                self._write_paragraph(
                    f'Conclusion: Minor voltage deviations detected ({avg_outside:.1f}% outside tolerance). '
                    'Monitor over the next cycle. If trend persists, schedule a utility voltage review.',
                    bold=True)
            else:
                self._write_paragraph(
                    f'Conclusion: Significant voltage instability detected ({avg_outside:.1f}% outside tolerance). '
                    'A power quality audit is recommended to identify root cause.',
                    bold=True)

        if chart_path and os.path.exists(chart_path):
            self.ln(2)
            self.image(chart_path, x=10, w=190)
            self._chart_caption('Daily voltage trend for the reporting period')

    def add_current_section(self, current: Dict, chart_path: Optional[str]):
        self.add_page()
        meters = current.get('meters', [])
        if meters:
            ratios = [m['peak_current_a'] / m['avg_current_a'] for m in meters if m['avg_current_a'] > 0]
            avg_ratio = np.mean(ratios) if ratios else 1
            status = 'Green' if avg_ratio < 3 else ('Yellow' if avg_ratio < 5 else 'Red')
        else:
            avg_ratio = 1
            status = 'Green'
        self._section_header('Peak Current & Demand', status)

        self._write_paragraph(
            'This section identifies demand spikes - moments when electrical draw surges well above '
            'the average. High peak-to-average ratios increase demand charges on your utility bill '
            '(fees based on your highest draw, not total usage) and can stress electrical infrastructure.'
        )

        if meters:
            site_peak = max(m['peak_current_a'] for m in meters)
            site_avg = np.mean([m['avg_current_a'] for m in meters])
            peak_meter = max(meters, key=lambda m: m['peak_current_a'])

            self._metric_row('Highest Peak:', f"{site_peak:.0f}A ({peak_meter['meter_name']})")
            self._metric_row('Site Avg Current:', f'{site_avg:.1f}A')
            self._metric_callout_row('Peak/Avg Ratio:', f'{avg_ratio:.1f}x')
            self._metric_row('Peak Event Time:', peak_meter['peak_timestamp'][:16])

            if avg_ratio >= 3:
                self._write_paragraph(
                    'A ratio above 3x indicates demand spikes that utilities typically charge '
                    'as demand fees - billed on your single highest draw, not overall consumption.',
                    size=9)

            # Trend direction
            trend_sent = self._trend_sentence(current.get('daily_peak_trend', []), 'peak_a', lower_is_better=True)
            if trend_sent:
                self._write_paragraph(trend_sent, size=9)

            self._divider(top_margin=2, bottom_margin=2)

            if avg_ratio < 3:
                self._write_paragraph(
                    'Conclusion: Demand profile is healthy with no significant spikes. '
                    'Current demand charge exposure is low.',
                    bold=True)
            elif avg_ratio < 5:
                self._write_paragraph(
                    f'Conclusion: Moderate demand spikes detected (peak/avg {avg_ratio:.1f}x). '
                    'Review equipment startup schedules - staggering high-draw startups can reduce demand charges.',
                    bold=True)
            else:
                self._write_paragraph(
                    f'Conclusion: Large demand spikes detected (peak/avg {avg_ratio:.1f}x). '
                    'This is likely increasing demand charges. Recommend reviewing startup sequences '
                    'and considering load management controls.',
                    bold=True)

        if chart_path and os.path.exists(chart_path):
            self.ln(2)
            self.image(chart_path, x=10, w=190)
            self._chart_caption('Daily peak current for the reporting period')

    def add_frequency_section(self, freq: Dict, chart_path: Optional[str]):
        self.add_page()
        if freq.get('data_available'):
            exc = freq.get('excursion_count', 0)
            status = 'Green' if exc < 5 else ('Yellow' if exc < 20 else 'Red')
        else:
            status = None
        self._section_header('Grid Frequency', status)

        self._write_paragraph(
            'Grid frequency should hold steady at 60.00 Hz. Deviations outside 59.95-60.05 Hz '
            'can indicate grid instability. This metric is informational - frequency is controlled '
            'by the utility, not the facility. Persistent excursions should be reported to your utility provider.'
        )

        if not freq.get('data_available'):
            self._no_data_placeholder(
                'Frequency data collection is now active. Results will appear in the next report '
                'once sufficient data has been ingested.'
            )
            return

        self._metric_row('Average Frequency:', f"{freq['avg_frequency']} Hz")
        self._metric_row('Range:', f"{freq['min_frequency']}-{freq['max_frequency']} Hz")
        self._metric_callout_row('Excursions Outside Band:', f"{freq['excursion_count']} events ({freq['excursion_pct']}% of readings)")

        # Trend direction
        trend_sent = self._trend_sentence(freq.get('daily_trend', []), 'avg_hz', lower_is_better=False)
        if trend_sent:
            self._write_paragraph(trend_sent, size=9)

        self._divider(top_margin=2, bottom_margin=2)

        if freq['excursion_count'] < 5:
            self._write_paragraph(
                'Conclusion: Grid frequency is stable. No utility-side concerns.',
                bold=True)
        elif freq['excursion_count'] < 20:
            self._write_paragraph(
                f"Conclusion: {freq['excursion_count']} minor frequency deviations detected. "
                'Within normal range but worth monitoring over time.',
                bold=True)
        else:
            self._write_paragraph(
                f"Conclusion: {freq['excursion_count']} frequency excursions detected - above typical levels. "
                'Consider contacting your utility provider about grid stability.',
                bold=True)

        if chart_path and os.path.exists(chart_path):
            self.ln(2)
            self.image(chart_path, x=10, w=190)
            self._chart_caption('Daily grid frequency for the reporting period')

    def add_thd_section(self, thd: Dict, chart_path: Optional[str]):
        self.add_page()
        thd_limit_pct = thd.get('thd_limit_pct', 5.0)
        if thd.get('data_available') and thd.get('meters'):
            avg_thd = np.mean([m['avg_thd'] for m in thd['meters']])
            status = 'Green' if avg_thd < thd_limit_pct else ('Yellow' if avg_thd < thd_limit_pct + 3 else 'Red')
        else:
            avg_thd = 0
            status = None
        self._section_header('Harmonic Distortion (THD)', status)

        self._write_paragraph(
            'Harmonic distortion measures how "clean" the electrical current waveform is. '
            'High distortion (above the IEEE 519 standard of 5%) can overheat transformers, '
            'trip breakers, and void equipment warranties. Common sources include variable '
            'frequency drives (VFDs), LED drivers, and computer power supplies.'
        )

        if not thd.get('data_available'):
            self._no_data_placeholder(
                'Harmonic distortion data collection is now active. Results will appear in '
                'the next report once sufficient data has been ingested.'
            )
            return

        meters = thd.get('meters', [])
        limit = thd_limit_pct
        worst = max(meters, key=lambda m: m['avg_thd']) if meters else None
        above_count = sum(1 for m in meters if m['avg_thd'] >= limit)

        self._metric_row('IEEE 519 Limit:', f'{limit:.0f}%')
        self._metric_row('Meters Above Limit:', f'{above_count} of {len(meters)}')
        if worst:
            self._metric_callout_row('Highest THD Meter:', f"{worst['meter_name']} - {worst['avg_thd']:.1f}% avg")

        # IEEE 519 compliance status line
        if avg_thd < thd_limit_pct:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*TL_GREEN)
            self.cell(0, 6, f'  All circuits are within IEEE 519 compliance ({thd_limit_pct:.0f}% limit).', 0, 1)
        else:
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*TL_RED)
            self.cell(0, 6, f'  One or more circuits exceed the IEEE 519 limit ({thd_limit_pct:.0f}%). See Recommendations.', 0, 1)
        self.set_text_color(*ARGO_DARK)

        # Trend direction
        trend_sent = self._trend_sentence(thd.get('daily_trend', []), 'avg_thd', lower_is_better=True)
        if trend_sent:
            self._write_paragraph(trend_sent, size=9)

        self._divider(top_margin=2, bottom_margin=2)

        if avg_thd < thd_limit_pct:
            self._write_paragraph(
                f'Conclusion: Harmonic levels are within the configured limit of {thd_limit_pct:.0f}%. No action required.',
                bold=True)
        elif avg_thd < thd_limit_pct + 3:
            upper_band = thd_limit_pct + 3
            self._write_paragraph(
                f'Conclusion: Average THD of {avg_thd:.0f}% is in the caution band ({thd_limit_pct:.0f}%-{upper_band:.0f}%). '
                'Monitor for upward trend. If it rises above this range, plan a harmonic assessment.',
                bold=True)
        else:
            upper_band = thd_limit_pct + 3
            self._write_paragraph(
                f'Conclusion: Average THD of {avg_thd:.0f}% exceeds the configured limit of {thd_limit_pct:.0f}% by more than 3 percentage points '
                f'(above {upper_band:.0f}%). Recommend scheduling a harmonic assessment with a power quality specialist.',
                bold=True)

        if chart_path and os.path.exists(chart_path):
            self.ln(2)
            self.image(chart_path, x=10, w=190)
            self._chart_caption('Daily current harmonic distortion (THD) for the reporting period')

    # ── Recommended Actions Page ──────────────────────────────────────

    def add_recommendations_page(self, recommendations: List[Dict]):
        self.add_page()
        self._section_header('Recommended Actions')

        self._write_paragraph(
            'The following actions are prioritized based on this month\'s findings. '
            'High-priority items should be addressed within 30 days.'
        )

        for i, rec in enumerate(recommendations, 1):
            priority_colors = {'High': TL_RED, 'Medium': TL_YELLOW, 'Low': TL_GREEN}
            pc = priority_colors.get(rec['priority'], ARGO_GRAY)

            if self.get_y() > 250:
                self.add_page()

            y = self.get_y()

            # Left accent border line in priority color
            self.set_draw_color(*pc)
            self.set_line_width(1.2)
            self.line(10, y, 10, y + 26)
            self.set_line_width(0.2)
            self.set_draw_color(*ARGO_GRAY)

            # Number (indented from border)
            self.set_x(14)
            self.set_font('Arial', 'B', 10)
            self.set_text_color(*ARGO_DARK)
            self.cell(8, 7, f'{i}.', 0, 0)

            # Larger priority badge (22x7mm, 8pt)
            self.set_fill_color(*pc)
            self.set_text_color(*WHITE)
            self.set_font('Arial', 'B', 8)
            bx = self.get_x()
            self.rect(bx, y, 22, 7, 'F')
            self.set_xy(bx, y)
            self.cell(22, 7, rec['priority'].upper(), 0, 0, 'C')

            # Category label
            self.set_text_color(*ARGO_DARK)
            self.set_font('Arial', 'B', 9)
            self.cell(3, 7, '', 0, 0)
            self.cell(0, 7, rec['category'], 0, 1)

            # Finding
            self.set_x(36)
            self.set_font('Arial', '', 9)
            self.multi_cell(162, 5, rec['finding'])

            # Action
            self.set_x(36)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(*ARGO_NAVY)
            self.multi_cell(162, 5, f"Action: {rec['action']}")
            self.set_text_color(*ARGO_DARK)
            self.ln(5)

    # ── Appendix: Detailed Data ───────────────────────────────────────

    def add_appendix(self, data: Dict):
        self.add_page()
        self._section_header('Appendix: Detailed Meter Data')

        self._write_paragraph(
            'The tables below provide per-meter detail for reference. '
            'This data supports the conclusions and recommendations in the main report.',
            size=9,
        )

        # Voltage table
        voltage = data.get('voltage_stability', {})
        meters = voltage.get('meters', [])
        if meters:
            self.set_font('Arial', 'B', 10)
            self.cell(0, 7, 'Voltage Detail', 0, 1)
            self.ln(1)
            headers = ['Meter', 'Min V', 'Max V', 'Avg V', '% Outside', 'Sags', 'Swells']
            rows = []
            for m in meters:
                name = m['meter_name'][:22] if len(m['meter_name']) > 22 else m['meter_name']
                rows.append([
                    name, str(m['min_voltage']), str(m['max_voltage']),
                    str(m['avg_voltage']), f"{m['pct_outside_band']}%",
                    str(m['sag_count']), str(m['swell_count']),
                ])
            self._metric_table(headers, rows, [38, 20, 20, 20, 25, 20, 20])

        # Current table
        current = data.get('current_peaks', {})
        meters = current.get('meters', [])
        if meters:
            if self.get_y() > 220:
                self.add_page()
            self.set_font('Arial', 'B', 10)
            self.cell(0, 7, 'Peak Current Detail', 0, 1)
            self.ln(1)
            headers = ['Meter', 'Peak (A)', 'Avg (A)', 'Ratio', 'Peak Time']
            rows = []
            for m in meters:
                name = m['meter_name'][:22] if len(m['meter_name']) > 22 else m['meter_name']
                ratio = f"{m['peak_current_a'] / m['avg_current_a']:.1f}x" if m['avg_current_a'] > 0 else '-'
                ts = m['peak_timestamp'][:16] if len(m['peak_timestamp']) > 16 else m['peak_timestamp']
                rows.append([name, str(m['peak_current_a']), str(m['avg_current_a']), ratio, ts])
            self._metric_table(headers, rows, [38, 22, 22, 18, 52])

        # THD table
        thd = data.get('thd_analysis', {})
        if thd.get('data_available') and thd.get('meters'):
            if self.get_y() > 220:
                self.add_page()
            self.set_font('Arial', 'B', 10)
            self.cell(0, 7, 'Harmonic Distortion Detail', 0, 1)
            self.ln(1)
            headers = ['Meter', 'Avg THD %', 'Max THD %', 'Above 5% Count']
            rows = []
            for m in thd['meters']:
                name = m['meter_name'][:28] if len(m['meter_name']) > 28 else m['meter_name']
                rows.append([name, str(m['avg_thd']), str(m['max_thd']), str(m['above_limit_count'])])
            self._metric_table(headers, rows, [50, 30, 30, 35])

        # Neutral current table
        neutral = data.get('neutral_current', {})
        if neutral.get('data_available') and neutral.get('meters'):
            if self.get_y() > 220:
                self.add_page()
            self.set_font('Arial', 'B', 10)
            self.cell(0, 7, 'Neutral Current Detail', 0, 1)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(*ARGO_GRAY)
            self.multi_cell(0, 5,
                'Elevated neutral current indicates phase imbalance or harmonic distortion - '
                'both of which create heat in wiring and reduce capacity for additional loads.')
            self.set_text_color(*ARGO_DARK)
            self.ln(1)
            headers = ['Meter', 'Avg (A)', 'Max (A)', 'Elevated Events']
            rows = []
            for m in neutral['meters']:
                name = m['meter_name'][:28] if len(m['meter_name']) > 28 else m['meter_name']
                rows.append([name, str(m['avg_neutral_a']), str(m['max_neutral_a']),
                            str(m['elevated_count'])])
            self._metric_table(headers, rows, [50, 30, 30, 35])

        # Top peak events
        top = current.get('top_events', [])
        if top:
            if self.get_y() > 220:
                self.add_page()
            self.set_font('Arial', 'B', 10)
            self.cell(0, 7, f'Top {len(top)} Peak Current Events', 0, 1)
            self.ln(1)
            headers = ['Meter', 'Current (A)', 'Timestamp']
            rows = []
            for evt in top[:10]:
                name = evt['meter_name'][:28] if len(evt['meter_name']) > 28 else evt['meter_name']
                rows.append([name, str(evt['current_a']), evt['timestamp'][:19]])
            self._metric_table(headers, rows, [50, 30, 65])


# ═══════════════════════════════════════════════════════════════════════
# Report Generator (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════

class ElectricalHealthReportGenerator:
    """Orchestrates data fetching, chart generation, and PDF assembly.

    Stage 4 (Deliver) - calls Stage 3 (Analyze) functions,
    formats output into an executive-focused PDF.
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
        with self.conn.cursor() as cur:
            cur.execute("SELECT site_name FROM v_sites WHERE site_id = %s",
                        (str(self.site_id),))
            row = cur.fetchone()
            return row[0] if row else f'Site {self.site_id}'

    def generate(self) -> str:
        """Main generation pipeline. Returns output PDF path."""
        import sys
        from pathlib import Path
        pkg_root = Path(__file__).resolve().parent.parent.parent
        if str(pkg_root / 'python_scripts') not in sys.path:
            sys.path.insert(0, str(pkg_root / 'python_scripts'))

        from analyze.electrical_health import generate_electrical_health_data

        with tempfile.TemporaryDirectory() as chart_dir:
            # 1. Analytics data (Stage 3)
            data = generate_electrical_health_data(
                self.conn, self.site_id, self.start_date, self.end_date,
                self.nominal_voltage,
            )

            # 2. Recommendations
            recommendations = _generate_recommendations(data)

            # 3. Site name
            site_name = self._get_site_name()

            # 4. Charts
            voltage_chart = generate_voltage_chart(data['voltage_stability'], chart_dir)
            current_chart = generate_current_chart(data['current_peaks'], chart_dir)
            frequency_chart = generate_frequency_chart(data['frequency_excursions'], chart_dir)
            thd_chart = generate_thd_chart(data['thd_analysis'], chart_dir)

            # 5. PDF assembly
            pdf = ElectricalHealthPDF()
            pdf.set_auto_page_break(auto=True, margin=20)

            pdf.add_cover_page(site_name, self.start_date, self.end_date)
            pdf.add_executive_summary(data, recommendations)
            pdf.add_voltage_section(data['voltage_stability'], voltage_chart)
            pdf.add_current_section(data['current_peaks'], current_chart)
            pdf.add_frequency_section(data['frequency_excursions'], frequency_chart)
            pdf.add_thd_section(data['thd_analysis'], thd_chart)
            pdf.add_recommendations_page(recommendations)
            pdf.add_appendix(data)

            # 6. Save
            filename = f"electrical-health-{self.site_id}-{self.start_date}-to-{self.end_date}.pdf"
            output_path = os.path.join(self.output_dir, filename)
            os.makedirs(self.output_dir, exist_ok=True)
            pdf.output(output_path)

        print(f"Report generated: {output_path}")
        return output_path
