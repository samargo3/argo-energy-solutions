#!/usr/bin/env python3
"""
FastAPI Energy Data Server

Serves historical energy data from Neon (v_readings_enriched) to the React
frontend.  Aggregates by hour to keep payloads under 5 000 rows.

Usage:
    uvicorn backend.server.main:app --reload --port 8000
    npm run py:api

Requires: fastapi, uvicorn[standard], psycopg2-binary, python-dotenv
"""

import os
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set – check your .env file")

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")

MAX_ROWS = 5_000  # hard cap to protect the browser

# ---------------------------------------------------------------------------
# API Key Security
# ---------------------------------------------------------------------------
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: Optional[str] = Security(_api_key_header)):
    """Validate X-API-Key header. Warn-only when key is not configured."""
    if not API_SECRET_KEY:
        # Development mode — no key configured, allow all requests
        return api_key
    if not api_key or api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized — valid X-API-Key header required")
    return api_key

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Argo Energy API",
    version="0.1.0",
    description="Serves historical energy data for the React dashboard.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Database helper
# ---------------------------------------------------------------------------
@contextmanager
def get_cursor():
    """Yield a RealDictCursor, closing the connection when done."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            yield cur
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "service": "Argo Energy API"}


@app.get("/api/energy/history")
def energy_history(
    start_date: Optional[str] = Query("2025-11-05", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query("2026-02-05", description="End date (YYYY-MM-DD)"),
    _key: str = Depends(require_api_key),
):
    """
    Return hourly-aggregated energy data for the entire site.

    The raw ``readings`` table holds ~300 k 15-min rows.  To prevent
    crashing the browser we aggregate by hour and cap at 5 000 rows.

    Response shape::

        {
          "meta": { "start_date", "end_date", "rows", "aggregation" },
          "data": [ { "timestamp": "...", "energy_kwh": ..., "avg_power_kw": ... }, ... ]
        }
    """
    try:
        with get_cursor() as cur:
            # Hourly aggregation across all meters for the site
            cur.execute(
                """
                SELECT
                    date_trunc('hour', timestamp) AS timestamp,
                    SUM(energy_kwh)               AS energy_kwh,
                    AVG(power_kw)                 AS avg_power_kw
                FROM v_readings_enriched
                WHERE timestamp >= %s::date
                  AND timestamp <  (%s::date + INTERVAL '1 day')
                GROUP BY date_trunc('hour', timestamp)
                ORDER BY timestamp
                LIMIT %s
                """,
                (start_date, end_date, MAX_ROWS),
            )
            rows = cur.fetchall()

    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    # Serialise datetime → ISO-8601 string, round floats
    data = [
        {
            "timestamp": str(r["timestamp"]),
            "energy_kwh": round(float(r["energy_kwh"]), 3) if r["energy_kwh"] else 0,
            "avg_power_kw": round(float(r["avg_power_kw"]), 3) if r["avg_power_kw"] else 0,
        }
        for r in rows
    ]

    return {
        "meta": {
            "start_date": start_date,
            "end_date": end_date,
            "rows": len(data),
            "aggregation": "hourly",
        },
        "data": data,
    }
