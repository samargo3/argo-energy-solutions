#!/usr/bin/env python3
"""
Argo Energy — Unified FastAPI Server

Replaces both the Express api-server.js and the original single-endpoint
FastAPI server.  All data now flows through PostgreSQL (Neon).

Endpoints:
    /health                                     — health check (public)
    /api/auth/login                             — password gate
    /api/energy/history                         — hourly-aggregated site energy
    /api/channels                               — list channels
    /api/channels/{id}/readings                 — raw readings
    /api/channels/{id}/readings/aggregated      — aggregated readings
    /api/channels/{id}/statistics               — statistics
    /api/channels/{id}/readings/latest          — latest reading
    /api/channels/{id}/range                    — data availability range
    /api/organizations/{id}/summary             — org-level summary
    /api/analytics/forecast/{site_id}           — Prophet usage forecast
    /api/analytics/cost-optimization/{site_id}  — TOU + demand analysis
    /api/eniscope/readings/{channelId}          — Eniscope API proxy
    /api/eniscope/channels                      — Eniscope API proxy
    /api/eniscope/devices                       — Eniscope API proxy
    /api/reports/weekly/{site_id}/latest         — latest weekly brief JSON
    /api/reports/weekly/{site_id}                — list available weekly reports
    /api/reports/weekly/{site_id}/{filename}     — specific report by filename
    /api/reports/data-quality/{site_id}          — live data quality summary

Usage:
    uvicorn backend.server.main:app --reload --port 8000
    npm run py:api
"""

import asyncio
import glob as globmod
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from base64 import b64encode
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set – check your .env file")

API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

# Eniscope API credentials
ENISCOPE_API_URL = (
    os.getenv("ENISCOPE_API_URL")
    or os.getenv("VITE_ENISCOPE_API_URL")
    or "https://core.eniscope.com"
).rstrip("/")
ENISCOPE_API_KEY = os.getenv("ENISCOPE_API_KEY") or os.getenv("VITE_ENISCOPE_API_KEY") or ""
ENISCOPE_EMAIL = os.getenv("ENISCOPE_EMAIL") or os.getenv("VITE_ENISCOPE_EMAIL") or ""
ENISCOPE_PASSWORD = os.getenv("ENISCOPE_PASSWORD") or os.getenv("VITE_ENISCOPE_PASSWORD") or ""

# CORS — add your Render production domain here
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",  # Vite preview
]
_extra_origin = os.getenv("CORS_ORIGIN")
if _extra_origin:
    ALLOWED_ORIGINS.append(_extra_origin)

MAX_ROWS = 5_000
logger = logging.getLogger("argo.api")

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
# Simple token store (in-memory; fine for single-process deployment)
_valid_tokens: Dict[str, float] = {}   # token → expiry timestamp
TOKEN_TTL = 60 * 60 * 24  # 24 hours


class LoginRequest(BaseModel):
    password: str


def _create_token() -> str:
    token = secrets.token_urlsafe(32)
    _valid_tokens[token] = time.time() + TOKEN_TTL
    return token


def _verify_token(token: str) -> bool:
    expiry = _valid_tokens.get(token)
    if expiry is None:
        return False
    if time.time() > expiry:
        _valid_tokens.pop(token, None)
        return False
    return True


# Paths that don't require auth
_PUBLIC_PATHS = {"/", "/health", "/api/auth/login", "/docs", "/openapi.json", "/redoc"}


async def require_auth(request: Request):
    """Check Bearer token or X-API-Key on all /api/* routes."""
    path = request.url.path

    # Public endpoints
    if path in _PUBLIC_PATHS:
        return

    # X-API-Key header (for pipeline / server-to-server)
    api_key = request.headers.get("x-api-key")
    if API_SECRET_KEY and api_key == API_SECRET_KEY:
        return

    # Bearer token (for frontend after login)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if _verify_token(token):
            return

    # No APP_PASSWORD set → development mode, allow everything
    if not APP_PASSWORD:
        return

    raise HTTPException(status_code=401, detail="Unauthorized")


# ---------------------------------------------------------------------------
# Eniscope proxy
# ---------------------------------------------------------------------------
class EniscopeProxy:
    """Port of the Node.js EniscopeProxy class — session token auth + retries."""

    def __init__(self) -> None:
        self.session_token: Optional[str] = None
        self.api_key = ENISCOPE_API_KEY
        self.email = ENISCOPE_EMAIL
        self.password_md5 = hashlib.md5(ENISCOPE_PASSWORD.encode()).hexdigest()
        self.base_url = ENISCOPE_API_URL
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def authenticate(self) -> Optional[str]:
        auth_string = f"{self.email}:{self.password_md5}"
        auth_b64 = b64encode(auth_string.encode()).decode()

        client = await self._get_client()
        resp = await client.get(
            f"{self.base_url}/v1/1/organizations",
            headers={
                "Authorization": f"Basic {auth_b64}",
                "X-Eniscope-API": self.api_key,
                "Accept": "text/json",
            },
        )
        resp.raise_for_status()
        self.session_token = (
            resp.headers.get("x-eniscope-token")
            or resp.headers.get("X-Eniscope-Token")
        )
        return self.session_token

    async def make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None, retries: int = 3
    ) -> Any:
        headers: Dict[str, str] = {
            "X-Eniscope-API": self.api_key,
            "Accept": "text/json",
        }

        if not self.session_token:
            await self.authenticate()

        if self.session_token:
            headers["X-Eniscope-Token"] = self.session_token
        else:
            auth_string = f"{self.email}:{self.password_md5}"
            auth_b64 = b64encode(auth_string.encode()).decode()
            headers["Authorization"] = f"Basic {auth_b64}"

        client = await self._get_client()

        for attempt in range(retries):
            try:
                resp = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    params=params or {},
                )
                resp.raise_for_status()

                # Update session token if returned
                token = (
                    resp.headers.get("x-eniscope-token")
                    or resp.headers.get("X-Eniscope-Token")
                )
                if token:
                    self.session_token = token

                return resp.json()

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status in (401, 419):
                    self.session_token = None
                    await self.authenticate()
                    if self.session_token:
                        headers["X-Eniscope-Token"] = self.session_token
                    if attempt < retries - 1:
                        continue
                if status == 429 and attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        return None  # should not reach here


eniscope_proxy = EniscopeProxy()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Argo Energy API",
    version="0.2.0",
    description="Unified API — data, Eniscope proxy, and auth for the React dashboard.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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


@contextmanager
def get_connection():
    """Yield a raw psycopg2 connection (for analytics modules)."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def _serialize_row(row: Dict) -> Dict:
    """Convert datetime / Decimal objects to JSON-safe types."""
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif v is None:
            out[k] = None
        else:
            try:
                out[k] = round(float(v), 4)
            except (TypeError, ValueError):
                out[k] = str(v)
    return out


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "service": "Argo Energy API", "version": "0.2.0"}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.post("/api/auth/login")
def login(body: LoginRequest):
    """Validate the shared APP_PASSWORD and return a bearer token."""
    if not APP_PASSWORD:
        # Dev mode — no password required, issue token anyway
        return {"token": _create_token()}

    if not hmac.compare_digest(body.password, APP_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"token": _create_token()}


# ---------------------------------------------------------------------------
# Data routes (PostgreSQL — all queries go through Layer 3 Business Views)
#
# Argo Governance: The API server is part of Stage 4 (Deliver).  It must
# consume data from the governed view layer, never from raw tables.
# ---------------------------------------------------------------------------
@app.get("/api/energy/history", dependencies=[Depends(require_auth)])
def energy_history(
    start_date: Optional[str] = Query("2025-11-05", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query("2026-02-05", description="End date (YYYY-MM-DD)"),
):
    """Hourly-aggregated energy data for the entire site.

    Source: ``v_readings_enriched`` (Layer 3 Business View).
    """
    try:
        with get_cursor() as cur:
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


@app.get("/api/channels", dependencies=[Depends(require_auth)])
def get_channels(organizationId: Optional[int] = None):
    """List channels, optionally filtered by organization.

    Source: ``v_meters`` (Layer 3 Business View).
    """
    try:
        with get_cursor() as cur:
            if organizationId:
                cur.execute(
                    """
                    SELECT meter_id   AS channel_id,
                           meter_name AS channel_name,
                           channel_type,
                           device_id,
                           device_name,
                           site_id    AS organization_id,
                           site_name  AS organization_name
                    FROM v_meters
                    WHERE site_id = %s
                    ORDER BY meter_name
                    """,
                    (str(organizationId),),
                )
            else:
                cur.execute(
                    """
                    SELECT meter_id   AS channel_id,
                           meter_name AS channel_name,
                           channel_type,
                           device_id,
                           device_name,
                           site_id    AS organization_id,
                           site_name  AS organization_name
                    FROM v_meters
                    ORDER BY meter_name
                    """
                )
            return [_serialize_row(r) for r in cur.fetchall()]
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/channels/{channel_id}/readings", dependencies=[Depends(require_auth)])
def get_channel_readings(
    channel_id: int,
    startDate: str = Query(..., description="Start date YYYY-MM-DD"),
    endDate: str = Query(..., description="End date YYYY-MM-DD"),
    limit: Optional[int] = None,
):
    """Clean readings for a channel within a date range.

    Source: ``v_readings_enriched`` (Layer 3 Business View).
    """
    try:
        with get_cursor() as cur:
            sql = """
                SELECT timestamp, energy_kwh, power_kw,
                       voltage_v, current_a, power_factor
                FROM v_readings_enriched
                WHERE meter_id = %s
                  AND timestamp >= %s::date
                  AND timestamp <  (%s::date + INTERVAL '1 day')
                ORDER BY timestamp
            """
            params: list = [channel_id, startDate, endDate]
            if limit:
                sql += " LIMIT %s"
                params.append(limit)
            cur.execute(sql, params)
            return [_serialize_row(r) for r in cur.fetchall()]
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/channels/{channel_id}/readings/aggregated", dependencies=[Depends(require_auth)])
def get_aggregated_readings(
    channel_id: int,
    startDate: str = Query(...),
    endDate: str = Query(...),
    resolution: str = Query("hour", pattern="^(hour|day|week|month)$"),
):
    """Aggregated readings at the requested resolution.

    Source: ``v_readings_enriched`` (Layer 3 Business View).
    """
    trunc_map = {"hour": "hour", "day": "day", "week": "week", "month": "month"}
    trunc = trunc_map[resolution]
    try:
        with get_cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    date_trunc('{trunc}', timestamp) AS period,
                    %s AS channel_id,
                    COALESCE(SUM(energy_kwh), 0)  AS total_energy_kwh,
                    COALESCE(AVG(power_kw), 0)    AS average_power_kw,
                    COALESCE(MAX(power_kw), 0)    AS peak_power_kw,
                    COALESCE(MIN(power_kw), 0)    AS min_power_kw,
                    COALESCE(AVG(voltage_v), 0)   AS average_voltage_v,
                    COUNT(*)                       AS count
                FROM v_readings_enriched
                WHERE meter_id = %s
                  AND timestamp >= %s::date
                  AND timestamp <  (%s::date + INTERVAL '1 day')
                GROUP BY date_trunc('{trunc}', timestamp)
                ORDER BY period
                LIMIT %s
                """,
                (channel_id, channel_id, startDate, endDate, MAX_ROWS),
            )
            return [_serialize_row(r) for r in cur.fetchall()]
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/channels/{channel_id}/statistics", dependencies=[Depends(require_auth)])
def get_channel_statistics(
    channel_id: int,
    startDate: str = Query(...),
    endDate: str = Query(...),
):
    """Energy statistics for a channel in a date range.

    Source: ``v_readings_enriched`` (Layer 3 Business View).
    """
    try:
        with get_cursor() as cur:
            # Single query: stats + peak/min timestamps via window functions
            cur.execute(
                """
                WITH stats AS (
                    SELECT
                        COALESCE(SUM(energy_kwh), 0)  AS total_energy_kwh,
                        COALESCE(AVG(power_kw), 0)    AS average_power_kw,
                        COALESCE(MAX(power_kw), 0)    AS peak_power_kw,
                        COALESCE(MIN(power_kw), 0)    AS min_power_kw,
                        COALESCE(AVG(voltage_v), 0)   AS average_voltage_v,
                        COUNT(*)                       AS count
                    FROM v_readings_enriched
                    WHERE meter_id = %s
                      AND timestamp >= %s::date
                      AND timestamp <  (%s::date + INTERVAL '1 day')
                ),
                peak AS (
                    SELECT timestamp AS peak_timestamp
                    FROM v_readings_enriched
                    WHERE meter_id = %s
                      AND timestamp >= %s::date
                      AND timestamp <  (%s::date + INTERVAL '1 day')
                    ORDER BY power_kw DESC NULLS LAST
                    LIMIT 1
                ),
                trough AS (
                    SELECT timestamp AS min_timestamp
                    FROM v_readings_enriched
                    WHERE meter_id = %s
                      AND timestamp >= %s::date
                      AND timestamp <  (%s::date + INTERVAL '1 day')
                    ORDER BY power_kw ASC NULLS LAST
                    LIMIT 1
                )
                SELECT s.*, p.peak_timestamp, t.min_timestamp
                FROM stats s
                LEFT JOIN peak p ON true
                LEFT JOIN trough t ON true
                """,
                (
                    channel_id, startDate, endDate,
                    channel_id, startDate, endDate,
                    channel_id, startDate, endDate,
                ),
            )
            row = cur.fetchone()
            if not row:
                return {}

            result = _serialize_row(row)
            result["peak_timestamp"] = row["peak_timestamp"].isoformat() if row.get("peak_timestamp") else None
            result["min_timestamp"] = row["min_timestamp"].isoformat() if row.get("min_timestamp") else None
            return result
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/channels/{channel_id}/readings/latest", dependencies=[Depends(require_auth)])
def get_latest_reading(channel_id: int):
    """Most recent reading for a channel.

    Source: ``v_latest_readings`` (Layer 3 Business View).
    """
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT timestamp, energy_kwh, power_kw,
                       voltage_v, current_a, power_factor
                FROM v_latest_readings
                WHERE meter_id = %s
                """,
                (channel_id,),
            )
            row = cur.fetchone()
            return _serialize_row(row) if row else None
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/channels/{channel_id}/range", dependencies=[Depends(require_auth)])
def get_channel_range(channel_id: int):
    """Data availability range (earliest / latest timestamp).

    Source: ``v_readings_enriched`` (Layer 3 Business View).
    """
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    MIN(timestamp) AS earliest,
                    MAX(timestamp) AS latest,
                    COUNT(*)       AS total_readings
                FROM v_readings_enriched
                WHERE meter_id = %s
                """,
                (channel_id,),
            )
            row = cur.fetchone()
            return _serialize_row(row) if row else {}
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/organizations/{organization_id}/summary", dependencies=[Depends(require_auth)])
def get_organization_summary(
    organization_id: int,
    startDate: str = Query(...),
    endDate: str = Query(...),
):
    """Organization-level energy summary.

    Source: ``v_readings_enriched`` (Layer 3 Business View).
    """
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(DISTINCT meter_id)          AS channels,
                    COALESCE(SUM(energy_kwh), 0)      AS total_energy_kwh,
                    COALESCE(AVG(power_kw), 0)        AS average_power_kw,
                    COALESCE(MAX(power_kw), 0)        AS peak_power_kw,
                    COUNT(*)                           AS total_readings
                FROM v_readings_enriched
                WHERE site_id = %s
                  AND timestamp >= %s::date
                  AND timestamp <  (%s::date + INTERVAL '1 day')
                """,
                (str(organization_id), startDate, endDate),
            )
            row = cur.fetchone()
            return _serialize_row(row) if row else {}
    except psycopg2.Error as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Analytics routes
# ---------------------------------------------------------------------------
@app.get("/api/analytics/forecast/{site_id}", dependencies=[Depends(require_auth)])
def analytics_forecast(
    site_id: int,
    horizon: int = Query(7, description="Forecast horizon in days (7 or 30)"),
    lookback: int = Query(90, description="Days of history to train on"),
):
    """Generate a Prophet-based energy usage forecast for a site."""
    if horizon not in (7, 30):
        raise HTTPException(status_code=400, detail="horizon must be 7 or 30")

    from analyze.forecast import generate_forecast

    try:
        with get_connection() as conn:
            result = generate_forecast(
                conn,
                site_id=site_id,
                horizon_days=horizon,
                lookback_days=lookback,
            )
        return result
    except Exception as exc:
        logger.error("Forecast error for site %s: %s", site_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/analytics/cost-optimization/{site_id}", dependencies=[Depends(require_auth)])
def analytics_cost_optimization(
    site_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    flat_rate: float = Query(0.12, description="Current flat rate $/kWh"),
):
    """Full cost optimization report: TOU analysis + demand charge analysis."""
    from analyze.cost_model import generate_cost_optimization_report

    try:
        with get_connection() as conn:
            result = generate_cost_optimization_report(
                conn,
                site_id=site_id,
                days=days,
                flat_rate=flat_rate,
            )
        return result
    except Exception as exc:
        logger.error("Cost optimization error for site %s: %s", site_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/analytics/tou/{site_id}", dependencies=[Depends(require_auth)])
def analytics_tou(
    site_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    flat_rate: float = Query(0.12, description="Current flat rate $/kWh"),
):
    """Time-of-Use rate analysis only."""
    from analyze.cost_model import analyze_tou_costs

    try:
        with get_connection() as conn:
            result = analyze_tou_costs(
                conn,
                site_id=site_id,
                days=days,
                flat_rate=flat_rate,
            )
        return result
    except Exception as exc:
        logger.error("TOU analysis error for site %s: %s", site_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/analytics/demand/{site_id}", dependencies=[Depends(require_auth)])
def analytics_demand(
    site_id: int,
    days: int = Query(30, description="Number of days to analyze"),
):
    """Peak demand charge analysis only."""
    from analyze.cost_model import analyze_demand_charges

    try:
        with get_connection() as conn:
            result = analyze_demand_charges(
                conn,
                site_id=site_id,
                days=days,
            )
        return result
    except Exception as exc:
        logger.error("Demand analysis error for site %s: %s", site_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Eniscope API proxy routes
# ---------------------------------------------------------------------------
@app.get("/api/eniscope/readings/{channel_id}", dependencies=[Depends(require_auth)])
async def eniscope_readings(
    channel_id: str,
    request: Request,
):
    """Proxy Eniscope readings API."""
    query = dict(request.query_params)

    params: Dict[str, Any] = {
        "res": query.get("res", "3600"),
        "action": query.get("action", "summarize"),
        "showCounters": query.get("showCounters", "0"),
    }

    # Handle fields
    fields = query.get("fields") or query.get("fields[]")
    if fields:
        fields_list = fields if isinstance(fields, list) else [fields]
        params["fields[]"] = fields_list
    else:
        params["fields[]"] = ["E", "P", "V", "I", "PF"]

    # Handle daterange
    daterange = query.get("daterange") or query.get("daterange[]")
    if daterange:
        if isinstance(daterange, list):
            params["daterange[]"] = daterange
        else:
            params["daterange"] = daterange

    try:
        data = await eniscope_proxy.make_request(
            f"/v1/1/readings/{channel_id}", params
        )
        # Normalize response
        if isinstance(data, dict):
            return data.get("records") or data.get("data") or data.get("result") or data
        return data
    except Exception as exc:
        logger.error("Eniscope readings proxy error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/eniscope/channels", dependencies=[Depends(require_auth)])
async def eniscope_channels(
    organization: Optional[str] = None,
    deviceId: Optional[str] = None,
    name: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
):
    """Proxy Eniscope channels API."""
    params: Dict[str, Any] = {}
    if organization:
        params["organization"] = organization
    if deviceId:
        params["deviceId"] = deviceId
    if name:
        params["name"] = name
    if page:
        params["page"] = page
    if limit:
        params["limit"] = limit

    try:
        return await eniscope_proxy.make_request("/v1/1/channels", params)
    except Exception as exc:
        logger.error("Eniscope channels proxy error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/eniscope/devices", dependencies=[Depends(require_auth)])
async def eniscope_devices(
    organization: Optional[str] = None,
    uuid: Optional[str] = None,
    deviceType: Optional[str] = None,
    name: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None,
):
    """Proxy Eniscope devices API."""
    params: Dict[str, Any] = {}
    if organization:
        params["organization"] = organization
    if uuid:
        params["uuid"] = uuid
    if deviceType:
        params["deviceType"] = deviceType
    if name:
        params["name"] = name
    if page:
        params["page"] = page
    if limit:
        params["limit"] = limit

    try:
        return await eniscope_proxy.make_request("/v1/1/devices", params)
    except Exception as exc:
        logger.error("Eniscope devices proxy error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Reports endpoints
# ---------------------------------------------------------------------------
_REPORTS_DIR = _PROJECT_ROOT / "reports"


def _find_reports(site_id: str, pattern: str) -> List[Path]:
    """Find report files matching a site and glob pattern, newest first."""
    matches = sorted(
        _REPORTS_DIR.glob(f"{pattern}-{site_id}-*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches


@app.get("/api/reports/weekly/{site_id}/latest", dependencies=[Depends(require_auth)])
async def get_latest_weekly_report(site_id: str):
    """Return the most recent weekly brief JSON for a site."""
    reports = _find_reports(site_id, "weekly-brief")
    if not reports:
        raise HTTPException(status_code=404, detail=f"No weekly reports found for site {site_id}")
    try:
        return json.loads(reports[0].read_text())
    except Exception as exc:
        logger.error("Error reading report %s: %s", reports[0], exc)
        raise HTTPException(status_code=500, detail="Failed to read report") from exc


@app.get("/api/reports/weekly/{site_id}", dependencies=[Depends(require_auth)])
async def list_weekly_reports(site_id: str, limit: int = Query(10, ge=1, le=100)):
    """List available weekly brief reports for a site."""
    reports = _find_reports(site_id, "weekly-brief")
    return [
        {
            "filename": r.name,
            "generated_at": datetime.fromtimestamp(r.stat().st_mtime).isoformat(),
            "size_kb": round(r.stat().st_size / 1024, 1),
        }
        for r in reports[:limit]
    ]


@app.get("/api/reports/weekly/{site_id}/{filename}", dependencies=[Depends(require_auth)])
async def get_weekly_report_by_name(site_id: str, filename: str):
    """Return a specific weekly report by filename."""
    # Prevent path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    report_path = _REPORTS_DIR / filename
    if not report_path.exists() or site_id not in filename:
        raise HTTPException(status_code=404, detail="Report not found")
    try:
        return json.loads(report_path.read_text())
    except Exception as exc:
        logger.error("Error reading report %s: %s", report_path, exc)
        raise HTTPException(status_code=500, detail="Failed to read report") from exc


@app.get("/api/reports/data-quality/{site_id}", dependencies=[Depends(require_auth)])
async def get_data_quality_summary(site_id: str):
    """Return current data quality metrics for a site."""
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Channel completeness for last 7 days
        cur.execute("""
            WITH active_channels AS (
                SELECT r.channel_id, c.channel_name,
                       COUNT(*) as total_readings,
                       MAX(r.timestamp) as last_reading,
                       EXTRACT(EPOCH FROM (NOW() - MAX(r.timestamp))) / 3600 as hours_since_last
                FROM readings r
                JOIN channels c ON r.channel_id = c.channel_id
                WHERE c.organization_id = %s::int
                GROUP BY r.channel_id, c.channel_name
                HAVING COUNT(*) >= 100
            ),
            recent AS (
                SELECT ac.channel_id, ac.channel_name,
                       ac.total_readings, ac.last_reading, ac.hours_since_last,
                       COUNT(r.timestamp) as readings_last_7d
                FROM active_channels ac
                LEFT JOIN readings r ON r.channel_id = ac.channel_id
                    AND r.timestamp > NOW() - INTERVAL '7 days'
                GROUP BY ac.channel_id, ac.channel_name,
                         ac.total_readings, ac.last_reading, ac.hours_since_last
            )
            SELECT *,
                   ROUND(readings_last_7d * 100.0 / NULLIF(7 * 24, 0), 1) as completeness_pct
            FROM recent
            ORDER BY completeness_pct ASC
        """, (site_id,))
        channels = cur.fetchall()

        avg_completeness = (
            sum(ch["completeness_pct"] or 0 for ch in channels) / len(channels)
            if channels else 0
        )

        return {
            "site_id": site_id,
            "checked_at": datetime.utcnow().isoformat(),
            "active_channels": len(channels),
            "avg_completeness_pct": round(avg_completeness, 1),
            "channels": channels,
        }
