"""
Asset Health & Use Assessment Report — PDF Generator

Non-technical, impact-focused PDF for Westchester Country Day School
facilities and operations managers.

Answers the question: which pieces of equipment are consuming the most
energy, what is it costing, and what should we do about it?

Following Argo governance: Stage 4 (Deliver — Presentation)
Charts via matplotlib, PDF assembly via fpdf2.
"""

import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pytz
from fpdf import FPDF

plt.style.use('seaborn-v0_8-darkgrid')

# ── Path wiring: resolve python_scripts sibling package ──────────────────────
_SCRIPTS_PKG = Path(__file__).resolve().parent.parent.parent.parent / 'python_scripts'
if str(_SCRIPTS_PKG) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_PKG))

from config.report_config import is_business_hours, DEFAULT_CONFIG

# ── Argo brand palette ────────────────────────────────────────────────────────
ARGO_NAVY       = (26,  37,  52)
ARGO_GREEN      = (57, 208,  43)
ARGO_DARK       = (31,  41,  55)
ARGO_RED        = (239,  68,  68)
ARGO_AMBER      = (245, 158,  11)
ARGO_GRAY       = (107, 114, 128)
ARGO_LIGHT_GRAY = (243, 244, 246)
WHITE           = (255, 255, 255)

# Traffic-light colors
TL_GREEN  = (34,  197,  94)
TL_YELLOW = (234, 179,   8)
TL_RED    = (220,  38,  38)

# ── WCDS-specific constants ───────────────────────────────────────────────────
WCDS_RATE_PER_KWH = 0.115   # $0.115/kWh — client-specified
WCDS_CHANNEL_IDS  = [
    162119, 162120, 162121, 162122,
    162123, 162285, 162319, 162320,
]

# Plain-English name mapping keyed on the code prefix in the raw meter_name
ASSET_NAME_MAP = {
    'RTU-1':  'Rooftop Unit 1',
    'RTU-2':  'Rooftop Unit 2',
    'RTU-3':  'Rooftop Unit 3',
    'AHU-1A': 'Air Handler 1A',
    'AHU-1B': 'Air Handler 1B',
    'AHU-2':  'Air Handler 2',
    'CDPK':   'Kitchen — Main Panel',
    'CDKH':   'Kitchen — Secondary Panel',
}

_ET = pytz.timezone('America/New_York')


# ═══════════════════════════════════════════════════════════════════════════════
# Data Utilities
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_asset_name(meter_name: str) -> str:
    """Map raw DB meter_name to plain-English asset name.

    Iterates ASSET_NAME_MAP keys; returns the mapped value for the first
    key found as a substring of meter_name. Falls back to the raw name.
    """
    for code, plain_name in ASSET_NAME_MAP.items():
        if code in meter_name:
            return plain_name
    return meter_name


def _to_et(ts: datetime) -> datetime:
    """Convert a datetime (naive UTC or tz-aware) to Eastern Time."""
    if ts.tzinfo is None:
        ts = pytz.utc.localize(ts)
    return ts.astimezone(_ET)


def fetch_asset_data(
    conn,
    site_id: str,
    channel_ids: List[int],
    start_date: str,
    end_date: str,
) -> Tuple[str, List[Dict]]:
    """Fetch all asset readings for the reporting period.

    Governance: reads only through Layer 3 views (v_sites, v_meters,
    v_readings_enriched). No raw table access.

    Returns (site_name, list_of_asset_dicts).
    Each asset dict:
        {
            'meter_id':   int,
            'meter_name': str,   # raw DB name
            'asset_name': str,   # plain-English via resolve_asset_name()
            'readings': [
                {'ts': datetime, 'energy_kwh': float, 'power_kw': float},
                ...
            ]
        }
    """
    with conn.cursor() as cur:
        # Site name
        cur.execute(
            "SELECT site_name FROM v_sites WHERE site_id = %s",
            (str(site_id),)
        )
        row = cur.fetchone()
        site_name = row[0] if row else f'Site {site_id}'

        # Meter roster — filtered to the known WCDS channel IDs
        placeholders = ','.join(['%s'] * len(channel_ids))
        cur.execute(
            f"SELECT meter_id, meter_name FROM v_meters "
            f"WHERE site_id = %s AND meter_id IN ({placeholders}) "
            f"ORDER BY meter_name",
            [str(site_id)] + [str(c) for c in channel_ids]
        )
        meters = cur.fetchall()

        assets = []
        for meter_id, meter_name in meters:
            cur.execute(
                """
                SELECT timestamp  AS ts,
                       energy_kwh,
                       power_kw
                FROM   v_readings_enriched
                WHERE  meter_id  = %s
                  AND  timestamp >= %s
                  AND  timestamp <= %s
                ORDER BY timestamp
                """,
                (str(meter_id), start_date, end_date)
            )
            readings = [
                {
                    'ts':         r[0],
                    'energy_kwh': r[1] or 0.0,
                    'power_kw':   r[2] or 0.0,
                }
                for r in cur.fetchall()
            ]
            assets.append({
                'meter_id':   meter_id,
                'meter_name': meter_name,
                'asset_name': resolve_asset_name(meter_name),
                'readings':   readings,
            })

    return site_name, assets


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════════════════════════

def _empty_metrics(asset: Dict) -> Dict:
    return {
        'asset_name':       asset['asset_name'],
        'meter_id':         asset['meter_id'],
        'total_kwh':        0.0,
        'total_cost':       0.0,
        'avg_daily_kwh':    0.0,
        'peak_power_kw':    0.0,
        'after_hours_kwh':  0.0,
        'after_hours_pct':  0.0,
        'after_hours_flag': False,
        'health_status':    None,
        'status_note':      None,
    }


def compute_asset_metrics(asset: Dict, rate: float, config: Dict) -> Dict:
    """Compute all KPIs for a single asset.

    Returns a metrics dict (health_status and status_note are None until
    assign_health_status() is called across the full ranked list).
    """
    readings = asset['readings']
    if not readings:
        return _empty_metrics(asset)

    total_kwh     = sum(r['energy_kwh'] for r in readings)
    total_cost    = total_kwh * rate
    peak_power_kw = max((r['power_kw'] for r in readings), default=0.0)

    timestamps    = [r['ts'] for r in readings]
    days_spanned  = max(1, (max(timestamps) - min(timestamps)).days + 1)
    avg_daily_kwh = total_kwh / days_spanned

    # After-hours classification — convert to ET before checking schedule
    after_hours_kwh = 0.0
    for r in readings:
        ts_et = _to_et(r['ts']) if isinstance(r['ts'], datetime) else r['ts']
        if not is_business_hours(ts_et, config):
            after_hours_kwh += r['energy_kwh']

    after_hours_pct  = (after_hours_kwh / total_kwh * 100) if total_kwh > 0 else 0.0
    after_hours_flag = after_hours_pct > 20.0

    return {
        'asset_name':       asset['asset_name'],
        'meter_id':         asset['meter_id'],
        'total_kwh':        round(total_kwh, 2),
        'total_cost':       round(total_cost, 2),
        'avg_daily_kwh':    round(avg_daily_kwh, 2),
        'peak_power_kw':    round(peak_power_kw, 2),
        'after_hours_kwh':  round(after_hours_kwh, 2),
        'after_hours_pct':  round(after_hours_pct, 1),
        'after_hours_flag': after_hours_flag,
        'health_status':    None,
        'status_note':      None,
    }


def _build_status_note(m: Dict) -> str:
    """One plain-English sentence describing the asset's status."""
    if m['health_status'] == 'Red':
        if m['after_hours_pct'] > 20.0:
            return (
                f"Running {m['after_hours_pct']:.0f}% of its energy after school hours "
                f"— review scheduling."
            )
        return (
            f"Highest-consumption asset this period at "
            f"{m['total_kwh']:.0f} kWh (${m['total_cost']:.0f})."
        )
    elif m['health_status'] == 'Yellow':
        if m['after_hours_pct'] > 5.0:
            return (
                f"Some after-hours activity detected "
                f"({m['after_hours_pct']:.0f}% of energy use)."
            )
        return "Mid-range consumer — no immediate concerns."
    else:
        return "Operating efficiently within expected parameters."


def assign_health_status(metrics_list: List[Dict]) -> List[Dict]:
    """Assign Red/Yellow/Green status after all assets are ranked by kWh.

    Rules (after-hours override takes precedence):
      RED    — top-2 kWh consumers, OR after_hours_pct > 20%
      YELLOW — ranks 3-5, OR 5% < after_hours_pct <= 20%
      GREEN  — ranks 6+, AND after_hours_pct <= 5%
    """
    sorted_by_kwh = sorted(metrics_list, key=lambda m: m['total_kwh'], reverse=True)
    rank_map      = {m['meter_id']: i for i, m in enumerate(sorted_by_kwh)}

    for m in metrics_list:
        rank   = rank_map[m['meter_id']]   # 0-indexed
        ah_pct = m['after_hours_pct']

        if rank < 2 or ah_pct > 20.0:
            m['health_status'] = 'Red'
        elif rank < 5 or ah_pct > 5.0:
            m['health_status'] = 'Yellow'
        else:
            m['health_status'] = 'Green'

        m['status_note'] = _build_status_note(m)

    return metrics_list


def _generate_recommendations(metrics_list: List[Dict], period_days: int) -> List[str]:
    """Generate 3-5 plain-language action items for facilities managers.

    Ordered by impact: after-hours offenders → top consumer →
    peak-power note → annual cost projection → positive note.
    """
    recs: List[str] = []

    # After-hours offenders
    ah_assets = sorted(
        [m for m in metrics_list if m['after_hours_flag']],
        key=lambda m: m['after_hours_pct'], reverse=True,
    )
    if ah_assets:
        worst = ah_assets[0]
        savings_est = worst['after_hours_kwh'] * WCDS_RATE_PER_KWH
        recs.append(
            f"Review the scheduling timer on {worst['asset_name']}: "
            f"{worst['after_hours_pct']:.0f}% of its energy ran outside school hours "
            f"({worst['after_hours_kwh']:.0f} kWh, ${savings_est:.0f} over this period). "
            f"A schedule audit could eliminate this waste."
        )

    # Top consumer
    top = max(metrics_list, key=lambda m: m['total_kwh'])
    recs.append(
        f"{top['asset_name']} was the highest energy consumer "
        f"({top['total_kwh']:.0f} kWh, ${top['total_cost']:.0f} for the period). "
        f"Confirm setpoints and occupancy schedules are optimized."
    )

    # Notable peak power (only add if not already the top consumer)
    high_peak = sorted(metrics_list, key=lambda m: m['peak_power_kw'], reverse=True)
    for m in high_peak[:2]:
        if m['meter_id'] != top['meter_id'] and m['avg_daily_kwh'] > 0:
            recs.append(
                f"Consider a seasonal energy audit of {m['asset_name']}, "
                f"which peaked at {m['peak_power_kw']:.1f} kW. "
                f"Verifying refrigerant levels and filter condition can improve efficiency."
            )
            break

    # Annual cost projection
    total_cost  = sum(m['total_cost'] for m in metrics_list)
    annual_proj = total_cost * (365 / max(period_days, 1))
    recs.append(
        f"At current consumption rates, total facility energy for monitored assets "
        f"is on track to cost approximately ${annual_proj:,.0f} annually. "
        f"Addressing the after-hours and scheduling items above could reduce this by 10-20%."
    )

    # Positive note if majority are green
    green_count = sum(1 for m in metrics_list if m['health_status'] == 'Green')
    if green_count >= 4:
        recs.append(
            f"{green_count} of {len(metrics_list)} assets are operating "
            f"efficiently within expected parameters — no immediate action needed on those units."
        )

    return recs[:5]


# ═══════════════════════════════════════════════════════════════════════════════
# Chart Generation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_ranking_chart(metrics_list: List[Dict], chart_dir: str) -> str:
    """Generate a horizontal bar chart of assets ranked by kWh.

    Bars are colored by health status (Red/Yellow/Green) and annotated
    with dollar cost. Returns path to saved PNG.
    """
    # Sort ascending so the highest-kWh bar renders at the top
    sorted_assets = sorted(metrics_list, key=lambda m: m['total_kwh'])

    names  = [m['asset_name']  for m in sorted_assets]
    kwh    = [m['total_kwh']   for m in sorted_assets]
    costs  = [m['total_cost']  for m in sorted_assets]

    status_color_map = {
        'Red':    tuple(c / 255 for c in TL_RED),
        'Yellow': tuple(c / 255 for c in TL_YELLOW),
        'Green':  tuple(c / 255 for c in TL_GREEN),
    }
    colors = [status_color_map.get(m['health_status'],
                                   tuple(c / 255 for c in ARGO_GRAY))
              for m in sorted_assets]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(names, kwh, color=colors, alpha=0.85, height=0.6)

    # Dollar cost annotations at the end of each bar
    max_kwh = max(kwh) if kwh else 1
    for bar, cost in zip(bars, costs):
        w = bar.get_width()
        ax.text(
            w + max_kwh * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f'${cost:,.0f}',
            va='center', ha='left', fontsize=9,
            color='#374151', fontweight='bold',
        )

    ax.set_xlabel('Energy Use (kWh)', fontsize=10)
    ax.set_title('Asset Energy Ranking — Reporting Period', fontsize=12,
                 fontweight='bold', color='#1a2534')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Extra right margin so cost labels don't clip
    ax.set_xlim(right=max_kwh * 1.18)

    legend_items = [
        mpatches.Patch(color=status_color_map['Red'],    label='High Priority'),
        mpatches.Patch(color=status_color_map['Yellow'], label='Monitor'),
        mpatches.Patch(color=status_color_map['Green'],  label='Good'),
    ]
    ax.legend(handles=legend_items, loc='lower right', fontsize=9)

    plt.tight_layout()
    path = os.path.join(chart_dir, 'asset_ranking.png')
    plt.savefig(path, dpi=180, bbox_inches='tight')
    plt.close()
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# PDF Class
# ═══════════════════════════════════════════════════════════════════════════════

class AssetHealthPDF(FPDF):
    """Argo-branded PDF for the Asset Health & Use Assessment."""

    # ── Header / Footer ───────────────────────────────────────────────────────

    def header(self):
        if self.page_no() == 1:
            return
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.jpg')
        has_logo  = os.path.exists(logo_path)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*ARGO_NAVY)
        title_w = 170 if has_logo else 0
        self.cell(title_w, 8, 'Asset Health & Use Assessment', 0, 0, 'L')
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

    # ── Layout Helpers ────────────────────────────────────────────────────────

    def _traffic_light(self, status: str, x: float, y: float,
                       w: float = 40, h: float = 12):
        """Draw a traffic-light badge at (x, y)."""
        colors = {'Green': TL_GREEN, 'Yellow': TL_YELLOW, 'Red': TL_RED}
        labels = {'Green': 'GOOD', 'Yellow': 'MONITOR', 'Red': 'ACTION NEEDED'}
        color = colors.get(status, ARGO_GRAY)
        label = labels.get(status, status)
        self.set_fill_color(*color)
        self.rect(x, y, w, h, 'F')
        self.set_xy(x, y + 2)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(*WHITE)
        self.cell(w, h - 4, label, 0, 0, 'C')
        self.set_text_color(*ARGO_DARK)

    def _section_header(self, title: str):
        self.set_fill_color(*ARGO_NAVY)
        self.set_text_color(*WHITE)
        self.set_font('Arial', 'B', 14)
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

    def _metric_callout_row(self, label: str, value: str, indent: float = 15):
        """Highlighted label+value row with light-gray background."""
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

    def _divider(self, top_margin: float = 3, bottom_margin: float = 3):
        self.ln(top_margin)
        self.set_draw_color(*ARGO_LIGHT_GRAY)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(bottom_margin)

    def _chart_caption(self, text: str):
        if not hasattr(self, '_figure_counter'):
            self._figure_counter = 0
        self._figure_counter += 1
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*ARGO_GRAY)
        self.cell(0, 5, f'Figure {self._figure_counter}: {text}', 0, 1, 'C')
        self.set_text_color(*ARGO_DARK)
        self.ln(2)

    # ── Cover Page ────────────────────────────────────────────────────────────

    def add_cover_page(self, site_name: str, start_date: str, end_date: str):
        self.add_page()

        # Primary navy header band
        self.set_fill_color(*ARGO_NAVY)
        self.rect(0, 0, 210, 80, 'F')

        # Accent band below header
        self.set_fill_color(44, 52, 68)
        self.rect(0, 80, 210, 8, 'F')

        # Title text
        self.set_y(16)
        self.set_font('Arial', 'B', 28)
        self.set_text_color(*WHITE)
        self.cell(0, 14, 'Asset Health & Use', 0, 1, 'C')
        self.cell(0, 14, 'Assessment', 0, 1, 'C')
        self.set_font('Arial', '', 13)
        self.cell(0, 9, 'Facilities & Operations Energy Report', 0, 1, 'C')

        # Logo centered below header band
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.jpg')
        if os.path.exists(logo_path):
            self.image(logo_path, x=70, y=94, w=70)
            content_y = 175
        else:
            self.set_y(100)
            self.set_text_color(*ARGO_DARK)
            self.set_font('Arial', 'B', 18)
            self.cell(0, 10, 'Argo Energy Solutions', 0, 1, 'C')
            content_y = 125

        # Date formatting
        try:
            dt_start  = datetime.strptime(start_date, '%Y-%m-%d')
            dt_end    = datetime.strptime(end_date,   '%Y-%m-%d')
            fmt_start = dt_start.strftime('%B %-d, %Y')
            fmt_end   = dt_end.strftime('%B %-d, %Y')
            period_str = f'{fmt_start} — {fmt_end}'
        except ValueError:
            period_str = f'{start_date} — {end_date}'

        # Metadata block
        self.set_y(content_y)
        self.set_text_color(*ARGO_DARK)
        self.set_font('Arial', '', 13)
        self.cell(0, 10, f'Prepared for: {site_name}', 0, 1, 'C')
        self.cell(0, 10, f'Report Period: {period_str}', 0, 1, 'C')
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%B %-d, %Y")}', 0, 1, 'C')

        # Footer band
        self.set_fill_color(*ARGO_NAVY)
        self.rect(0, 265, 210, 32, 'F')
        self.set_y(270)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*WHITE)
        self.cell(0, 8, 'Argo Energy Solutions', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 7, 'Facilities | Operations | Energy Report', 0, 1, 'C')

    # ── Executive Overview ────────────────────────────────────────────────────

    def add_executive_overview(
        self,
        total_kwh:  float,
        total_cost: float,
        top_asset:  str,
        start_date: str,
        end_date:   str,
    ):
        """Page 2: three side-by-side headline metric callout boxes."""
        self.add_page()
        self._section_header('Executive Overview')

        self._write_paragraph(
            'This report summarises energy use and estimated costs for all monitored equipment '
            'at this facility over the reporting period. Assets are evaluated by total consumption, '
            'after-hours activity, and peak demand — and given a plain-language health status '
            '(Good / Monitor / Action Needed) to help prioritise facilities decisions.'
        )
        self.ln(2)

        # Three metric callout boxes side-by-side
        box_w = 56
        box_h = 34
        box_y = self.get_y()
        gap   = 5
        start_x = (210 - 3 * box_w - 2 * gap) / 2  # centre three boxes

        box_configs = [
            ('Total Facility kWh', f'{total_kwh:,.0f} kWh',     'Monitored assets, period total'),
            ('Total Period Cost',  f'${total_cost:,.2f}',        f'At ${WCDS_RATE_PER_KWH}/kWh'),
            ('Top Consumer',       top_asset,                    'Highest energy-use asset'),
        ]

        for i, (heading, value, sub) in enumerate(box_configs):
            bx = start_x + i * (box_w + gap)

            # Box background
            self.set_fill_color(*ARGO_LIGHT_GRAY)
            self.set_draw_color(*ARGO_NAVY)
            self.rect(bx, box_y, box_w, box_h, 'FD')

            # Navy heading strip
            self.set_fill_color(*ARGO_NAVY)
            self.rect(bx, box_y, box_w, 9, 'F')
            self.set_xy(bx, box_y + 1)
            self.set_font('Arial', 'B', 7)
            self.set_text_color(*WHITE)
            self.cell(box_w, 7, heading.upper(), 0, 0, 'C')

            # Large value
            self.set_xy(bx, box_y + 11)
            self.set_font('Arial', 'B', 11)
            self.set_text_color(*ARGO_NAVY)
            self.cell(box_w, 9, value, 0, 1, 'C')

            # Sub-label
            self.set_x(bx)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(*ARGO_GRAY)
            self.cell(box_w, 6, sub, 0, 0, 'C')

        self.set_text_color(*ARGO_DARK)
        self.set_y(box_y + box_h + 6)

        # Period annotation
        try:
            dt_start  = datetime.strptime(start_date, '%Y-%m-%d')
            dt_end    = datetime.strptime(end_date,   '%Y-%m-%d')
            fmt_start = dt_start.strftime('%B %-d')
            fmt_end   = dt_end.strftime('%B %-d, %Y')
            period_str = f'{fmt_start} — {fmt_end}'
        except ValueError:
            period_str = f'{start_date} — {end_date}'

        self.set_font('Arial', 'I', 9)
        self.set_text_color(*ARGO_GRAY)
        self.cell(0, 6, f'Reporting period: {period_str}', 0, 1, 'C')
        self.set_text_color(*ARGO_DARK)
        self.ln(4)

    # ── Ranking Chart Page ────────────────────────────────────────────────────

    def add_ranking_chart_page(self, chart_path: str):
        """Full-width horizontal bar chart: assets ranked by kWh."""
        self.add_page()
        self._section_header('Asset Energy Ranking')

        self._write_paragraph(
            'The chart below ranks each monitored asset by total energy consumption for the '
            'reporting period. Bar colour indicates health status: red bars are the highest '
            'consumers or have notable after-hours activity; yellow bars are mid-range or '
            'have some off-hours use; green bars are operating within expected parameters. '
            'Dollar amounts show the estimated cost at $0.115/kWh.'
        )

        if os.path.exists(chart_path):
            self.image(chart_path, x=10, w=190)
            self._chart_caption('Assets ranked by total energy consumption — reporting period')

    # ── Asset Detail Cards ────────────────────────────────────────────────────

    def add_asset_detail_section(self, metrics_list: List[Dict]):
        """One card per asset — two cards per A4 page."""
        self.add_page()
        self._section_header('Asset Detail')

        self._write_paragraph(
            'Each card below summarises one monitored asset. The coloured left bar and '
            'status badge correspond to the same traffic-light logic used in the ranking chart.'
        )
        self.ln(2)

        card_h  = 55    # mm per card
        card_gap = 6    # mm between cards
        card_x  = 12
        card_w  = 186

        for idx, m in enumerate(metrics_list):
            # Two cards per page; start a new page after the second card
            if idx > 0 and idx % 2 == 0:
                self.add_page()
                self.ln(4)

            y = self.get_y()

            # Guard: if card would overflow page, start a new page
            if y + card_h > 270:
                self.add_page()
                self.ln(4)
                y = self.get_y()

            status_colors = {'Red': TL_RED, 'Yellow': TL_YELLOW, 'Green': TL_GREEN}
            sc = status_colors.get(m['health_status'], ARGO_GRAY)

            # Card background
            self.set_fill_color(*ARGO_LIGHT_GRAY)
            self.rect(card_x, y, card_w, card_h, 'F')

            # Coloured left accent bar
            self.set_fill_color(*sc)
            self.rect(card_x, y, 3, card_h, 'F')

            # ── Row 1: Asset name + traffic-light badge ──
            self.set_xy(card_x + 6, y + 4)
            self.set_font('Arial', 'B', 13)
            self.set_text_color(*ARGO_DARK)
            self.cell(110, 8, m['asset_name'], 0, 0)

            # Traffic-light badge (right-aligned)
            badge_w = 44
            badge_x = card_x + card_w - badge_w - 4
            self._traffic_light(m['health_status'], badge_x, y + 3, w=badge_w, h=10)

            # ── Thin divider below name row ──
            div_y = y + 14
            self.set_draw_color(*ARGO_GRAY)
            self.set_line_width(0.2)
            self.line(card_x + 4, div_y, card_x + card_w - 4, div_y)
            self.set_draw_color(*ARGO_DARK)

            # ── Row 2: kWh | Cost | Peak ──
            self.set_xy(card_x + 6, y + 17)
            self.set_font('Arial', '', 9)
            self.set_text_color(*ARGO_GRAY)
            self.cell(30, 5, 'Period kWh:', 0, 0)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*ARGO_DARK)
            self.cell(28, 5, f'{m["total_kwh"]:,.0f}', 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(*ARGO_GRAY)
            self.cell(20, 5, 'Cost:', 0, 0)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*ARGO_DARK)
            self.cell(28, 5, f'${m["total_cost"]:,.2f}', 0, 0)
            self.set_font('Arial', '', 9)
            self.set_text_color(*ARGO_GRAY)
            self.cell(18, 5, 'Peak kW:', 0, 0)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*ARGO_DARK)
            self.cell(0, 5, f'{m["peak_power_kw"]:.1f}', 0, 1)

            # ── Row 3: Avg Daily kWh ──
            self.set_xy(card_x + 6, y + 24)
            self.set_font('Arial', '', 9)
            self.set_text_color(*ARGO_GRAY)
            self.cell(30, 5, 'Avg Daily:', 0, 0)
            self.set_font('Arial', 'B', 9)
            self.set_text_color(*ARGO_DARK)
            self.cell(0, 5, f'{m["avg_daily_kwh"]:.1f} kWh/day', 0, 1)

            # ── Row 4: After-hours ──
            self.set_xy(card_x + 6, y + 31)
            self.set_font('Arial', '', 9)
            if m['after_hours_flag']:
                self.set_text_color(*ARGO_AMBER)
                ah_text = (
                    f"After-hours: {m['after_hours_pct']:.0f}% of energy "
                    f"({m['after_hours_kwh']:.0f} kWh) — outside school hours"
                )
                self.set_font('Arial', 'I', 9)
            else:
                self.set_text_color(*ARGO_GRAY)
                ah_pct_str = f'{m["after_hours_pct"]:.0f}%' if m['after_hours_pct'] > 0 else 'none'
                ah_text = f'After-hours activity: {ah_pct_str} — within normal range'
            self.cell(0, 5, ah_text, 0, 1)

            # ── Row 5: Status note ──
            self.set_xy(card_x + 6, y + 39)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(*ARGO_GRAY)
            self.cell(card_w - 10, 5, m['status_note'] or '', 0, 1)

            # Advance cursor below card
            self.set_y(y + card_h + card_gap)
            self.set_text_color(*ARGO_DARK)

    # ── Financial Summary ─────────────────────────────────────────────────────

    def add_financial_summary(self, metrics_list: List[Dict], period_days: int):
        """Financial Impact Summary page."""
        self.add_page()
        self._section_header('Financial Impact Summary')

        self._write_paragraph(
            'The figures below show estimated costs for the reporting period along with '
            'projections based on current consumption rates. Savings estimates assume '
            'that after-hours energy use identified in this report is eliminated through '
            'schedule corrections.'
        )
        self.ln(2)

        period_cost  = sum(m['total_cost']       for m in metrics_list)
        period_kwh   = sum(m['total_kwh']        for m in metrics_list)
        monthly_proj = period_cost * (30  / max(period_days, 1))
        annual_proj  = period_cost * (365 / max(period_days, 1))

        # After-hours savings estimate
        ah_kwh_flagged = sum(
            m['after_hours_kwh'] for m in metrics_list if m['after_hours_flag']
        )
        savings_est = ah_kwh_flagged * WCDS_RATE_PER_KWH

        self._metric_callout_row('Period Total (kWh):',     f'{period_kwh:,.0f} kWh')
        self._metric_callout_row('Period Total Cost:',      f'${period_cost:,.2f}')
        self._metric_callout_row('Monthly Projection:',     f'${monthly_proj:,.2f}')
        self._metric_callout_row('Annual Projection:',      f'${annual_proj:,.2f}')

        self._divider()

        self._metric_callout_row(
            'After-hours kWh (flagged assets):',
            f'{ah_kwh_flagged:,.0f} kWh',
        )
        self._metric_callout_row(
            'Est. Savings if After-hours Eliminated:',
            f'${savings_est:,.2f} / period  (${savings_est * 365 / max(period_days, 1):,.0f} / yr)',
        )

        self.ln(4)
        self._write_paragraph(
            f'Note: cost estimates use a flat rate of ${WCDS_RATE_PER_KWH}/kWh. '
            f'Actual utility invoices may include demand charges, taxes, and other fees '
            f'not reflected here.',
            size=9,
        )

    # ── Recommendations Page ──────────────────────────────────────────────────

    def add_recommendations_page(self, recommendations: List[str]):
        """Numbered plain-language action list for facilities managers."""
        self.add_page()
        self._section_header('Recommended Actions')

        self._write_paragraph(
            'The following actions are prioritised based on this period\'s findings. '
            'Items are ordered by potential impact — the first item typically represents '
            'the largest single opportunity for cost reduction.'
        )

        for i, rec in enumerate(recommendations, 1):
            if self.get_y() > 245:
                self.add_page()

            y = self.get_y()

            # Left accent border (navy)
            self.set_draw_color(*ARGO_NAVY)
            self.set_line_width(1.2)
            self.line(10, y, 10, y + 28)
            self.set_line_width(0.2)
            self.set_draw_color(*ARGO_GRAY)

            # Item number
            self.set_x(14)
            self.set_font('Arial', 'B', 11)
            self.set_text_color(*ARGO_NAVY)
            self.cell(8, 7, f'{i}.', 0, 0)

            # Recommendation text
            self.set_font('Arial', '', 10)
            self.set_text_color(*ARGO_DARK)
            self.multi_cell(170, 5, rec)
            self.ln(5)

        self.set_text_color(*ARGO_DARK)


# ═══════════════════════════════════════════════════════════════════════════════
# Report Generator (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════════

class AssetHealthReportGenerator:
    """Stage 4 (Deliver) orchestrator for the Asset Health & Use PDF.

    Wires together: DB queries → analytics → chart → PDF assembly.
    Reads exclusively through Layer 3 views (v_sites, v_meters,
    v_readings_enriched). No raw table access.
    """

    def __init__(
        self,
        conn,
        site_id:     str,
        start_date:  str,
        end_date:    str,
        rate:        float      = WCDS_RATE_PER_KWH,
        channel_ids: List[int]  = None,
        output_dir:  str        = 'reports',
    ):
        self.conn        = conn
        self.site_id     = site_id
        self.start_date  = start_date
        self.end_date    = end_date
        self.rate        = rate
        self.channel_ids = channel_ids or WCDS_CHANNEL_IDS
        self.output_dir  = output_dir

    def generate(self) -> str:
        """Run the full pipeline and return the absolute path to the PDF."""
        period_days = (
            datetime.strptime(self.end_date,   '%Y-%m-%d') -
            datetime.strptime(self.start_date, '%Y-%m-%d')
        ).days + 1

        with tempfile.TemporaryDirectory() as chart_dir:
            # 1. Fetch data (Layer 3 views only)
            site_name, assets = fetch_asset_data(
                self.conn,
                self.site_id,
                self.channel_ids,
                self.start_date,
                self.end_date,
            )

            # 2. Per-asset metrics
            config      = DEFAULT_CONFIG
            raw_metrics = [
                compute_asset_metrics(a, self.rate, config) for a in assets
            ]

            # 3. Traffic-light health status (ranking-dependent)
            metrics = assign_health_status(raw_metrics)

            # 4. Executive overview aggregates
            total_kwh  = sum(m['total_kwh']  for m in metrics)
            total_cost = sum(m['total_cost'] for m in metrics)
            top_asset  = (
                max(metrics, key=lambda m: m['total_kwh'])['asset_name']
                if metrics else 'N/A'
            )

            # 5. Plain-language recommendations
            recommendations = _generate_recommendations(metrics, period_days)

            # 6. Ranking chart
            chart_path = generate_ranking_chart(metrics, chart_dir)

            # 7. PDF assembly
            pdf = AssetHealthPDF()
            pdf.set_auto_page_break(auto=True, margin=20)

            pdf.add_cover_page(site_name, self.start_date, self.end_date)
            pdf.add_executive_overview(
                total_kwh, total_cost, top_asset,
                self.start_date, self.end_date,
            )
            pdf.add_ranking_chart_page(chart_path)
            pdf.add_asset_detail_section(metrics)
            pdf.add_financial_summary(metrics, period_days)
            pdf.add_recommendations_page(recommendations)

            # 8. Save
            fname    = (
                f"asset-health-{self.site_id}-"
                f"{self.start_date}-to-{self.end_date}.pdf"
            )
            out_path = os.path.join(self.output_dir, fname)
            os.makedirs(self.output_dir, exist_ok=True)
            pdf.output(out_path)

        print(f"Report generated: {out_path}")
        return out_path
