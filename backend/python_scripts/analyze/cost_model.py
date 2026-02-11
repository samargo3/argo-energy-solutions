"""
Energy Cost Optimization — TOU Rate Modeling & Peak Demand Analysis

Provides two capabilities:
  1. **TOU Rate Analysis** — Apply time-of-use tariff schedules to actual usage
     to model costs under different rate structures and identify savings from
     load-shifting.
  2. **Peak Demand Analysis** — Identify the billing-period demand peaks,
     quantify demand charges, and model savings from peak shaving.

Following Argo governance: Stage 3 (Analyze — Read-Only)

Usage:
    from analyze.cost_model import analyze_tou_costs, analyze_demand_charges
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Default Rate Structures
# ═══════════════════════════════════════════════════════════════════════

# Standard flat rate as a baseline
DEFAULT_FLAT_RATE = 0.12  # $/kWh

# US-style Time-of-Use schedule (modify in config/report_config.py)
DEFAULT_TOU_SCHEDULE = {
    "name": "Standard TOU",
    "periods": {
        "off_peak": {
            "rate": 0.06,       # $/kWh
            "weekday_hours": list(range(0, 7)) + list(range(21, 24)),  # 9pm-7am
            "weekend_hours": list(range(0, 24)),  # all day
        },
        "mid_peak": {
            "rate": 0.10,       # $/kWh
            "weekday_hours": list(range(7, 12)) + list(range(18, 21)),  # 7am-12pm, 6pm-9pm
            "weekend_hours": [],
        },
        "on_peak": {
            "rate": 0.20,       # $/kWh
            "weekday_hours": list(range(12, 18)),  # 12pm-6pm
            "weekend_hours": [],
        },
    },
}

# Demand charge tiers
DEFAULT_DEMAND_CONFIG = {
    "rate_per_kw": 12.00,          # $/kW per billing period
    "billing_period_days": 30,     # standard billing cycle
    "ratchet_pct": 0.80,           # 80% ratchet (common utility rule)
    "ratchet_months": 11,          # ratchet window
}


# ═══════════════════════════════════════════════════════════════════════
# Data Fetching
# ═══════════════════════════════════════════════════════════════════════

def _fetch_hourly_usage(conn, site_id: int, days: int = 30) -> pd.DataFrame:
    """Fetch hourly usage data for cost analysis from the governed view layer.

    Queries ``v_readings_hourly`` (Layer 3 Business View) which sits on top
    of the materialized ``mv_hourly_usage`` and includes site context.
    This respects Argo governance: Analyze modules consume governed views,
    never raw tables.

    Uses ``avg_kw`` as the demand proxy — at hourly resolution this
    represents the average demand during the billing interval, which is the
    standard method used by most utilities.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                hour,
                SUM(total_kwh)  AS total_kwh,
                SUM(avg_kw)     AS peak_kw
            FROM v_readings_hourly
            WHERE site_id = %s
              AND hour >= %s
            GROUP BY hour
            ORDER BY hour
            """,
            (str(site_id), cutoff),
        )
        rows = cur.fetchall()

    if not rows:
        return pd.DataFrame(columns=["hour", "total_kwh", "peak_kw"])

    df = pd.DataFrame(rows, columns=["hour", "total_kwh", "peak_kw"])
    df["hour"] = pd.to_datetime(df["hour"], utc=True)
    df["total_kwh"] = df["total_kwh"].astype(float)
    df["peak_kw"] = df["peak_kw"].astype(float).fillna(0)
    return df


# ═══════════════════════════════════════════════════════════════════════
# TOU Rate Analysis
# ═══════════════════════════════════════════════════════════════════════

def _classify_tou_period(ts: pd.Timestamp, schedule: Dict) -> Tuple[str, float]:
    """Classify a timestamp into a TOU period and return (period_name, rate)."""
    hour = ts.hour
    is_weekend = ts.weekday() >= 5

    for period_name, period_def in schedule["periods"].items():
        if is_weekend:
            if hour in period_def["weekend_hours"]:
                return period_name, period_def["rate"]
        else:
            if hour in period_def["weekday_hours"]:
                return period_name, period_def["rate"]

    # Fallback to off-peak if no match
    return "off_peak", schedule["periods"]["off_peak"]["rate"]


def analyze_tou_costs(
    conn,
    site_id: int,
    days: int = 30,
    flat_rate: float = DEFAULT_FLAT_RATE,
    tou_schedule: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Analyze energy costs under flat vs TOU rate structures.

    Args:
        conn: psycopg2 connection
        site_id: Eniscope organization_id
        days: Number of days to analyze
        flat_rate: Current flat rate ($/kWh) for comparison
        tou_schedule: TOU schedule dict (uses DEFAULT_TOU_SCHEDULE if None)

    Returns:
        Dict with cost breakdown, savings opportunities, and hourly detail.
    """
    if tou_schedule is None:
        tou_schedule = DEFAULT_TOU_SCHEDULE

    logger.info("Analyzing TOU costs for site %d (%d days, flat=%.3f)",
                site_id, days, flat_rate)

    df = _fetch_hourly_usage(conn, site_id, days)

    if df.empty:
        return {
            "error": "No usage data found",
            "site_id": site_id,
            "period_days": days,
        }

    # Classify each hour
    df["tou_period"], df["tou_rate"] = zip(
        *df["hour"].apply(lambda ts: _classify_tou_period(ts, tou_schedule))
    )
    df["flat_cost"] = df["total_kwh"] * flat_rate
    df["tou_cost"] = df["total_kwh"] * df["tou_rate"]

    total_kwh = float(df["total_kwh"].sum())
    flat_total = float(df["flat_cost"].sum())
    tou_total = float(df["tou_cost"].sum())

    # Breakdown by TOU period
    period_breakdown = {}
    for period_name in tou_schedule["periods"]:
        period_data = df[df["tou_period"] == period_name]
        period_kwh = float(period_data["total_kwh"].sum())
        period_cost = float(period_data["tou_cost"].sum())
        period_hours = len(period_data)
        period_breakdown[period_name] = {
            "kwh": round(period_kwh, 2),
            "cost": round(period_cost, 2),
            "hours": period_hours,
            "pct_of_total_kwh": round((period_kwh / total_kwh * 100) if total_kwh > 0 else 0, 1),
            "rate": tou_schedule["periods"][period_name]["rate"],
        }

    # Load-shifting opportunity: how much on-peak usage could move to off-peak?
    on_peak_kwh = period_breakdown.get("on_peak", {}).get("kwh", 0)
    on_peak_rate = tou_schedule["periods"]["on_peak"]["rate"]
    off_peak_rate = tou_schedule["periods"]["off_peak"]["rate"]
    shift_savings_per_kwh = on_peak_rate - off_peak_rate
    max_shift_savings = round(on_peak_kwh * shift_savings_per_kwh, 2)

    # Daily cost trend
    df["date"] = df["hour"].dt.date
    daily_costs = (
        df.groupby("date")
        .agg(kwh=("total_kwh", "sum"), flat_cost=("flat_cost", "sum"), tou_cost=("tou_cost", "sum"))
        .reset_index()
    )
    daily_detail = []
    for _, row in daily_costs.iterrows():
        daily_detail.append({
            "date": row["date"].isoformat(),
            "kwh": round(float(row["kwh"]), 2),
            "flat_cost": round(float(row["flat_cost"]), 2),
            "tou_cost": round(float(row["tou_cost"]), 2),
        })

    result = {
        "site_id": site_id,
        "period_days": days,
        "total_kwh": round(total_kwh, 2),
        "flat_rate": flat_rate,
        "flat_total_cost": round(flat_total, 2),
        "tou_schedule_name": tou_schedule["name"],
        "tou_total_cost": round(tou_total, 2),
        "tou_vs_flat_savings": round(flat_total - tou_total, 2),
        "tou_vs_flat_pct": round(((flat_total - tou_total) / flat_total * 100) if flat_total > 0 else 0, 1),
        "period_breakdown": period_breakdown,
        "load_shift_opportunity": {
            "on_peak_kwh": round(on_peak_kwh, 2),
            "potential_savings_per_kwh": round(shift_savings_per_kwh, 4),
            "max_monthly_savings": max_shift_savings,
            "description": (
                f"Shifting {round(on_peak_kwh, 0)} kWh from on-peak to off-peak "
                f"could save up to ${max_shift_savings}/period"
            ),
        },
        "daily_detail": daily_detail,
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info("TOU analysis complete: flat=$%.2f, TOU=$%.2f, delta=$%.2f",
                flat_total, tou_total, flat_total - tou_total)
    return result


# ═══════════════════════════════════════════════════════════════════════
# Peak Demand Charge Analysis
# ═══════════════════════════════════════════════════════════════════════

def analyze_demand_charges(
    conn,
    site_id: int,
    days: int = 30,
    demand_config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Analyze peak demand charges and identify shaving opportunities.

    Args:
        conn: psycopg2 connection
        site_id: Eniscope organization_id
        days: Number of days to analyze
        demand_config: Demand charge configuration (uses DEFAULT_DEMAND_CONFIG if None)

    Returns:
        Dict with peak demand events, charges, and optimization opportunities.
    """
    if demand_config is None:
        demand_config = DEFAULT_DEMAND_CONFIG

    rate_per_kw = demand_config["rate_per_kw"]

    logger.info("Analyzing demand charges for site %d (%d days, $%.2f/kW)",
                site_id, days, rate_per_kw)

    df = _fetch_hourly_usage(conn, site_id, days)

    if df.empty:
        return {
            "error": "No usage data found",
            "site_id": site_id,
            "period_days": days,
        }

    # ── Identify peak demand ─────────────────────────────────────
    peak_idx = df["peak_kw"].idxmax()
    peak_row = df.loc[peak_idx]
    peak_kw = float(peak_row["peak_kw"])
    peak_time = peak_row["hour"]

    # Top 10 demand peaks (distinct hours)
    top_peaks = (
        df.nlargest(10, "peak_kw")[["hour", "peak_kw"]]
        .reset_index(drop=True)
    )
    peak_events = []
    for _, row in top_peaks.iterrows():
        peak_events.append({
            "timestamp": row["hour"].isoformat(),
            "demand_kw": round(float(row["peak_kw"]), 2),
            "hour_of_day": row["hour"].hour,
            "day_of_week": row["hour"].strftime("%A"),
        })

    # ── Demand charge calculation ────────────────────────────────
    demand_charge = round(peak_kw * rate_per_kw, 2)

    # What if we could shave 5%, 10%, 15%, 20% off peak?
    shaving_scenarios = []
    for pct in [5, 10, 15, 20]:
        reduced_kw = peak_kw * (1 - pct / 100)
        reduced_charge = round(reduced_kw * rate_per_kw, 2)
        savings = round(demand_charge - reduced_charge, 2)
        annual_savings = round(savings * 12, 2)
        shaving_scenarios.append({
            "reduction_pct": pct,
            "reduced_peak_kw": round(reduced_kw, 2),
            "monthly_charge": reduced_charge,
            "monthly_savings": savings,
            "annual_savings": annual_savings,
        })

    # ── Load profile analysis ────────────────────────────────────
    df["hour_of_day"] = df["hour"].dt.hour
    df["is_weekday"] = df["hour"].dt.weekday < 5

    hourly_profile = (
        df.groupby("hour_of_day")
        .agg(avg_kw=("peak_kw", "mean"), max_kw=("peak_kw", "max"), avg_kwh=("total_kwh", "mean"))
        .reset_index()
    )
    load_profile = []
    for _, row in hourly_profile.iterrows():
        load_profile.append({
            "hour": int(row["hour_of_day"]),
            "avg_kw": round(float(row["avg_kw"]), 2),
            "max_kw": round(float(row["max_kw"]), 2),
            "avg_kwh": round(float(row["avg_kwh"]), 3),
        })

    # Weekday vs weekend comparison
    weekday_peak = float(df[df["is_weekday"]]["peak_kw"].max()) if df["is_weekday"].any() else 0
    weekend_peak = float(df[~df["is_weekday"]]["peak_kw"].max()) if (~df["is_weekday"]).any() else 0

    # ── Timing analysis — when do peaks happen? ──────────────────
    peak_hour_counts = df.nlargest(50, "peak_kw")["hour_of_day"].value_counts()
    peak_concentration_hours = peak_hour_counts.head(3).index.tolist()

    result = {
        "site_id": site_id,
        "period_days": days,
        "billing_peak_kw": round(peak_kw, 2),
        "peak_timestamp": peak_time.isoformat(),
        "demand_rate_per_kw": rate_per_kw,
        "monthly_demand_charge": demand_charge,
        "annual_demand_charge": round(demand_charge * 12, 2),
        "top_peak_events": peak_events,
        "shaving_scenarios": shaving_scenarios,
        "load_profile": load_profile,
        "weekday_peak_kw": round(weekday_peak, 2),
        "weekend_peak_kw": round(weekend_peak, 2),
        "peak_concentration_hours": peak_concentration_hours,
        "recommendations": _generate_demand_recommendations(
            peak_kw, weekday_peak, weekend_peak,
            peak_concentration_hours, demand_charge,
        ),
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info("Demand analysis complete: peak=%.1f kW, charge=$%.2f/mo",
                peak_kw, demand_charge)
    return result


def _generate_demand_recommendations(
    peak_kw: float,
    weekday_peak: float,
    weekend_peak: float,
    peak_hours: List[int],
    monthly_charge: float,
) -> List[Dict[str, str]]:
    """Generate actionable recommendations for demand charge reduction."""
    recs = []

    # If weekday peak >> weekend, there's shifting potential
    if weekday_peak > 0 and weekend_peak > 0:
        ratio = weekday_peak / weekend_peak
        if ratio > 2.0:
            recs.append({
                "priority": "high",
                "category": "load_shifting",
                "title": "Shift non-critical weekday loads",
                "detail": (
                    f"Weekday peak ({weekday_peak:.0f} kW) is {ratio:.1f}x higher "
                    f"than weekend ({weekend_peak:.0f} kW). Consider shifting batch "
                    f"processes, HVAC pre-cooling, or EV charging to off-peak hours."
                ),
            })

    # Peak concentration means targeted intervention is possible
    if peak_hours:
        hour_str = ", ".join(f"{h}:00" for h in sorted(peak_hours))
        recs.append({
            "priority": "high",
            "category": "peak_shaving",
            "title": "Target peak concentration hours",
            "detail": (
                f"Demand peaks concentrate around {hour_str}. "
                f"Stagger equipment startup or use demand-limiting controls "
                f"during these hours to reduce the billing peak."
            ),
        })

    # If peak is high enough to warrant battery/DER consideration
    if monthly_charge > 500:
        ten_pct_savings = round(monthly_charge * 0.10, 2)
        recs.append({
            "priority": "medium",
            "category": "investment",
            "title": "Evaluate battery energy storage",
            "detail": (
                f"At ${monthly_charge:.0f}/month in demand charges, "
                f"even a 10% reduction saves ~${ten_pct_savings}/month "
                f"(${ten_pct_savings * 12:.0f}/year). Battery storage or "
                f"demand response programs may have attractive payback periods."
            ),
        })

    if not recs:
        recs.append({
            "priority": "low",
            "category": "monitoring",
            "title": "Continue monitoring demand patterns",
            "detail": (
                f"Current peak of {peak_kw:.0f} kW. "
                f"No immediate high-impact optimization identified. "
                f"Continue monitoring for pattern changes."
            ),
        })

    return recs


# ═══════════════════════════════════════════════════════════════════════
# Combined Cost Optimization Report
# ═══════════════════════════════════════════════════════════════════════

def generate_cost_optimization_report(
    conn,
    site_id: int,
    days: int = 30,
    flat_rate: float = DEFAULT_FLAT_RATE,
    tou_schedule: Optional[Dict] = None,
    demand_config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Generate a combined cost optimization report.

    This is the high-level entry point that combines TOU analysis and
    demand charge analysis into a single report.
    """
    logger.info("Generating full cost optimization report for site %d", site_id)

    tou_result = analyze_tou_costs(conn, site_id, days, flat_rate, tou_schedule)
    demand_result = analyze_demand_charges(conn, site_id, days, demand_config)

    # Calculate combined potential savings
    tou_savings = tou_result.get("tou_vs_flat_savings", 0)
    demand_10pct = next(
        (s["monthly_savings"] for s in demand_result.get("shaving_scenarios", [])
         if s["reduction_pct"] == 10),
        0,
    )

    total_monthly_savings = round(
        max(tou_savings, 0) + demand_10pct, 2
    )

    return {
        "site_id": site_id,
        "period_days": days,
        "tou_analysis": tou_result,
        "demand_analysis": demand_result,
        "combined_summary": {
            "total_energy_kwh": tou_result.get("total_kwh", 0),
            "current_flat_cost": tou_result.get("flat_total_cost", 0),
            "tou_optimized_cost": tou_result.get("tou_total_cost", 0),
            "demand_charge": demand_result.get("monthly_demand_charge", 0),
            "estimated_monthly_savings_potential": total_monthly_savings,
            "estimated_annual_savings_potential": round(total_monthly_savings * 12, 2),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }
