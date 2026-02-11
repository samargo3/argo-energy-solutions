"""
Energy Usage Forecasting — Prophet-based time series prediction

Consumes hourly data from mv_hourly_usage or v_readings_hourly and produces
7-day and 30-day forecasts with confidence intervals.  Designed to run as a
standalone analysis or be called from the report pipeline.

Following Argo governance: Stage 3 (Analyze — Read-Only)

Usage:
    from analyze.forecast import generate_forecast
    result = generate_forecast(conn, site_id=23271, horizon_days=7)
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from prophet import Prophet

logger = logging.getLogger(__name__)


def _fetch_hourly_data(conn, site_id: int, lookback_days: int = 90) -> pd.DataFrame:
    """Fetch hourly energy data from the governed view layer for Prophet training.

    Queries ``v_readings_hourly`` (Layer 3 Business View) which sits on top
    of the materialized ``mv_hourly_usage`` and includes site context.
    This respects Argo governance: Analyze modules consume governed views,
    never raw tables.

    Returns a DataFrame with columns: ds (datetime), y (total kWh).
    """
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                hour                AS ds,
                SUM(total_kwh)      AS y
            FROM v_readings_hourly
            WHERE site_id = %s
              AND hour >= %s
            GROUP BY hour
            ORDER BY ds
            """,
            (str(site_id), cutoff),
        )
        rows = cur.fetchall()

    if not rows:
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.DataFrame(rows, columns=["ds", "y"])
    df["ds"] = pd.to_datetime(df["ds"], utc=True).dt.tz_localize(None)
    df["y"] = df["y"].astype(float)
    return df


def generate_forecast(
    conn,
    site_id: int,
    horizon_days: int = 7,
    lookback_days: int = 90,
    interval_width: float = 0.80,
) -> Dict[str, Any]:
    """Generate an energy usage forecast using Prophet.

    Args:
        conn: psycopg2 connection
        site_id: Eniscope organization_id
        horizon_days: How many days to forecast (7 or 30)
        lookback_days: Days of history to train on
        interval_width: Confidence interval width (0.80 = 80%)

    Returns:
        Dictionary with keys: forecast, summary, model_info
    """
    logger.info("Generating %d-day forecast for site %d (lookback=%d days)",
                horizon_days, site_id, lookback_days)

    df = _fetch_hourly_data(conn, site_id, lookback_days)

    if len(df) < 48:  # need at least 2 days of hourly data
        return {
            "forecast": [],
            "summary": {
                "error": "Insufficient data",
                "rows_available": len(df),
                "min_required": 48,
            },
            "model_info": None,
        }

    # ── Fit Prophet ──────────────────────────────────────────────
    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,  # not enough data for yearly yet
        interval_width=interval_width,
        changepoint_prior_scale=0.05,  # conservative trend changes
    )
    # Suppress Prophet's internal logging
    model.fit(df)

    # ── Predict ──────────────────────────────────────────────────
    future = model.make_future_dataframe(periods=horizon_days * 24, freq="h")
    prediction = model.predict(future)

    # Split into historical fit and future forecast
    last_actual = df["ds"].max()
    forecast_rows = prediction[prediction["ds"] > last_actual].copy()

    forecast_data = []
    for _, row in forecast_rows.iterrows():
        forecast_data.append({
            "timestamp": row["ds"].isoformat(),
            "predicted_kwh": round(max(float(row["yhat"]), 0), 3),
            "lower_bound": round(max(float(row["yhat_lower"]), 0), 3),
            "upper_bound": round(max(float(row["yhat_upper"]), 0), 3),
        })

    # ── Summary stats ────────────────────────────────────────────
    forecast_values = [r["predicted_kwh"] for r in forecast_data]
    actual_last_7d = df[df["ds"] > (last_actual - timedelta(days=7))]["y"]

    total_predicted = sum(forecast_values)
    total_recent = float(actual_last_7d.sum()) if len(actual_last_7d) > 0 else 0

    # Daily forecast aggregation
    daily_forecast = []
    for day_offset in range(horizon_days):
        day_start = day_offset * 24
        day_end = (day_offset + 1) * 24
        day_rows = forecast_data[day_start:day_end]
        if day_rows:
            day_total = sum(r["predicted_kwh"] for r in day_rows)
            day_peak = max(r["predicted_kwh"] for r in day_rows)
            daily_forecast.append({
                "date": day_rows[0]["timestamp"][:10],
                "predicted_kwh": round(day_total, 2),
                "peak_hour_kwh": round(day_peak, 3),
            })

    summary = {
        "site_id": site_id,
        "horizon_days": horizon_days,
        "lookback_days": lookback_days,
        "training_rows": len(df),
        "forecast_hours": len(forecast_data),
        "total_predicted_kwh": round(total_predicted, 2),
        "total_last_7d_actual_kwh": round(total_recent, 2),
        "daily_forecast": daily_forecast,
        "generated_at": datetime.utcnow().isoformat(),
    }

    # Trend direction
    if len(daily_forecast) >= 2:
        first_day = daily_forecast[0]["predicted_kwh"]
        last_day = daily_forecast[-1]["predicted_kwh"]
        if first_day > 0:
            change_pct = ((last_day - first_day) / first_day) * 100
            summary["trend_direction"] = "increasing" if change_pct > 2 else ("decreasing" if change_pct < -2 else "stable")
            summary["trend_change_pct"] = round(change_pct, 1)

    model_info = {
        "changepoints": len(model.changepoints),
        "interval_width": interval_width,
        "seasonalities": list(model.seasonalities.keys()),
    }

    logger.info("Forecast complete: %d hours, %.1f kWh total predicted",
                len(forecast_data), total_predicted)

    return {
        "forecast": forecast_data,
        "summary": summary,
        "model_info": model_info,
    }
