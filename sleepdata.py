"""Data loading, cleaning, statistics and auto-generated findings.

Pure pandas + numpy (no Streamlit / Plotly) so everything here is testable.
Every number shown in the dashboard is computed from the uploaded file.
"""
from __future__ import annotations

import io
import re
from html import escape as esc

import numpy as np
import pandas as pd

TARGET = "Quality of Sleep"
BMI_ORDER = ["Underweight", "Normal", "Overweight", "Obese"]
AGE_LABELS = ["Under 30", "30–39", "40–49", "50+"]

ALIASES = {
    "Person ID": ["person id", "personid", "id", "participant id"],
    "Gender": ["gender", "sex"],
    "Age": ["age"],
    "Occupation": ["occupation", "job", "profession"],
    "Sleep Duration": ["sleep duration", "sleep duration hours", "sleep hours", "hours of sleep"],
    "Quality of Sleep": ["quality of sleep", "sleep quality"],
    "Physical Activity Level": ["physical activity level", "physical activity", "activity level", "activity"],
    "Stress Level": ["stress level", "stress"],
    "BMI Category": ["bmi category", "bmi class"],
    "Blood Pressure": ["blood pressure"],
    "Heart Rate": ["heart rate", "resting heart rate"],
    "Daily Steps": ["daily steps", "steps"],
    "Sleep Disorder": ["sleep disorder"],
}
LOOKUP = {alias: col for col, names in ALIASES.items() for alias in names}
REQUIRED = ["Gender", "Age", "Occupation", "Sleep Duration", "Quality of Sleep",
            "Physical Activity Level", "Stress Level"]
CORE_NUMERIC = ["Age", "Sleep Duration", "Quality of Sleep", "Physical Activity Level", "Stress Level"]
VALID_RANGE = {  # values outside are treated as invalid (-> missing)
    "Age": (1, 110), "Sleep Duration": (0, 24), "Quality of Sleep": (0, 10),
    "Stress Level": (0, 10), "Physical Activity Level": (0, 1000),
    "Heart Rate": (20, 250), "Daily Steps": (0, 100000),
}
NA_TOKENS = {"", "na", "n/a", "nan", "null", "-", "?"}
BMI_MAP = {"normal weight": "Normal", "normal": "Normal", "overweight": "Overweight",
           "obese": "Obese", "obesity": "Obese", "underweight": "Underweight"}

# The three competing explanations in the research question.
GROUPS = {
    "Stress": ["Stress Level"],
    "Physical activity": ["Physical Activity Level"],
    "Lifestyle & body profile": ["Daily Steps", "BMI Score", "Heart Rate"],
}


class DataError(Exception):
    """Raised with a human-friendly message when a file can't be used."""


# --------------------------------------------------------------------------- loading
def _norm(name) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def _read(raw: bytes) -> pd.DataFrame:
    if not raw or not raw.strip():
        raise DataError("The file is empty. Please upload a CSV that contains a header row and data.")
    err = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            table = pd.read_csv(io.BytesIO(raw), dtype=str, keep_default_na=False,
                                sep=None, engine="python", encoding=enc)
            break
        except UnicodeDecodeError:
            continue
        except Exception as exc:  # parser / delimiter problems
            err = exc
            table = None
            break
    else:
        raise DataError("The file could not be decoded as text. Please export it again as a UTF-8 CSV.")
    if table is None:
        raise DataError(f"This doesn't look like a valid CSV file ({type(err).__name__}: {err}).")
    if table.empty or table.shape[1] < 2:
        raise DataError("The file has no usable rows or only one column. Check the delimiter and header row.")
    return table


def load(raw: bytes):
    """Parse raw CSV bytes -> (clean DataFrame, report dict). Raises DataError."""
    return prepare(_read(raw))


def prepare(table: pd.DataFrame):
    report: dict = {"rows_raw": len(table)}
    table = table.copy()
    table.columns = [str(c).strip() for c in table.columns]

    rename = {}
    for col in table.columns:
        canon = LOOKUP.get(_norm(col))
        if canon and canon not in rename.values():
            rename[col] = canon
    report["ignored_columns"] = [c for c in table.columns if c not in rename]
    df = table[list(rename)].rename(columns=rename)

    missing_cols = [c for c in REQUIRED if c not in df.columns]
    if missing_cols:
        raise DataError(
            "Required columns are missing: " + ", ".join(missing_cols)
            + ". Columns found: " + ", ".join("".join(ch for ch in str(c) if ch.isprintable()) for c in table.columns[:15])
            + ("…" if table.shape[1] > 15 else ""))

    # text cleanup + missing tokens
    for col in df.columns:
        s = df[col].astype(str).str.strip()
        df[col] = s.where(~s.str.lower().isin(NA_TOKENS), np.nan)

    # numeric coercion + validity ranges
    coerced, out_of_range = 0, {}
    for col, (lo, hi) in VALID_RANGE.items():
        if col not in df.columns:
            continue
        text = df[col]
        if col == "Daily Steps":
            text = text.str.replace(",", "", regex=False)
        elif col == "Sleep Duration":  # tolerate decimal commas (7,5)
            text = text.str.replace(",", ".", regex=False)
        num = pd.to_numeric(text, errors="coerce")
        coerced += int((text.notna() & num.isna()).sum())
        bad = num.notna() & ((num < lo) | (num > hi))
        out_of_range[col] = int(bad.sum())
        df[col] = num.mask(bad)
    report["unparseable_values"] = coerced
    report["out_of_range"] = {k: v for k, v in out_of_range.items() if v}
    report["missing"] = {c: int(n) for c, n in df.isna().sum().items() if n}

    # categories
    df["Gender"] = df["Gender"].str.title().fillna("Unknown")
    df["Occupation"] = df["Occupation"].fillna("Unknown")
    if "BMI Category" in df.columns:
        low = df["BMI Category"].str.lower()
        df["BMI Category"] = low.map(BMI_MAP).fillna(df["BMI Category"].str.title()).fillna("Unknown")
        df["BMI Score"] = df["BMI Category"].map({b: i for i, b in enumerate(BMI_ORDER)})
    if "Sleep Disorder" in df.columns:
        sd = df["Sleep Disorder"].str.title()
        df["Sleep Disorder"] = sd.fillna("Not recorded")
    if "Blood Pressure" in df.columns:
        bp = df["Blood Pressure"].str.extract(r"(\d{2,3})\s*/\s*(\d{2,3})")
        df["Systolic"] = pd.to_numeric(bp[0], errors="coerce")
        df["Diastolic"] = pd.to_numeric(bp[1], errors="coerce")

    # rows we cannot analyse at all
    keep = df[CORE_NUMERIC].notna().all(axis=1)
    report["dropped_rows"] = int((~keep).sum())
    df = df[keep].reset_index(drop=True)
    if df.empty:
        raise DataError("No rows contain valid values for sleep duration, sleep quality, stress, activity and age.")

    if "Person ID" not in df.columns:
        df.insert(0, "Person ID", np.arange(1, len(df) + 1).astype(str))
    report["duplicate_ids"] = int(df["Person ID"].duplicated().sum())
    content = [c for c in df.columns if c != "Person ID"]
    df["Repeat Profile"] = df.duplicated(subset=content, keep="first")
    report["repeat_profiles"] = int(df["Repeat Profile"].sum())

    df["Age Group"] = pd.cut(df["Age"], bins=[0, 30, 40, 50, 200], labels=AGE_LABELS, right=False)
    report["optional_missing"] = [c for c in ["BMI Category", "Blood Pressure", "Heart Rate", "Daily Steps",
                                              "Sleep Disorder"] if c not in df.columns]
    report["rows_clean"] = len(df)
    return df, report


def apply_filters(df, age_range, genders, occupations, exclude_repeats=False):
    m = df["Age"].between(age_range[0], age_range[1]) & df["Gender"].isin(genders) \
        & df["Occupation"].isin(occupations)
    if exclude_repeats:
        m &= ~df["Repeat Profile"]
    return df[m]


# --------------------------------------------------------------------------- statistics
def spearman(a: pd.Series, b: pd.Series) -> float:
    d = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(d) < 3 or d["a"].nunique() < 2 or d["b"].nunique() < 2:
        return float("nan")
    return float(d["a"].rank().corr(d["b"].rank()))


def strength(r: float) -> str:
    a = abs(r)
    return ("negligible" if a < 0.1 else "weak" if a < 0.3 else "moderate" if a < 0.5
            else "strong" if a < 0.7 else "very strong")


def eta(cat: pd.Series, y: pd.Series) -> float:
    """Correlation ratio: how much of y's variance sits between categories (0-1)."""
    d = pd.concat([cat.rename("c"), y.rename("y")], axis=1).dropna()
    if d["c"].nunique() < 2 or len(d) < 3:
        return float("nan")
    sst = ((d["y"] - d["y"].mean()) ** 2).sum()
    if sst == 0:
        return float("nan")
    ssb = d.groupby("c")["y"].agg(lambda v: len(v) * (v.mean() - d["y"].mean()) ** 2).sum()
    return float(np.sqrt(ssb / sst))


def correlation_matrix(df, cols=None):
    cols = cols or [c for c in ["Sleep Duration", "Quality of Sleep", "Stress Level",
                                "Physical Activity Level", "Daily Steps", "Heart Rate", "BMI Score", "Age"]
                    if c in df.columns]
    return df[cols].rank().corr().rename(index={"BMI Score": "BMI (ordinal)"},
                                         columns={"BMI Score": "BMI (ordinal)"})


def driver_table(df) -> pd.DataFrame:
    """How strongly each factor is associated with sleep quality (rank-based)."""
    rows = []
    numeric = [("Stress Level", "Stress"), ("Physical Activity Level", "Physical activity"),
               ("Daily Steps", "Lifestyle & body profile"), ("BMI Score", "Lifestyle & body profile"),
               ("Heart Rate", "Lifestyle & body profile"), ("Age", "Context")]
    for col, group in numeric:
        if col in df.columns:
            r = spearman(df[col], df[TARGET])
            if not np.isnan(r):
                rows.append(dict(Factor="BMI category (ordinal)" if col == "BMI Score" else col,
                                 Group=group, r=r, strength=abs(r), Method="Spearman ρ"))
    for col in ["Occupation", "Gender"]:
        e = eta(df[col], df[TARGET])
        if not np.isnan(e):
            rows.append(dict(Factor=col, Group="Context", r=float("nan"), strength=e, Method="Correlation ratio η"))
    return pd.DataFrame(rows).sort_values("strength", ascending=False).reset_index(drop=True) if rows \
        else pd.DataFrame(columns=["Factor", "Group", "r", "strength", "Method"])


def _r2(X: np.ndarray, y: np.ndarray) -> float:
    if X.shape[1] == 0:
        return 0.0
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    sst = ((y - y.mean()) ** 2).sum()
    return float(1 - ((y - X1 @ beta) ** 2).sum() / sst) if sst > 0 else float("nan")


def group_contributions(df):
    """R² of sleep quality explained by each group alone and uniquely (linear model)."""
    groups = {g: [c for c in cols if c in df.columns] for g, cols in GROUPS.items()}
    groups = {g: c for g, c in groups.items() if c}
    allc = [c for cols in groups.values() for c in cols]
    if len(groups) < 2:
        return None
    sub = df[[TARGET] + allc].dropna()
    allc = [c for c in allc if sub[c].nunique() > 1]
    groups = {g: [c for c in cols if c in allc] for g, cols in groups.items()}
    groups = {g: c for g, c in groups.items() if c}
    if len(sub) < len(allc) + 15 or len(groups) < 2:
        return None
    Z = (sub[allc] - sub[allc].mean()) / sub[allc].std(ddof=0)
    y = sub[TARGET].to_numpy(float)
    full = _r2(Z.to_numpy(), y)
    rows = []
    for g, cols in groups.items():
        rest = [c for c in allc if c not in cols]
        rows.append(dict(group=g, factors=", ".join(cols).replace("BMI Score", "BMI"),
                         alone=_r2(Z[cols].to_numpy(), y),
                         unique=max(0.0, full - _r2(Z[rest].to_numpy(), y))))
    return {"table": pd.DataFrame(rows), "full": full, "n": len(sub)}


def bin_means(df, x, y, q=4) -> pd.DataFrame:
    """Mean of y within quantile bins of x."""
    empty = pd.DataFrame(columns=["label", "mean", "n"])
    d = df[[x, y]].dropna()
    if d[x].nunique() < 2 or len(d) < q * 2:
        return empty
    try:
        bins = pd.qcut(d[x], q=q, duplicates="drop")
    except ValueError:
        return empty
    g = d.groupby(bins, observed=True)[y].agg(["mean", "count"]).reset_index()
    g.columns = ["interval", "mean", "n"]
    lo = float(d[x].min())
    g["label"] = [f"{max(i.left, lo) if k == 0 else i.left:,.0f}–{i.right:,.0f}" for k, i in enumerate(g["interval"])]
    return g[["label", "mean", "n"]]


def group_summary(df, by) -> pd.DataFrame:
    return (df.groupby(by, observed=True)
              .agg(n=("Person ID", "size"), duration=("Sleep Duration", "mean"), quality=(TARGET, "mean"),
                   stress=("Stress Level", "mean"), activity=("Physical Activity Level", "mean"))
              .reset_index())


def extreme_gap(df, col, target=TARGET, q=0.25):
    d = df[[col, target]].dropna()
    if d.empty:
        return None
    lo, hi = d[col].quantile(q), d[col].quantile(1 - q)
    a, b = d.loc[d[col] <= lo, target], d.loc[d[col] >= hi, target]
    if lo >= hi or len(a) < 5 or len(b) < 5:
        return None
    return dict(lo=lo, hi=hi, low_mean=a.mean(), high_mean=b.mean(), n_low=len(a), n_high=len(b))


def _trend_word(means: pd.Series) -> str:
    d = np.sign(np.diff(means.to_numpy()))
    if len(d) >= 2 and (d > 0).all():
        return "rises steadily"
    if len(d) >= 2 and (d < 0).all():
        return "falls steadily"
    return "does not move in a straight line"


# --------------------------------------------------------------------------- findings
def b(v) -> str:
    return f"<b>{esc(str(v))}</b>"


def build_findings(df, contrib=None):
    """Return [(tag, title, body_html)] — all numbers computed from `df`."""
    out = []
    if len(df) < 10:
        return [("Small sample", "Too few records for findings",
                 "Fewer than 10 records match the current filters. Loosen the filters to see findings.")]

    if contrib:
        t = contrib["table"].sort_values("alone", ascending=False).reset_index(drop=True)
        parts = "; ".join(f"{esc(r.group)} {r.alone:.0%}" for r in t.itertuples())
        top = t.iloc[0]
        gap = top.alone - t.iloc[1].alone
        if top.alone < 0.05:
            verdict = "None of the three explains much of the variation in this sample."
        elif gap < 0.05:
            verdict = f"{b(top.group)} leads, but the gap to the runner-up is small — the data cannot clearly separate them."
        else:
            verdict = f"{b(top.group)} comes out ahead in this sample."
        overlap = ""
        if t["unique"].sum() < 0.6 * t["alone"].sum():
            overlap = " Much of what each group explains overlaps with the others, so their separate effects are hard to untangle."
        out.append(("Research question", "What matters more for sleep quality?",
                    f"Share of sleep-quality variation each group explains on its own: {parts}. {verdict}{overlap} "
                    f"Together they explain {contrib['full']:.0%} (n = {contrib['n']})."))

    r = spearman(df["Stress Level"], df[TARGET])
    gap = extreme_gap(df, "Stress Level")
    if not np.isnan(r):
        body = (f"Stress and sleep quality are {strength(r)}ly associated "
                f"({'inversely' if r < 0 else 'positively'}, Spearman ρ = {r:.2f}).")
        if gap:
            body += (f" The lowest-stress group (stress ≤ {gap['lo']:.0f}) averages {gap['low_mean']:.1f}/10 sleep quality "
                     f"vs {gap['high_mean']:.1f}/10 for the highest-stress group (≥ {gap['hi']:.0f}).")
        out.append(("Stress", "Stress and sleep quality", body))

    r = spearman(df["Physical Activity Level"], df[TARGET])
    bm = bin_means(df, "Physical Activity Level", TARGET)
    if not np.isnan(r):
        body = f"Physical activity and sleep quality show a {strength(r)} association (ρ = {r:.2f})."
        if len(bm) >= 3:
            body += f" Average quality {_trend_word(bm['mean'])} across activity quartiles."
        out.append(("Activity", "Physical activity and sleep quality", body))

    if "Daily Steps" in df.columns:
        r = spearman(df["Daily Steps"], df["Sleep Duration"])
        if not np.isnan(r):
            out.append(("Activity", "Daily steps and sleep duration",
                        f"Daily steps and sleep duration show a {strength(r)} association (ρ = {r:.2f})."))

    if "BMI Category" in df.columns:
        g = group_summary(df[df["BMI Category"] != "Unknown"], "BMI Category")
        g = g[g["n"] >= 5]
        if len(g) >= 2:
            hi, lo = g.loc[g["quality"].idxmax()], g.loc[g["quality"].idxmin()]
            out.append(("Lifestyle", "BMI categories",
                        f"{b(hi['BMI Category'])} averages {hi.quality:.1f}/10 sleep quality (n = {int(hi.n)}) versus "
                        f"{b(lo['BMI Category'])} at {lo.quality:.1f}/10 (n = {int(lo.n)})."))

    g = group_summary(df, "Occupation")
    g = g[g["n"] >= 10]
    if len(g) >= 2:
        hi, lo = g.loc[g["quality"].idxmax()], g.loc[g["quality"].idxmin()]
        out.append(("Demographics", "Occupation differences",
                    f"Among occupations with ≥ 10 people, {b(hi['Occupation'])} reports the best sleep quality "
                    f"({hi.quality:.1f}/10) and {b(lo['Occupation'])} the lowest ({lo.quality:.1f}/10)."))

    if "Sleep Disorder" in df.columns:
        g = group_summary(df[df["Sleep Disorder"] != "Not recorded"], "Sleep Disorder")
        g = g[g["n"] >= 5]
        if len(g) >= 2:
            hi, lo = g.loc[g["quality"].idxmax()], g.loc[g["quality"].idxmin()]
            out.append(("Health", "Sleep disorders",
                        f"Sleep quality averages {hi.quality:.1f}/10 for “{esc(hi['Sleep Disorder'])}” "
                        f"(n = {int(hi.n)}) versus {lo.quality:.1f}/10 for “{esc(lo['Sleep Disorder'])}” (n = {int(lo.n)})."))
    return out


def limitations(report, df_all, df):
    n = len(df_all)
    items = [
        "<b>Correlation is not causation.</b> These patterns describe association only. Stress, activity and sleep "
        "may influence each other in both directions, and unmeasured factors could drive all of them.",
        f"<b>Small, single-snapshot sample.</b> {len(df):,} records are in view. Results may not generalise, and "
        "subgroups (some occupations or BMI categories) are very small.",
        "<b>Coarse, probably self-reported measures.</b> Sleep quality and stress are whole-number ratings, which "
        "creates many ties and limits what any statistic can show.",
    ]
    if report["repeat_profiles"]:
        items.append(
            f"<b>Repeated profiles.</b> {report['repeat_profiles']:,} of {n:,} records "
            f"({report['repeat_profiles'] / n:.0%}) match an earlier record on every column except Person ID. "
            "They may be genuinely similar people or duplicate entries. Use the sidebar toggle to check whether "
            "conclusions change without them.")
    if report["dropped_rows"] or report["out_of_range"] or report["unparseable_values"]:
        items.append(
            f"<b>Cleaning applied.</b> {report['dropped_rows']} rows were dropped for missing core values, "
            f"{sum(report['out_of_range'].values())} out-of-range values and "
            f"{report['unparseable_values']} unreadable values were set to missing.")
    if report["optional_missing"]:
        items.append("<b>Columns not in this file:</b> " + esc(", ".join(report["optional_missing"]))
                     + ". Related charts are hidden or reduced.")
    return items


def headline(contrib) -> str:
    """One short, data-driven sentence for cards (HTML)."""
    t = contrib["table"].sort_values("alone", ascending=False).reset_index(drop=True)
    top, second = t.iloc[0], t.iloc[1]
    if top.alone < 0.05:
        lead = "No group explains much of the variation in sleep quality in this sample."
    elif top.alone - second.alone < 0.05:
        lead = (f"{b(top.group)} and {b(second.group)} are too close to separate "
                f"({top.alone:.0%} vs {second.alone:.0%}).")
    else:
        lead = (f"{b(top.group)} lines up most closely with sleep quality, explaining {b(f'{top.alone:.0%}')} of its variation "
                f"on its own, versus {second.alone:.0%} for {esc(second.group)}.")
    return f"<p>{lead}</p><p>This is association, not cause — the Final Discoveries page shows the evidence and limits.</p>"


def same_leader(c1, c2) -> str:
    a = c1["table"].sort_values("alone", ascending=False).iloc[0].group
    z = c2["table"].sort_values("alone", ascending=False).iloc[0].group
    return (f"The leading group is still {esc(z)}." if a == z
            else f"The leading group changes from {esc(a)} to {esc(z)}, so treat the ranking with caution.")


# --------------------------------------------------------------------------- sleep profiles
PROFILE_METRICS = [  # (column, label, unit, decimals)
    ("Sleep Duration", "Sleep duration", " h", 2),
    (TARGET, "Sleep quality", " /10", 1),
    ("Stress Level", "Stress", " /10", 1),
    ("Physical Activity Level", "Physical activity", " min/day", 0),
    ("Daily Steps", "Daily steps", "", 0),
    ("Heart Rate", "Heart rate", " bpm", 0),
    ("Age", "Age", " yrs", 0),
]


def profile_metrics(df):
    return [m for m in PROFILE_METRICS if m[0] in df.columns and df[m[0]].notna().any()]


def profile_defs(df, min_n: int = 8):
    """Profiles defined by this sample's own quartiles/medians (so they follow the sidebar filters).

    Returns [dict(key, name, rule, mask, defining)]; a profile needs at least `min_n` people
    and must not be the whole sample.
    """
    if len(df) < 2 * min_n:
        return []
    S, A, T, D = "Stress Level", "Physical Activity Level", TARGET, "Sleep Duration"
    q = lambda c, p: float(df[c].quantile(p))
    raw = [
        ("high_stress", "High-stress sleepers", f"Stress ≥ {q(S, .75):g}", df[S] >= q(S, .75), {S}),
        ("low_stress", "Low-stress sleepers", f"Stress ≤ {q(S, .25):g}", df[S] <= q(S, .25), {S}),
        ("active", "Active sleepers", f"Activity ≥ {q(A, .75):g} min/day", df[A] >= q(A, .75), {A}),
        ("inactive", "Low-activity sleepers", f"Activity ≤ {q(A, .25):g} min/day", df[A] <= q(A, .25), {A}),
        ("good", "Good sleepers", f"Sleep quality ≥ {q(T, .75):g}", df[T] >= q(T, .75), {T}),
        ("poor", "Poor sleepers", f"Sleep quality ≤ {q(T, .25):g}", df[T] <= q(T, .25), {T}),
        ("short", "Short sleepers", f"Sleep ≤ {q(D, .25):g} h", df[D] <= q(D, .25), {D}),
        ("calm_active", "Calm & active",
         f"Stress ≤ {q(S, .5):g} and activity ≥ {q(A, .5):g} min/day (medians)",
         (df[S] <= q(S, .5)) & (df[A] >= q(A, .5)), {S, A}),
    ]
    if "Sleep Disorder" in df.columns:
        raw.append(("disorder", "Reported sleep disorder", "A sleep disorder is recorded",
                    ~df["Sleep Disorder"].isin(["None", "Not recorded"]), {"Sleep Disorder"}))
    out = []
    for key, name, rule, mask, defining in raw:
        mask = mask.fillna(False)
        if min_n <= int(mask.sum()) < len(df):
            out.append(dict(key=key, name=name, rule=rule, mask=mask, defining=defining))
    return out


def profile_summary(df, p, metrics):
    """Group-vs-everyone-else statistics and a plain-language note built only from the differences found."""
    m = p["mask"]
    g, rest = df[m], df[~m]
    rows, effects = [], []
    for col, label, unit, dec in metrics:
        gm, rm = float(g[col].mean()), float(rest[col].mean())
        r = dict(col=col, label=label, unit=unit, dec=dec, group=gm, rest=rm, diff=gm - rm)
        rows.append(r)
        spread = float(df[col].std())
        if col not in p["defining"] and spread > 0 and not np.isnan(r["diff"]):
            effects.append((abs(r["diff"]) / spread, r))
    effects.sort(key=lambda t: -t[0])
    notes = [f"{r['label'].lower()} averages {r['group']:.{r['dec']}f}{r['unit']} vs {r['rest']:.{r['dec']}f}{r['unit']} for everyone else"
             for e, r in effects[:3] if e >= 0.2]
    occ = g["Occupation"].value_counts()
    disorder = None
    if "Sleep Disorder" in g.columns:
        disorder = float((~g["Sleep Disorder"].isin(["None", "Not recorded"])).mean())
    return dict(n=int(m.sum()), share=float(m.mean()), rows=rows, notes=notes,
                top_occ=(str(occ.index[0]), int(occ.iloc[0])) if len(occ) else None, disorder=disorder)


def effect_word(d: float) -> str:
    if d is None or np.isnan(d):
        return "n/a"
    a = abs(d)
    return "negligible" if a < 0.2 else "small" if a < 0.5 else "moderate" if a < 0.8 else "large"


def compare_profiles(df, ma, mb, metrics):
    """Means of each profile, their difference and Cohen's d (pooled SD). Also returns how many people are in both."""
    a, b = df[ma], df[mb]
    rows = []
    for col, label, unit, dec in metrics:
        am, bm = float(a[col].mean()), float(b[col].mean())
        na, nb = int(a[col].count()), int(b[col].count())
        d = np.nan
        if na > 1 and nb > 1:
            pooled = np.sqrt(((na - 1) * a[col].var(ddof=1) + (nb - 1) * b[col].var(ddof=1)) / (na + nb - 2))
            if pooled > 0:
                d = (am - bm) / pooled
        rows.append(dict(col=col, label=label, unit=unit, dec=dec, a=am, b=bm, diff=am - bm, d=float(d)))
    return pd.DataFrame(rows), int((ma & mb).sum())
