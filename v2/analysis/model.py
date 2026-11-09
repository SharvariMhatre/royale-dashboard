"""Daily floor coin-in forecast. Candidates are chosen by rolling-origin CV inside Jan-Apr only;
May-Jun is scored once, at the end. Event flags only use events announced before each forecast origin.
An 80% interval comes from CV residuals (split-conformal) and its May-Jun coverage is reported."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge

from common import CAL, EVT, PD, con, save

TRAIN_END = pd.Timestamp("2025-04-30")
WD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def frame(c) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = c.sql(f"""SELECT p.gaming_date::DATE AS gd, p.coin_in_usd::DOUBLE AS y, c.local_weekday AS wd,
                  c.federal_holiday IS NOT NULL AS hol, c.scheduled_seconds / 3600.0 AS hrs
                  FROM {PD} p JOIN {CAL} c USING (gaming_date) ORDER BY 1""").df()
    d["gd"] = pd.to_datetime(d.gd)
    ev = c.sql(f"SELECT * FROM {EVT}").df()
    for col in ["start_date", "end_date", "announced_date"]:
        ev[col] = pd.to_datetime(ev[col])
    return d, ev


def feats(df: pd.DataFrame, ev: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    X = pd.DataFrame({w: (df.wd.str[:3] == w).astype(float) for w in WD}, index=df.index)
    X["hol"] = df.hol.astype(float)
    X["hrs"] = df.hrs
    for et in ["convention", "sports_viewing", "festival", "property_promotion"]:
        X["ev_" + et] = 0.0
        for _, e in ev[(ev.event_type == et) & (ev.announced_date < origin)].iterrows():
            X.loc[(df.gd >= e.start_date) & (df.gd <= e.end_date), "ev_" + et] = 1.0
    return X


MODELS = ["Constant mean", "Weekday mean", "Weekday median", "Weekday + events (ridge)", "Gradient boosting"]


def predict(name, tr, te, ev, origin):
    if name == "Constant mean":
        return np.full(len(te), tr.y.mean())
    if name == "Weekday mean":
        return te.wd.map(tr.groupby("wd").y.mean()).values
    if name == "Weekday median":
        return te.wd.map(tr.groupby("wd").y.median()).values
    Xtr, Xte = feats(tr, ev, origin), feats(te, ev, origin)
    if name == "Weekday + events (ridge)":
        return Ridge(alpha=1.0).fit(Xtr, tr.y).predict(Xte)
    return GradientBoostingRegressor(n_estimators=200, max_depth=2, learning_rate=0.05, random_state=0).fit(Xtr, tr.y).predict(Xte)


def main() -> None:
    c = con()
    d, ev = frame(c)
    train = d[d.gd <= TRAIN_END]
    # Rolling origins: fit on everything before each origin, forecast the next 14 days.
    origins = pd.date_range("2025-03-01", "2025-04-17", freq="14D")
    cv, resid = {n: [] for n in MODELS}, {n: [] for n in MODELS}
    for o in origins:
        tr, va = train[train.gd < o], train[(train.gd >= o) & (train.gd < o + pd.Timedelta(days=14))]
        for n in MODELS:
            p = predict(n, tr, va, ev, o)
            cv[n].append(np.abs(va.y.values - p).mean())
            resid[n].extend((va.y.values - p).tolist())
    cv_mae = {n: float(np.mean(v)) for n, v in cv.items()}
    selected = min(cv_mae, key=cv_mae.get)
    # Final: fit on all of Jan-Apr, forecast May-Jun once.
    test = d[d.gd > TRAIN_END]
    preds = {n: predict(n, train, test, ev, TRAIN_END + pd.Timedelta(days=1)) for n in MODELS}
    test_mae = {n: float(np.abs(test.y.values - p).mean()) for n, p in preds.items()}
    r = np.abs(np.array(resid[selected]))
    q80 = float(np.quantile(r, 0.8))
    p_sel = preds[selected]
    coverage = float(np.mean(np.abs(test.y.values - p_sel) <= q80))
    # Decision use: forecast by weekday for July staffing and the promotion break-even
    by_wd = pd.DataFrame({"wd": test.wd.str[:3], "pred": p_sel}).groupby("wd").pred.mean().reindex(WD)
    save("model", {
        "cv_origins": [o.strftime("%Y-%m-%d") for o in origins], "cv_mae": cv_mae, "selected": selected,
        "test_mae": test_mae, "interval_80_halfwidth": q80, "interval_80_coverage": coverage,
        "test": {"d": [x.strftime("%Y-%m-%d") for x in test.gd], "actual": test.y.round(0).tolist(),
                 "pred": np.round(p_sel, 0).tolist(), "baseline": np.round(preds["Constant mean"], 0).tolist()},
        "weekday_forecast": by_wd.round(0).to_dict(),
        "train_bias": float((test.y.values - p_sel).mean()),
    })
    print("CV", {k: round(v) for k, v in cv_mae.items()}, "->", selected)
    print("TEST", {k: round(v) for k, v in test_mae.items()}, "80% band +/-", round(q80), "coverage", round(coverage, 3))


if __name__ == "__main__":
    main()
