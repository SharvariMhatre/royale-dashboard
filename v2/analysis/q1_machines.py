"""Q1: which machines truly underperform, and the M-1158 mechanism.

Luck uses the closed form: z = (house win - theo) / sqrt(sum_bet_squared x payout_multiplier_variance).
Hit test: z_hit = (hits - p x spins) / sqrt(p (1 - p) spins), independent of award size.
Peer indices exclude the machine itself (leave-one-out)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import GM, PLC, SES, con, save

Z_INSPECT = 3.29  # two-sided p < 0.001 per machine: about 0.3 false alarms across 310 machines


def machine_table(c, start="2025-01-01", end="2025-06-30") -> pd.DataFrame:
    f = c.sql(f"SELECT * FROM floor WHERE gaming_date BETWEEN '{start}' AND '{end}'").df()
    m = f.groupby("machine_id").agg(
        zone=("zone_id", "last"), bank=("bank_id", "last"), config=("config_id", "first"), theme=("theme", "first"),
        lease=("lease_class", "first"), days=("gaming_date", "nunique"), sched_h=("sched_h", "sum"), avail_h=("avail_h", "sum"),
        occ_h=("occ_h", "sum"), coin_in=("coin_in", "sum"), house_win=("house_win", "sum"), theo=("theo", "sum"),
        var=("luck_var", "sum"), spins=("spins", "sum"), hits=("hits", "sum"), hit_p=("hit_p", "first"),
        contribution=("contribution", "sum"))
    m["luck_z"] = (m.house_win - m.theo) / np.sqrt(m["var"].where(m["var"] > 0))
    m["hit_z"] = (m.hits - m.hit_p * m.spins) / np.sqrt(m.hit_p * (1 - m.hit_p) * m.spins.where(m.spins > 0))
    m["theo_per_h"] = m.theo / m.avail_h
    m["availability"] = m.avail_h / m.sched_h
    # Same game, rest of floor (leave-one-out): theo per available hour
    g = f.groupby("config_id")[["theo", "avail_h"]].sum()
    m["game_rate_loo"] = (m.config.map(g.theo) - m.theo) / (m.config.map(g.avail_h) - m.avail_h)
    m["vs_same_game"] = m.theo_per_h / m.game_rate_loo
    # Same game in the same zone, leave-one-out (machine effect net of location)
    # Expected theo = the machine's own hours x the rate of its game in the zone it stood in that day,
    # with the machine's own play removed from that rate (so moved machines are compared correctly).
    gz = f.groupby(["config_id", "zone_id"])[["theo", "avail_h"]].sum()
    own = f.groupby(["machine_id", "config_id", "zone_id"])[["theo", "avail_h"]].sum().reset_index()
    tot = gz.reindex(list(zip(own.config_id, own.zone_id))).to_numpy()
    peer_h = tot[:, 1] - own.avail_h.values
    peer_rate = np.where(peer_h > 50, (tot[:, 0] - own.theo.values) / np.where(peer_h > 0, peer_h, np.nan), np.nan)
    own["expected"] = own.avail_h * peer_rate
    own["covered"] = np.where(np.isnan(peer_rate), 0, own.avail_h)
    agg = own.assign(expected=own.expected.fillna(0)).groupby("machine_id")[["expected", "covered", "theo"]].sum()
    own_cov = own[own.covered > 0].groupby("machine_id").theo.sum()
    m["vs_same_game_zone"] = (own_cov / agg.expected.where(agg.expected > 0)).reindex(m.index)
    # Zone index: zone theo per hour vs what its game mix earns floor-wide (excluding the zone itself)
    # Only games that also run elsewhere can be compared, so both sides use that subset.
    zg = f.groupby(["zone_id", "config_id"])[["theo", "avail_h"]].sum().reset_index()
    zone_idx = {}
    for z, grp in zg.groupby("zone_id"):
        other = f[f.zone_id != z].groupby("config_id")[["theo", "avail_h"]].sum()
        rate = (other.theo / other.avail_h).reindex(grp.config_id).values
        ok = ~np.isnan(rate)
        zone_idx[z] = float(grp.theo.values[ok].sum() / (grp.avail_h.values[ok] * rate[ok]).sum()) if ok.any() else float("nan")
    m["zone_index"] = m.zone.map(zone_idx)
    m["verdict"] = m.apply(verdict, axis=1)
    return m, zone_idx


def verdict(r) -> str:
    if abs(r.luck_z) > Z_INSPECT or abs(r.hit_z) > Z_INSPECT:
        return "Inspect"
    if r.days < 120:
        return "Short exposure"
    if r.vs_same_game_zone < 0.8:
        return "Truly weak"
    if r.zone_index < 0.85:
        return "Bad spot"
    if r.luck_z < -1.96:
        return "Unlucky"
    return "Healthy"


def mechanism(c) -> dict:
    """Is M-1158's anomaly meter arithmetic, a bet level, a period, or the paytable?"""
    S = SES
    integ = c.sql(f"""SELECT count(*) sessions,
        count(*) FILTER (WHERE NOT list_contains(string_split(g.bet_options_cents, '|'), s.fixed_bet_cents::VARCHAR)) illegal_bets,
        count(*) FILTER (WHERE s.payout_cents % g.payout_increment_cents <> 0) off_increment,
        count(*) FILTER (WHERE s.coin_in_cents <> s.fixed_bet_cents * s.paid_spins) coin_in_mismatch
        FROM {S} s JOIN {GM} g USING (config_id)""").df().iloc[0].to_dict()
    by_bet = c.sql(f"""SELECT fixed_bet_cents bet, sum(paid_spins) spins, sum(payout_positive_spins)/sum(paid_spins) hit,
        1 - sum(payout_cents)/sum(coin_in_cents)::DOUBLE hold, sum(payout_cents)/sum(payout_positive_spins)/avg(fixed_bet_cents) award_x
        FROM {S} WHERE machine_id='M-1158' GROUP BY 1 ORDER BY 1""").df()
    peers = c.sql(f"""SELECT sum(payout_positive_spins)/sum(paid_spins) hit, 1 - sum(payout_cents)/sum(coin_in_cents)::DOUBLE hold,
        sum(payout_cents)/sum(payout_positive_spins)/(sum(coin_in_cents)/sum(paid_spins)) award_x
        FROM {S} WHERE config_id='G-STD90' AND machine_id <> 'M-1158'""").df().iloc[0].to_dict()
    by_month = c.sql("""SELECT month, sum(hits)/sum(spins) hit, sum(house_win)/sum(coin_in) hold,
        (sum(hits) - any_value(hit_p)*sum(spins)) / sqrt(any_value(hit_p)*(1-any_value(hit_p))*sum(spins)) hit_z
        FROM floor WHERE machine_id='M-1158' GROUP BY 1 ORDER BY 1""").df()
    split = c.sql("""SELECT 1 - sum(carded_payout)/sum(carded_coin_in) carded_hold,
        1 - (sum(payout) - sum(carded_payout)) / (sum(coin_in) - sum(carded_coin_in)) uncarded_hold,
        sum(coin_in) coin_in, sum(theo) theo, sum(house_win) house_win, count(*) AS n_days FROM floor WHERE machine_id='M-1158'""").df().iloc[0].to_dict()
    eff_rtp = 1 - split["house_win"] / split["coin_in"]
    return {"integrity": integ, "by_bet": by_bet.to_dict("records"), "peers": peers, "by_month": by_month.to_dict("records"),
            "split": split, "effective_rtp": eff_rtp, "configured_rtp": 0.90,
            "shortfall_per_day": (split["theo"] - split["house_win"]) / split["n_days"]}


def swaps_and_moves(c) -> dict:
    """Our own natural experiments: the same slot with a new machine, and machines that moved zone."""
    out = {}
    q = lambda sql: c.sql(sql).df()
    # Same slot, two machines (L-38-5: M-1120 until 2025-05-13, then M-5076 with the same game)
    out["same_slot"] = q("""SELECT machine_id, min(gaming_date)::VARCHAR first, max(gaming_date)::VARCHAR last, count(*) AS n_days,
        sum(theo)/sum(avail_h) theo_per_h, sum(coin_in)/sum(avail_h) coin_in_per_h, sum(occ_h)/sum(avail_h) occupancy
        FROM floor WHERE location_id='L-38-5' GROUP BY 1 ORDER BY first""").to_dict("records")
    # Floor reference over the same windows, so a floor-wide change is not credited to the swap
    out["same_slot_floor"] = q("""SELECT gaming_date < DATE '2025-05-13' before, sum(theo)/sum(avail_h) floor_theo_per_h
        FROM floor GROUP BY 1 ORDER BY 1""").to_dict("records")
    moves = []
    for mid in ["M-1152", "M-1113", "M-1126", "M-1299"]:
        r = q(f"""WITH x AS (SELECT gaming_date, zone_id, theo, avail_h, config_id FROM floor WHERE machine_id='{mid}')
            SELECT zone_id, min(gaming_date)::VARCHAR first, max(gaming_date)::VARCHAR last, count(*) AS n_days,
                   sum(theo)/sum(avail_h) theo_per_h FROM x GROUP BY 1 ORDER BY first""")
        moves.append({"machine_id": mid, "spells": r.to_dict("records")})
    out["moves"] = moves
    return out


def main() -> None:
    c = con()
    m, zone_idx = machine_table(c)
    gm10 = m.sort_values("house_win").head(10).index.tolist()
    m["gm_rank"] = m.index.map({k: i + 1 for i, k in enumerate(gm10)})
    calib = {"luck_z_sd": float(m.luck_z.std()), "hit_z_sd_excl_1158": float(m.drop("M-1158").hit_z.std()),
             "n_inspect": int((m.verdict == "Inspect").sum())}
    # Luck persistence: does a machine's luck in Jan-Mar predict Apr-Jun? (pure luck would not)
    a, _ = machine_table(c, "2025-01-01", "2025-03-31")
    b, _ = machine_table(c, "2025-04-01", "2025-06-30")
    both = pd.concat([a.luck_z, b.luck_z], axis=1, keys=["h1", "h2"]).dropna().drop("M-1158", errors="ignore")
    calib["luck_persistence_r"] = float(both.corr().iloc[0, 1])
    save("q1", {"machines": m.reset_index().to_dict("records"), "gm10": gm10, "zone_index": zone_idx, "calibration": calib,
                "verdict_counts": m.verdict.value_counts().to_dict(),
                "gm10_verdicts": m.loc[gm10, "verdict"].value_counts().to_dict()})
    save("mechanism", mechanism(c))
    save("experiments", swaps_and_moves(c))
    print(m.loc[gm10, ["zone", "days", "luck_z", "hit_z", "vs_same_game", "vs_same_game_zone", "zone_index", "verdict"]].round(2))
    print(calib, m.verdict.value_counts().to_dict())


if __name__ == "__main__":
    main()
