"""
Electrical Health Screening Analytics

Computes voltage stability, current peaks, frequency excursions,
neutral current indicators, and THD metrics for the Electrical Health
Screening report.

Following Argo governance: Stage 3 (Analyze -- Read-Only)
All queries use Layer 3 governed views only (v_readings_enriched, v_readings_daily).

Usage:
    from analyze.electrical_health import generate_electrical_health_data
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Nominal voltage lookup (common US commercial)
NOMINAL_VOLTAGES = [120, 208, 277, 480]

# Default thresholds (can be overridden via report_config)
DEFAULT_THRESHOLDS = {
    'voltage_tolerance_pct': 5,           # +/- 5% of nominal
    'frequency_band': (59.95, 60.05),     # Hz acceptable range
    'thd_current_limit_pct': 5.0,         # IEEE 519 typical
    'neutral_current_elevated_pct': 20,   # % of avg phase current
    'health_score_weights': {
        'voltage': 0.35,
        'current': 0.25,
        'frequency': 0.20,
        'thd': 0.20,
    },
}


def detect_nominal_voltage(avg_voltage: float) -> int:
    """Determine nominal voltage from average reading.

    Returns the closest standard nominal voltage.
    """
    if avg_voltage is None or np.isnan(avg_voltage):
        return 120  # safe default
    return min(NOMINAL_VOLTAGES, key=lambda nv: abs(nv - avg_voltage))


def _fetch_readings_df(conn, site_id: str, start_date: str, end_date: str,
                       columns: List[str]) -> pd.DataFrame:
    """Fetch readings from v_readings_enriched into a DataFrame.

    Governed access: Layer 3 view only.
    """
    col_list = ', '.join(columns)
    query = f"""
        SELECT {col_list}
        FROM v_readings_enriched
        WHERE site_id = %s
          AND timestamp >= %s::timestamptz
          AND timestamp < (%s::date + INTERVAL '1 day')::timestamptz
        ORDER BY timestamp
    """
    with conn.cursor() as cur:
        cur.execute(query, (str(site_id), start_date, end_date))
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
    return pd.DataFrame(rows, columns=col_names)


def _fetch_daily_df(conn, site_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch daily aggregates from v_readings_daily.

    Governed access: Layer 3 view only.
    """
    query = """
        SELECT *
        FROM v_readings_daily
        WHERE site_id = %s
          AND reading_date >= %s::date
          AND reading_date <= %s::date
        ORDER BY meter_id, reading_date
    """
    with conn.cursor() as cur:
        cur.execute(query, (str(site_id), start_date, end_date))
        rows = cur.fetchall()
        col_names = [desc[0] for desc in cur.description]
    return pd.DataFrame(rows, columns=col_names)


def analyze_voltage_stability(
    conn, site_id: str, start_date: str, end_date: str,
    nominal_voltage: Optional[int] = None,
    thresholds: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Voltage stability analysis per meter.

    Queries v_readings_enriched for individual readings to compute
    sag/swell event counts and % outside tolerance band.
    Uses v_readings_daily for daily trend data.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    tol_pct = thresholds.get('voltage_tolerance_pct', 5)

    # Fetch per-reading voltage data
    df = _fetch_readings_df(conn, site_id, start_date, end_date,
                            ['meter_id', 'meter_name', 'timestamp', 'voltage_v'])

    if df.empty:
        return {'nominal_voltage': nominal_voltage or 120, 'meters': [], 'daily_trend': []}

    # Auto-detect nominal voltage if not provided
    avg_v = df['voltage_v'].dropna().mean()
    if nominal_voltage is None:
        nominal_voltage = detect_nominal_voltage(avg_v)

    low_limit = nominal_voltage * (1 - tol_pct / 100)
    high_limit = nominal_voltage * (1 + tol_pct / 100)

    # Per-meter stats
    meters = []
    for (mid, mname), grp in df.groupby(['meter_id', 'meter_name']):
        v = grp['voltage_v'].dropna()
        if v.empty:
            continue
        outside = v[(v < low_limit) | (v > high_limit)]
        sags = v[v < low_limit]
        swells = v[v > high_limit]

        meters.append({
            'meter_id': int(mid),
            'meter_name': mname,
            'min_voltage': round(float(v.min()), 1),
            'max_voltage': round(float(v.max()), 1),
            'avg_voltage': round(float(v.mean()), 1),
            'pct_outside_band': round(float(len(outside) / len(v) * 100), 2),
            'sag_count': int(len(sags)),
            'swell_count': int(len(swells)),
            'reading_count': int(len(v)),
        })

    # Daily trend from v_readings_daily
    daily = _fetch_daily_df(conn, site_id, start_date, end_date)
    daily_trend = []
    if not daily.empty and 'min_voltage_v' in daily.columns:
        for date, day_grp in daily.groupby('reading_date'):
            daily_trend.append({
                'date': str(date),
                'min_v': round(float(day_grp['min_voltage_v'].min()), 1),
                'max_v': round(float(day_grp['max_voltage_v'].max()), 1),
                'avg_v': round(float(day_grp['avg_voltage_v'].mean()), 1),
            })

    return {
        'nominal_voltage': nominal_voltage,
        'low_limit': round(low_limit, 1),
        'high_limit': round(high_limit, 1),
        'meters': meters,
        'daily_trend': daily_trend,
    }


def analyze_current_peaks(
    conn, site_id: str, start_date: str, end_date: str,
    top_n: int = 10,
) -> Dict[str, Any]:
    """Peak current event analysis.

    Queries v_readings_enriched for individual current readings.
    """
    df = _fetch_readings_df(conn, site_id, start_date, end_date,
                            ['meter_id', 'meter_name', 'timestamp', 'current_a'])

    if df.empty:
        return {'meters': [], 'top_events': [], 'daily_peak_trend': []}

    # Per-meter peak stats
    meters = []
    for (mid, mname), grp in df.groupby(['meter_id', 'meter_name']):
        a = grp['current_a'].dropna()
        if a.empty:
            continue
        peak_idx = a.idxmax()
        meters.append({
            'meter_id': int(mid),
            'meter_name': mname,
            'peak_current_a': round(float(a.max()), 2),
            'avg_current_a': round(float(a.mean()), 2),
            'peak_timestamp': str(grp.loc[peak_idx, 'timestamp']),
        })

    # Top N peak events across all meters
    valid = df.dropna(subset=['current_a']).nlargest(top_n, 'current_a')
    top_events = []
    for _, row in valid.iterrows():
        top_events.append({
            'meter_id': int(row['meter_id']),
            'meter_name': row['meter_name'],
            'current_a': round(float(row['current_a']), 2),
            'timestamp': str(row['timestamp']),
        })

    # Daily peak trend
    daily = _fetch_daily_df(conn, site_id, start_date, end_date)
    daily_peak_trend = []
    if not daily.empty and 'peak_current_a' in daily.columns:
        for date, day_grp in daily.groupby('reading_date'):
            daily_peak_trend.append({
                'date': str(date),
                'peak_a': round(float(day_grp['peak_current_a'].max()), 2),
            })

    return {
        'meters': meters,
        'top_events': top_events,
        'daily_peak_trend': daily_peak_trend,
    }


def analyze_frequency_excursions(
    conn, site_id: str, start_date: str, end_date: str,
    thresholds: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Frequency stability analysis.

    Returns data_available=False if no frequency_hz data exists.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    band_low, band_high = thresholds.get('frequency_band', (59.95, 60.05))

    df = _fetch_readings_df(conn, site_id, start_date, end_date,
                            ['meter_id', 'meter_name', 'timestamp', 'frequency_hz'])

    freq = df['frequency_hz'].dropna()
    if freq.empty:
        return {
            'data_available': False,
            'message': 'Frequency data not yet available. Will populate after next ingestion cycle with expanded field capture.',
        }

    excursions = freq[(freq < band_low) | (freq > band_high)]

    # Daily trend
    df_valid = df.dropna(subset=['frequency_hz']).copy()
    df_valid['date'] = pd.to_datetime(df_valid['timestamp']).dt.date
    daily_trend = []
    for date, day_grp in df_valid.groupby('date'):
        f = day_grp['frequency_hz']
        daily_trend.append({
            'date': str(date),
            'min_hz': round(float(f.min()), 3),
            'max_hz': round(float(f.max()), 3),
            'avg_hz': round(float(f.mean()), 3),
        })

    return {
        'data_available': True,
        'avg_frequency': round(float(freq.mean()), 3),
        'min_frequency': round(float(freq.min()), 3),
        'max_frequency': round(float(freq.max()), 3),
        'excursion_count': int(len(excursions)),
        'excursion_pct': round(float(len(excursions) / len(freq) * 100), 2),
        'total_readings': int(len(freq)),
        'band_low': band_low,
        'band_high': band_high,
        'daily_trend': daily_trend,
    }


def analyze_neutral_current(
    conn, site_id: str, start_date: str, end_date: str,
    thresholds: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Neutral current analysis.

    Returns data_available=False if no neutral_current_a data exists.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    df = _fetch_readings_df(conn, site_id, start_date, end_date,
                            ['meter_id', 'meter_name', 'timestamp',
                             'neutral_current_a', 'current_a'])

    neutral = df['neutral_current_a'].dropna()
    if neutral.empty:
        return {
            'data_available': False,
            'message': 'Neutral current data not yet available. Will populate after next ingestion cycle with expanded field capture.',
        }

    # Per-meter stats
    meters = []
    for (mid, mname), grp in df.groupby(['meter_id', 'meter_name']):
        nc = grp['neutral_current_a'].dropna()
        if nc.empty:
            continue
        avg_phase = grp['current_a'].dropna().mean()
        elevated_threshold = avg_phase * thresholds.get('neutral_current_elevated_pct', 20) / 100
        elevated_count = int((nc > elevated_threshold).sum()) if avg_phase > 0 else 0

        meters.append({
            'meter_id': int(mid),
            'meter_name': mname,
            'avg_neutral_a': round(float(nc.mean()), 2),
            'max_neutral_a': round(float(nc.max()), 2),
            'elevated_count': elevated_count,
            'reading_count': int(len(nc)),
        })

    # Daily trend
    df_valid = df.dropna(subset=['neutral_current_a']).copy()
    df_valid['date'] = pd.to_datetime(df_valid['timestamp']).dt.date
    daily_trend = []
    for date, day_grp in df_valid.groupby('date'):
        nc = day_grp['neutral_current_a']
        daily_trend.append({
            'date': str(date),
            'avg_a': round(float(nc.mean()), 2),
            'max_a': round(float(nc.max()), 2),
        })

    return {
        'data_available': True,
        'meters': meters,
        'daily_trend': daily_trend,
    }


def analyze_thd(
    conn, site_id: str, start_date: str, end_date: str,
    thresholds: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Current THD analysis.

    Note: Only current THD (API field 'D') is available from Eniscope.
    Voltage THD is not provided by the hardware.

    Returns data_available=False if no thd_current data exists.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    thd_limit = thresholds.get('thd_current_limit_pct', 5.0)

    df = _fetch_readings_df(conn, site_id, start_date, end_date,
                            ['meter_id', 'meter_name', 'timestamp', 'thd_current'])

    thd = df['thd_current'].dropna()
    if thd.empty:
        return {
            'data_available': False,
            'message': 'Current THD data not yet available. Will populate after next ingestion cycle with expanded field capture.',
        }

    # Per-meter stats
    meters = []
    for (mid, mname), grp in df.groupby(['meter_id', 'meter_name']):
        t = grp['thd_current'].dropna()
        if t.empty:
            continue
        above_limit = int((t > thd_limit).sum())
        meters.append({
            'meter_id': int(mid),
            'meter_name': mname,
            'avg_thd': round(float(t.mean()), 2),
            'max_thd': round(float(t.max()), 2),
            'above_limit_count': above_limit,
            'reading_count': int(len(t)),
        })

    # Daily trend
    df_valid = df.dropna(subset=['thd_current']).copy()
    df_valid['date'] = pd.to_datetime(df_valid['timestamp']).dt.date
    daily_trend = []
    for date, day_grp in df_valid.groupby('date'):
        t = day_grp['thd_current']
        daily_trend.append({
            'date': str(date),
            'avg_thd': round(float(t.mean()), 2),
            'max_thd': round(float(t.max()), 2),
        })

    return {
        'data_available': True,
        'thd_limit_pct': thd_limit,
        'meters': meters,
        'daily_trend': daily_trend,
    }


def compute_health_score(
    voltage: Dict, current: Dict, frequency: Dict, thd: Dict,
    thresholds: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Compute overall electrical health score.

    Scoring rubric:
      Voltage: pct_outside_band < 2% = Good, < 10% = Fair, else Poor
      Current: peak/avg ratio < 3x = Good, < 5x = Fair, else Poor
      Frequency: excursion_count < 5 = Good, < 20 = Fair, else Poor
      THD: avg current THD < 5% = Good, < 8% = Fair, else Poor
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    weights = thresholds.get('health_score_weights', DEFAULT_THRESHOLDS['health_score_weights'])
    findings = []

    # --- Voltage score ---
    voltage_score = 100
    if voltage.get('meters'):
        avg_outside = np.mean([m['pct_outside_band'] for m in voltage['meters']])
        if avg_outside >= 10:
            voltage_score = 30
            findings.append(f"Voltage outside +/-5% band {avg_outside:.1f}% of the time (Poor)")
        elif avg_outside >= 2:
            voltage_score = 65
            findings.append(f"Voltage outside +/-5% band {avg_outside:.1f}% of the time (Fair)")
        else:
            findings.append(f"Voltage stability excellent ({avg_outside:.1f}% outside band)")

    # --- Current score ---
    current_score = 100
    if current.get('meters'):
        ratios = []
        for m in current['meters']:
            if m['avg_current_a'] > 0:
                ratios.append(m['peak_current_a'] / m['avg_current_a'])
        if ratios:
            avg_ratio = np.mean(ratios)
            if avg_ratio >= 5:
                current_score = 30
                findings.append(f"Peak/avg current ratio {avg_ratio:.1f}x (Poor - high demand spikes)")
            elif avg_ratio >= 3:
                current_score = 65
                findings.append(f"Peak/avg current ratio {avg_ratio:.1f}x (Fair - moderate demand spikes)")
            else:
                findings.append(f"Current demand profile healthy (peak/avg ratio {avg_ratio:.1f}x)")

    # --- Frequency score ---
    freq_score = 100
    if frequency.get('data_available'):
        exc_count = frequency.get('excursion_count', 0)
        if exc_count >= 20:
            freq_score = 30
            findings.append(f"{exc_count} frequency excursions detected (Poor)")
        elif exc_count >= 5:
            freq_score = 65
            findings.append(f"{exc_count} frequency excursions detected (Fair)")
        else:
            findings.append(f"Frequency stable ({exc_count} excursions)")
    else:
        freq_score = None  # Not scored

    # --- THD score ---
    thd_score = 100
    if thd.get('data_available') and thd.get('meters'):
        avg_thd = np.mean([m['avg_thd'] for m in thd['meters']])
        if avg_thd >= 8:
            thd_score = 30
            findings.append(f"Average current THD {avg_thd:.1f}% (Poor - exceeds IEEE 519)")
        elif avg_thd >= 5:
            thd_score = 65
            findings.append(f"Average current THD {avg_thd:.1f}% (Fair - near IEEE 519 limit)")
        else:
            findings.append(f"Current THD healthy ({avg_thd:.1f}%)")
    else:
        thd_score = None  # Not scored

    # Compute weighted average (skip components without data)
    scored = {}
    if voltage_score is not None:
        scored['voltage'] = voltage_score
    if current_score is not None:
        scored['current'] = current_score
    if freq_score is not None:
        scored['frequency'] = freq_score
    if thd_score is not None:
        scored['thd'] = thd_score

    if scored:
        total_weight = sum(weights.get(k, 0) for k in scored)
        if total_weight > 0:
            numeric = sum(scored[k] * weights.get(k, 0) for k in scored) / total_weight
        else:
            numeric = 100
    else:
        numeric = 100

    numeric = round(numeric)

    if numeric >= 80:
        grade = 'Good'
    elif numeric >= 50:
        grade = 'Fair'
    else:
        grade = 'Poor'

    return {
        'score': grade,
        'score_numeric': numeric,
        'component_scores': scored,
        'findings': findings,
    }


def generate_electrical_health_data(
    conn, site_id: str, start_date: str, end_date: str,
    nominal_voltage: Optional[int] = None,
    thresholds: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Main entry point: run all analyses and return combined data dict.

    This is the orchestrator called by the Deliver stage.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    logger.info("Generating electrical health data for site %s (%s to %s)",
                site_id, start_date, end_date)

    voltage = analyze_voltage_stability(conn, site_id, start_date, end_date,
                                        nominal_voltage, thresholds)
    current = analyze_current_peaks(conn, site_id, start_date, end_date)
    frequency = analyze_frequency_excursions(conn, site_id, start_date, end_date, thresholds)
    neutral = analyze_neutral_current(conn, site_id, start_date, end_date, thresholds)
    thd = analyze_thd(conn, site_id, start_date, end_date, thresholds)
    health = compute_health_score(voltage, current, frequency, thd, thresholds)

    return {
        'site_id': site_id,
        'start_date': start_date,
        'end_date': end_date,
        'generated_at': datetime.now().isoformat(),
        'health_score': health,
        'voltage_stability': voltage,
        'current_peaks': current,
        'frequency_excursions': frequency,
        'neutral_current': neutral,
        'thd_analysis': thd,
    }
