"""Shared paths and helpers for the v2 pipeline. All money math lives in SQL as ratio of sums."""
from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("ROYALE_DATA", ROOT.parents[1] / "dashboard-royale" / "data"))
OUT = ROOT / "site" / "data"
OUT.mkdir(parents=True, exist_ok=True)
RESULTS = ROOT / "analysis" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def t(rel: str) -> str:
    """Quoted parquet path for a table, e.g. t('2_machine_decision/machine_day')."""
    return f"'{(DATA / rel).as_posix()}.parquet'"


MD = t("2_machine_decision/machine_day")
PV = t("1_prepared_views/prepared_daily_view")
PD = t("1_prepared_views/property_day")
PP = t("1_prepared_views/player_period")
GM = t("2_machine_decision/game_math")
CAL = t("2_machine_decision/calendar_day")
LOC = t("2_machine_decision/floor_locations")
WALK = t("2_machine_decision/floor_walkways")
PLC = t("2_machine_decision/placements")
OPS = t("2_machine_decision/operations")
MACH = t("2_machine_decision/machines")
ACT = t("2_machine_decision/action_catalog")
SES = t("3_guests/sessions")
LED = t("3_guests/loyalty_ledger")
EVT = t("4_context/events")
TRAF = t("4_context/zone_traffic_hourly")
CITY = t("4_context/real_sources/city_visitation_monthly")
ROSTER = t("5_optional/shift_roster")


def con() -> duckdb.DuckDBPyConnection:
    c = duckdb.connect()
    c.execute("SET TimeZone='UTC'")
    # One on-floor machine-day table used everywhere: meters from machine_day, location by date from the prepared view.
    c.execute(f"""
        CREATE OR REPLACE VIEW floor AS
        SELECT m.machine_id, m.gaming_date, p.month, p.local_weekday, p.zone_id, p.zone_name, p.bank_id, p.location_id,
               m.config_id, p.theme, p.manufacturer, p.lease_class,
               m.scheduled_seconds / 3600.0 AS sched_h, m.available_seconds / 3600.0 AS avail_h,
               m.occupied_seconds / 3600.0 AS occ_h, m.paid_spins AS spins, m.payout_positive_spins AS hits,
               m.coin_in_cents / 100.0 AS coin_in, m.payout_cents / 100.0 AS payout,
               m.house_win_cents / 100.0 AS house_win, CAST(m.theo_cents AS DOUBLE) / 100.0 AS theo,
               m.sum_bet_squared * CAST(g.payout_multiplier_variance AS DOUBLE) / 1e4 AS luck_var,
               CAST(g.hit_probability AS DOUBLE) AS hit_p, CAST(g.configured_rtp AS DOUBLE) AS rtp,
               m.carded_coin_in_cents / 100.0 AS carded_coin_in, m.carded_payout_cents / 100.0 AS carded_payout,
               p.contribution_after_supplied_costs_usd::DOUBLE AS contribution
        FROM {MD} m
        JOIN {PV} p USING (machine_id, gaming_date)
        JOIN {GM} g ON g.config_id = m.config_id
        WHERE m.active
    """)
    return c


def clean(o):
    """JSON for browsers: NaN/inf become null, numpy scalars become Python numbers."""
    import math
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):
        try:
            o = o.item()
        except Exception:
            pass
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return o


def dump(obj, **kw) -> str:
    return json.dumps(clean(obj), allow_nan=False, default=str, **kw)


def save(name: str, obj) -> None:
    (RESULTS / f"{name}.json").write_text(dump(obj, indent=1))


def load(name: str):
    return json.loads((RESULTS / f"{name}.json").read_text())
