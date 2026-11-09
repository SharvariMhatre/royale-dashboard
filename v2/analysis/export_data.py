"""Columnar data the dashboard recomputes from in the browser (site/data/floor.json, guests.json).

Every metric on the page is a ratio of sums over these rows, so any period, zone, bank or group
selection is exact, not a precomputed approximation."""
from __future__ import annotations

import json

import numpy as np

from common import CAL, EVT, LOC, OUT, PD, PP, TRAF, con


def r(x, n=2):
    return [round(float(v), n) for v in x]


def main() -> None:
    c = con()
    days = [str(d)[:10] for (d,) in c.sql(f"SELECT gaming_date FROM {CAL} ORDER BY 1").fetchall()]
    f = c.sql("SELECT * FROM floor ORDER BY gaming_date, machine_id").df()
    dims = {}
    for col in ["machine_id", "zone_id", "bank_id", "config_id"]:
        dims[col] = sorted(f[col].unique().tolist())
    idx = {col: {v: i for i, v in enumerate(dims[col])} for col in dims}
    day_i = {d: i for i, d in enumerate(days)}
    floor = {
        "m": [idx["machine_id"][v] for v in f.machine_id],
        "d": [day_i[str(v)[:10]] for v in f.gaming_date],
        "z": [idx["zone_id"][v] for v in f.zone_id],
        "b": [idx["bank_id"][v] for v in f.bank_id],
        "g": [idx["config_id"][v] for v in f.config_id],
        "sh": r(f.sched_h, 3), "ah": r(f.avail_h, 3), "oh": r(f.occ_h, 3),
        "sp": f.spins.astype(int).tolist(), "hi": f.hits.astype(int).tolist(),
        "ci": r(f.coin_in), "hw": r(f.house_win), "th": r(f.theo, 4), "v": r(f.luck_var, 1),
        "cc": r(f.contribution),
    }
    zones = c.sql(f"SELECT zone_id, name FROM {LOC} WHERE node_type='zone' ORDER BY 1").df()
    machines = c.sql("""SELECT machine_id, any_value(theme) theme, any_value(manufacturer) mfr, any_value(lease_class) lease,
                        arg_max(zone_id, gaming_date) last_zone, arg_max(bank_id, gaming_date) last_bank,
                        arg_max(location_id, gaming_date) last_loc FROM floor GROUP BY 1 ORDER BY 1""").df()
    games = c.sql("SELECT config_id, any_value(theme) theme, any_value(rtp) rtp, any_value(hit_p) hit_p FROM floor GROUP BY 1 ORDER BY 1").df()
    slots = c.sql(f"SELECT location_id, bank_id, zone_id, x_m, y_m FROM {LOC} WHERE node_type='slot'").df()
    meta = {
        "days": days,
        "weekday": [w for (w,) in c.sql(f"SELECT local_weekday FROM {CAL} ORDER BY gaming_date").fetchall()],
        "dims": dims,
        "zone_names": dict(zip(zones.zone_id, zones.name)),
        "machines": machines.to_dict("records"),
        "games": games.to_dict("records"),
        "slots": slots.to_dict("records"),
    }
    prop = c.sql(f"""SELECT gaming_date::VARCHAR d, coin_in_usd::DOUBLE ci, house_win_usd::DOUBLE hw, theo_usd::DOUBLE th,
        available_machine_hours ah, occupied_machine_hours oh, comp_cost_usd::DOUBLE comp, comp_face_value_usd::DOUBLE comp_face,
        pos_cash_usd::DOUBLE pos_cash, pos_cogs_usd::DOUBLE pos_cogs, total_zone_entries_observed entries,
        counter_coverage_share cov, coalesce(events_active,'') events FROM {PD} ORDER BY 1""").df()
    traffic = c.sql(f"""SELECT zone_id, CAST(hour_start_local - INTERVAL 6 HOUR AS DATE)::VARCHAR d,
        sum(entries_count) FILTER (WHERE counter_status <> 'offline') e, sum(coverage_minutes) cov_min
        FROM {TRAF} GROUP BY 1, 2 ORDER BY 2, 1""").df()
    events = c.sql(f"SELECT event_id, name, event_type, start_date::VARCHAR s, end_date::VARCHAR e, announced_date::VARCHAR a, local_scope FROM {EVT} ORDER BY s").df()
    payload = {"meta": meta, "floor": floor, "property": prop.to_dict("list"),
               "traffic": traffic.to_dict("list"), "events": events.to_dict("records")}
    (OUT / "floor.json").write_text(json.dumps(payload, separators=(",", ":"), default=float))

    # Guests: tracked play by month x tier x age x region (sums only, so any group/period is exact)
    g = c.sql(f"""SELECT period_month mo, opening_tier tier, coalesce(age_band,'unknown') age, home_region region,
        count(*) pm, sum(tracked_coin_in_usd)::DOUBLE ci, sum(tracked_payout_usd)::DOUBLE po, sum(tracked_net_usd)::DOUBLE net,
        sum(theo_usd)::DOUBLE th, sum(comp_cost_usd)::DOUBLE comp, sum(comp_face_value_usd)::DOUBLE face,
        sum(points_earned)::DOUBLE pe, sum(points_redeemed)::DOUBLE pr, sum(observed_visits)::DOUBLE visits,
        sum(CASE WHEN tracked_net_usd > 0 THEN 1 ELSE 0 END) ahead_pm
        FROM {PP} GROUP BY ALL ORDER BY ALL""").df()
    (OUT / "guests.json").write_text(json.dumps(g.to_dict("list"), separators=(",", ":"), default=float))
    print(f"floor rows {len(f):,}  guest cells {len(g):,}  size {(OUT / 'floor.json').stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
