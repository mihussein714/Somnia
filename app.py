"""Somnia — Decode your nights. A Sleep, Health & Lifestyle analytics dashboard.

Run:  streamlit run app.py
"""
from __future__ import annotations

import hashlib
import time
from html import escape as esc
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import sleepdata as sd
import theme
import viz

st.set_page_config(page_title="Somnia · Decode your nights", page_icon="🌙", layout="wide", initial_sidebar_state="expanded")

# Streamlit only reads .streamlit/config.toml from the folder it was launched in; if that file was missed, the UI falls back to
# Streamlit's default red. Apply the theme from code too, then rerun once so the browser receives it.
_THEME = {"base": "dark", "primaryColor": "#8B5CF6", "backgroundColor": "#0B0F19",
          "secondaryBackgroundColor": "#111830", "textColor": "#E7EAF6", "font": "sans serif"}
try:
    from streamlit import config as _cfg
    if _cfg.get_option("theme.primaryColor") != _THEME["primaryColor"] and not st.session_state.get("_theme_applied"):
        for _k, _v in _THEME.items():
            _cfg.set_option(f"theme.{_k}", _v)
        st.session_state["_theme_applied"] = True
        st.rerun()
except Exception:  # never let theming break the app
    pass

_SAMPLE_NAME = "Sleep_health_and_lifestyle_dataset.csv"
SAMPLE = next((p for p in (Path(__file__).parent / "data" / _SAMPLE_NAME, Path(__file__).parent / _SAMPLE_NAME) if p.exists()),
              Path(__file__).parent / "data" / _SAMPLE_NAME)   # bundled Kaggle CSV (data/ folder, or next to app.py)
PAGES = ["Overview", "Sleep Patterns", "Stress Analysis", "Lifestyle Analysis", "Demographic Insights",
         "Sleep Profiles", "Compare Profiles", "Final Discoveries"]
CHART_CFG = {"displayModeBar": False}
TARGET = sd.TARGET
DURATION, STRESS, ACTIVITY = "Sleep Duration", "Stress Level", "Physical Activity Level"


def show(fig, key):
  st.plotly_chart(
      fig, theme=None, config=CHART_CFG, key=key, use_container_width=True
  )

def have(df, *cols):
    return all(c in df.columns for c in cols)


# --------------------------------------------------------------------------- data intake
@st.cache_data(show_spinner="Reading dataset…")
def parse_upload(raw: bytes):
    return sd.load(raw)


SPLASH_STEPS = ["Reading your file", "Cleaning and checking columns", "Building sleep profiles"]
DEMO_STEPS = ["Loading the demo dataset", "Cleaning and checking columns", "Building sleep profiles"]
FILTER_KEYS = ("age_", "gender_", "occ_", "rep_")       # per-dataset sidebar filter state (see sidebar_filters)
BOX_NOTE = ("How to read the boxes: the line inside is the middle value, the box holds the middle half of people, "
            "the thin lines reach the usual range, and any dots are unusual values.")


def run_splash(work, steps=SPLASH_STEPS):
    """Show the branded loading screen while `work()` runs, then for a short moment per remaining step. Errors are re-raised."""
    slot, err, out = st.empty(), None, None
    for i in range(len(steps)):
        with slot:
            theme.loading_screen(i, steps)
        if i == 0:
            try:
                out = work()
            except Exception as exc:
                err = exc
        if err is not None:
            break
        time.sleep(0.55)
    slot.empty()
    if err is not None:
        raise err
    return out


def ingest(up) -> None:
    """Validate a newly uploaded file and make it the active dataset."""
    if up is None:
        return
    sig = (up.name, up.size)
    if st.session_state.get("last_sig") == sig:
        return
    st.session_state["last_sig"] = sig
    raw = up.getvalue()
    try:
        run_splash(lambda: parse_upload(raw))
    except sd.DataError as exc:
        st.session_state["upload_error"] = str(exc)
        return
    except Exception as exc:  # never crash on a weird file
        st.session_state["upload_error"] = f"Something unexpected went wrong while reading the file ({type(exc).__name__}: {exc})."
        return
    set_dataset(raw, up.name)


def set_dataset(raw: bytes, name: str, demo: bool = False) -> None:
    st.session_state.update(raw=raw, name=name, ds_id=hashlib.md5(raw).hexdigest()[:10], demo=demo)
    st.session_state.pop("upload_error", None)


def launch_demo() -> None:
    """One click: load the bundled real dataset, hide repeated records, and open the Overview page."""
    set_dataset(SAMPLE.read_bytes(), SAMPLE.name, demo=True)
    ds = st.session_state["ds_id"]
    for p in FILTER_KEYS:
        st.session_state.pop(f"{p}{ds}", None)           # start from the default age / gender / occupation filters...
    st.session_state[f"rep_{ds}"] = True                 # ...plus the demo filter: exclude repeated profiles
    st.session_state.update(page="Overview", _splash=True)


def exit_demo() -> None:
    """Leave the demo and return to the landing page (clears the dataset, filters and page choice)."""
    drop = [k for k in st.session_state if k.startswith(FILTER_KEYS)
            or k in ("raw", "name", "ds_id", "demo", "page", "last_sig", "upload_error", "_splash")]
    for k in drop:
        st.session_state.pop(k, None)


def landing() -> None:
    theme.hero_pro("What really shapes how well we sleep?",
                   "What matters more for sleep quality — stress, physical activity, or lifestyle? "
                   "Launch the demo to see the answer in one click, or upload the Sleep Health & Lifestyle dataset and let the data answer.",
                   [(str(len(PAGES)), "analysis pages"), ("2", "profile tools"), ("100%", "calculated from your file")])
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        if SAMPLE.exists():
            st.button("▶  Launch Demo", type="primary", on_click=launch_demo, key="launch_demo")
            theme.note("One click · uses the real Kaggle sleep dataset · no upload needed · exit any time")
            theme.divider_or("or use your own data")
        else:
            st.caption("The demo dataset wasn't found in the data/ folder. You can still upload your own CSV below.")
        up = st.file_uploader("Drop your CSV here", type=["csv"], key="main_up",
                              help="Kaggle: Sleep Health and Lifestyle Dataset (Sleep_health_and_lifestyle_dataset.csv)")
        ingest(up)
        if st.session_state.get("upload_error"):
            theme.callout(esc(st.session_state["upload_error"]), "We couldn't use that file", "error")
    if "raw" in st.session_state:
        st.rerun()
    theme.steps([("Start", "Launch the demo, or upload the Kaggle CSV. Column names are matched flexibly and messy values are tidied up."),
                 ("Explore", "Filter by age, gender and occupation — every number and chart updates."),
                 ("Discover", "Read findings worked out from the data, along with what they can't tell you.")])
    theme.section("Expected columns", "● marks a required column; ○ columns are optional and unlock extra charts.")
    req = set(sd.REQUIRED)
    theme.chips([("● " if c in req else "○ ") + c for c in sd.ALIASES if c != "Person ID"])


# --------------------------------------------------------------------------- sidebar filters
def reset_filters(ds_id, age, genders):
    st.session_state[f"age_{ds_id}"] = age
    st.session_state[f"gender_{ds_id}"] = genders
    st.session_state[f"occ_{ds_id}"] = []          # empty = all occupations
    st.session_state[f"rep_{ds_id}"] = False


def sidebar_filters(df_all):
    ds = st.session_state["ds_id"]
    amin, amax = int(df_all["Age"].min()), int(df_all["Age"].max())
    genders, occs = sorted(df_all["Gender"].unique()), sorted(df_all["Occupation"].unique())
    st.session_state.setdefault(f"age_{ds}", (amin, amax))
    st.session_state.setdefault(f"gender_{ds}", genders)
    st.session_state.setdefault(f"occ_{ds}", [])
    st.session_state.setdefault(f"rep_{ds}", False)

    theme.side_label("Filters")
    theme.spacer(6)
    if amin < amax:
        age = st.slider("Age range", min_value=amin, max_value=amax, key=f"age_{ds}")
    else:
        age = (amin, amax)
        st.caption(f"All participants are {amin} years old.")
    theme.spacer(14)
    if len(genders) <= 4 and hasattr(st, "segmented_control"):   # modern segmented control (Streamlit ≥ 1.40)
        g = list(st.segmented_control("Gender", genders, selection_mode="multi", key=f"gender_{ds}") or [])
    else:
        g = st.multiselect("Gender", genders, key=f"gender_{ds}")
    theme.spacer(14)
    # Drop stale selections (e.g. after switching datasets) so the widget can never hold a value outside `occs`.
    st.session_state[f"occ_{ds}"] = [x for x in st.session_state.get(f"occ_{ds}", []) if x in occs]
    o = st.multiselect("Occupation", occs, key=f"occ_{ds}", placeholder="All occupations · type to search")
    theme.spacer(10)
    n_rep = int(df_all["Repeat Profile"].sum())
    rep = st.toggle("Exclude repeated profiles", key=f"rep_{ds}",
                    help=f"{n_rep:,} records are exactly the same as an earlier one in every column except Person ID. "
                         "Switch this on to check whether the findings still hold without them.")
    theme.spacer(6)
    st.button("Reset filters", on_click=reset_filters, args=(ds, (amin, amax), genders))
    return sd.apply_filters(df_all, age, g, o or occs, rep)


# --------------------------------------------------------------------------- pages
def demo_banner(df, df_all) -> None:
    """Strip shown only in demo mode: says what is loaded and which filter is on, with an easy way out."""
    n_rep = int(df_all["Repeat Profile"].sum())
    if st.session_state.get(f"rep_{st.session_state['ds_id']}"):
        msg = (f"You're exploring the <b>real Sleep Health &amp; Lifestyle dataset</b>. "
               f"{n_rep:,} records that are exact copies of another (apart from Person ID) are hidden, leaving "
               f"<b>{len(df):,} of {len(df_all):,}</b> people in view. Change any filter in the sidebar — "
               "or switch off “Exclude repeated profiles” to see everyone.")
    else:
        msg = (f"You're exploring the <b>real Sleep Health &amp; Lifestyle dataset</b> with "
               f"<b>{len(df):,} of {len(df_all):,}</b> people in view. Use the sidebar filters to slice it any way you like.")
    c1, c2 = st.columns([5, 1], vertical_alignment="center")
    with c1:
        theme.callout(msg, "Demo mode", "good")
    with c2:
        st.button("✕ Exit demo", on_click=exit_demo, key="exit_demo_main")


def signed(r: float) -> str:
    return sd.fmt_r(r)


def group_table(g) -> None:
    t = g.rename(columns={"n": "Participants", "duration": "Avg sleep (h)", "quality": "Avg quality (out of 10)",
                          "stress": "Avg stress (out of 10)", "activity": "Avg activity (min/day)"})
    t["Participants"] = t["Participants"].astype(int)
    theme.table(t)


def go_final():
    st.session_state["page"] = "Final Discoveries"


def go_profiles():
    st.session_state["page"] = "Sleep Profiles"


def page_overview(df, df_all, report):
    contrib = sd.group_contributions(df)
    stats = [(f"{len(df):,}", "participants in view"), (f"{df['Occupation'].nunique()}", "occupations"),
             (f"{df[TARGET].mean():.1f} / 10", "average sleep quality")]
    if contrib:
        lead = contrib["table"].sort_values("alone", ascending=False).iloc[0]
        stats.append((f"{lead.alone:.0%}", f"of the differences in sleep quality explained by {lead.group.lower()} alone"))
    theme.hero_pro("What really shapes how well we sleep?",
                   "What matters more for sleep quality — stress, physical activity, or lifestyle?", stats)
    theme.kpi_grid([
        ("Avg sleep duration", f"{df[DURATION].mean():.2f} h", f"middle value {df[DURATION].median():.1f} h", "clock", df[DURATION]),
        ("Avg sleep quality", f"{df[TARGET].mean():.2f} / 10", f"middle value {df[TARGET].median():.0f}", "sleep", df[TARGET]),
        ("Avg stress level", f"{df[STRESS].mean():.2f} / 10", f"middle value {df[STRESS].median():.0f}", "stress", df[STRESS]),
        ("Avg physical activity", f"{df[ACTIVITY].mean():.0f} min/day", f"middle value {df[ACTIVITY].median():.0f}", "bolt", df[ACTIVITY]),
    ])

    theme.section("Most interesting findings", "Worked out live from your current filters. They show what goes together, not what causes what.")
    theme.finding_cards(sd.build_findings(df, contrib)[:3])

    if contrib:
        theme.section("The research question", "How much of the differences in sleep quality each group accounts for.")
        c1, c2 = st.columns([3, 2])
        with c1:
            theme.suspects(contrib["table"])
        with c2:
            theme.card("Main discovery", sd.headline(contrib))
            theme.spacer(16)
            st.button("Open Final Discoveries →", on_click=go_final, key="go_final")
            st.button("Explore sleep profiles →", on_click=go_profiles, key="go_profiles")

    theme.section("About the data")
    n = len(df_all)
    c1, c2 = st.columns(2)
    with c1:
        theme.card("The dataset", theme.bullets([
            f"<b>{n:,}</b> participants · <b>{df_all['Occupation'].nunique()}</b> occupations · ages "
            f"<b>{int(df_all['Age'].min())}–{int(df_all['Age'].max())}</b>",
            f"Source: <b>{esc(st.session_state.get('name', 'uploaded file'))}</b>",
            "Measures: sleep duration &amp; quality, stress, activity, BMI, blood pressure, heart rate, daily steps, sleep disorder",
            "Every figure on this site is calculated from this file — nothing is simulated.",
        ]))
    with c2:
        notes = [f"<b>{report['repeat_profiles']:,}</b> repeated profiles ({report['repeat_profiles'] / n:.0%}) — "
                 "exactly the same as another record in every column except Person ID"]
        notes.append("Missing values: " + (", ".join(f"{esc(k)} ({v})" for k, v in report["missing"].items()) or "none found"))
        if report["dropped_rows"]:
            notes.append(f"{report['dropped_rows']} rows dropped because key values were missing")
        if report["out_of_range"]:
            notes.append("Impossible values removed: " + ", ".join(f"{esc(k)} ({v})" for k, v in report["out_of_range"].items()))
        if report["optional_missing"]:
            notes.append("Not in file: " + esc(", ".join(report["optional_missing"])))
        theme.card("Data quality", theme.bullets(notes))

    theme.section("The big picture", "How every measure lines up with every other. Scores run from −1 (one goes up as the other goes down) "
                  "to +1 (they rise together); 0 means no link.")
    left, right = st.columns([3, 2])
    with left:
        if len(df) >= 3:
            show(viz.corr_heatmap(sd.correlation_matrix(df), "How the measures connect"), "ov_corr")
    with right:
        drivers = sd.driver_table(df)
        if not drivers.empty:
            show(viz.driver_bar(drivers, "What moves sleep quality?"), "ov_driver")
            st.caption("↑ higher values go with better sleep · ↓ higher values go with worse sleep · “by group” = a category, such as occupation.")
    if not drivers.empty:
        top = drivers.iloc[0]
        theme.callout(f"In the current view, <b>{esc(top['Factor'])}</b> lines up most closely with sleep quality "
                      f"(score {top['strength']:.2f} out of 1). That is a link, not proof of cause — see <b>Final Discoveries</b> "
                      "for the full comparison of stress, activity and lifestyle.")
        pairs = [("stress", sd.spearman(df[STRESS], df[TARGET])), ("physical activity", sd.spearman(df[ACTIVITY], df[TARGET]))]
        link = sd.spearman(df[STRESS], df[ACTIVITY])
        if all(not np.isnan(p[1]) for p in pairs) and not np.isnan(link):
            theme.callout(f"Link with sleep quality: <b>stress</b> {signed(pairs[0][1])}, <b>physical activity</b> {signed(pairs[1][1])}. "
                          f"Stress and physical activity are also linked to each other (score {signed(link)}), "
                          "which makes it hard to tell their separate roles apart.",
                          "How the factors connect")


def page_sleep(df):
    theme.page_header("Sleep Patterns", "How long and how well people sleep — use the sidebar filters to slice the sample.", eyebrow="Explore · Distributions")
    c1, c2 = st.columns(2)
    with c1:
        show(viz.histogram(df, DURATION, "Sleep duration distribution", unit=" h"), "sp_dur")
    with c2:
        show(viz.count_bar(df, TARGET, "Sleep quality distribution"), "sp_q")
    short = (df[DURATION] < 7).mean()
    good = (df[TARGET] >= 8).mean()
    theme.callout(f"The average person sleeps <b>{df[DURATION].mean():.2f} hours</b> (the person in the middle sleeps "
                  f"{df[DURATION].median():.1f}). <b>{short:.0%}</b> sleep under 7 hours, the minimum commonly recommended for adults, "
                  f"and <b>{good:.0%}</b> rate their sleep quality 8 or higher.")

    theme.section("Sleep length and sleep quality", "Do longer sleepers rate their sleep higher?")
    view = st.radio("View", ["Dot chart", "Ranges by quality score"], horizontal=True, label_visibility="collapsed", key="sp_view")
    color_opts = [c for c in ["Gender", "BMI Category", "Sleep Disorder", "Age Group"] if c in df.columns]
    if view == "Dot chart":
        color = st.selectbox("Colour by", color_opts, key="sp_color")
        show(viz.scatter(df, DURATION, TARGET, color=color, jx=0.04, jy=0.15, hover=["Occupation", "Age"],
                         title="Sleep duration vs. quality"), "sp_scatter")
        st.caption("Dots are nudged slightly so overlapping ones stay visible. Hover over a dot to see its exact values.")
    else:
        d = df.copy()
        d[TARGET] = d[TARGET].round().astype(int)
        show(viz.box(d, TARGET, DURATION, "Sleep duration for each quality score", order=sorted(d[TARGET].unique())), "sp_box")
        st.caption(BOX_NOTE)
    r = sd.spearman(df[DURATION], df[TARGET])
    if not np.isnan(r):
        theme.callout(f"{sd.plain_link('sleep duration', 'sleep quality', r)}. Both are probably self-reported, "
                      "and both can be shaped by the same things, such as stress or health.")


def page_stress(df):
    theme.page_header("Stress Analysis", "Is higher stress linked to worse sleep? Everything below is computed from the filtered data.", eyebrow="Explore · Stress")
    r = sd.spearman(df[STRESS], df[TARGET])
    gap = sd.extreme_gap(df, STRESS)
    kp = [("Stress–sleep link score", "n/a" if np.isnan(r) else signed(r), "stress vs. sleep quality" if np.isnan(r) else sd.link_label(r))]
    if gap:
        kp += [("Low-stress group", f"{gap['low_mean']:.1f} / 10", f"stress {gap['lo']:.0f} or below · {gap['n_low']} people"),
               ("High-stress group", f"{gap['high_mean']:.1f} / 10", f"stress {gap['hi']:.0f} or above · {gap['n_high']} people"),
               ("Quality gap", f"{gap['low_mean'] - gap['high_mean']:+.1f}", "low-stress minus high-stress group")]
    theme.kpi_grid(kp)

    c1, c2 = st.columns([3, 2])
    with c1:
        opts = [c for c in ["Gender", "Occupation", "BMI Category", "Sleep Disorder"] if c in df.columns]
        color = st.selectbox("Colour points by", opts, key="st_color")
        show(viz.scatter(df, STRESS, TARGET, color=color, jx=0.14, jy=0.14, hover=["Occupation", "Age"],
                         title="Stress level vs. sleep quality"), "st_scatter")
    with c2:
        g = df.groupby(STRESS)[TARGET].agg(["mean", "count"]).reset_index()
        g.columns = ["stress", "mean", "n"]
        st.write("")
        st.write("")
        show(viz.mean_bars(g, "stress", "mean", "n", "Average sleep quality by stress level", "Average sleep quality"), "st_means")
    if not np.isnan(r):
        text = f"{sd.plain_link('stress', 'sleep quality', r)}, across the {len(df):,} people in view."
        if gap:
            text += (f" People at the low end of stress (level {gap['lo']:.0f} or below) average <b>{gap['low_mean']:.1f}</b>/10 sleep quality; "
                     f"those at the high end (level {gap['hi']:.0f} or above) average <b>{gap['high_mean']:.1f}</b>/10.")
        theme.callout(text + " Dots are nudged slightly for readability; the dashed line shows the overall trend.")

    theme.section("Where people cluster", "How many people fall at each combination of stress level and sleep-quality score.")
    show(viz.heatmap_counts(df.assign(**{TARGET: df[TARGET].round().astype(int), STRESS: df[STRESS].round().astype(int)}),
                            STRESS, TARGET, "Participants by stress level and sleep quality"), "st_heat")
    if have(df, "Heart Rate"):
        rh = sd.spearman(df[STRESS], df["Heart Rate"])
        if not np.isnan(rh):
            theme.callout(f"Stress is also linked to heart rate (score {signed(rh)}), so stress overlaps with body measures — "
                          "one reason it is hard to pin down what stress alone does to sleep.", "A related pattern")


def page_lifestyle(df):
    theme.page_header("Lifestyle Analysis", "Physical activity, daily steps and body composition — and how each lines up with sleep.", eyebrow="Explore · Lifestyle")
    tabs = st.tabs(["Physical activity", "Daily steps", "BMI category"])

    with tabs[0]:
        r = sd.spearman(df[ACTIVITY], df[TARGET])
        c1, c2 = st.columns(2)
        with c1:
            show(viz.scatter(df, ACTIVITY, TARGET, color="Gender", jy=0.14, hover=["Occupation"],
                             title="Physical activity vs. sleep quality"), "lf_act")
        bm = sd.bin_means(df, ACTIVITY, TARGET)
        with c2:
            if not bm.empty:
                show(viz.mean_bars(bm, "label", "mean", "n", "Sleep quality by activity level (four equal-sized groups)", "Average sleep quality"), "lf_act_bins")
        if not np.isnan(r):
            shape = f" Splitting people into four equal-sized groups by activity, average sleep quality <b>{sd._trend_word(bm['mean'])}</b>." if len(bm) >= 3 else ""
            theme.callout(f"{sd.plain_link('physical activity', 'sleep quality', r)} (activity is measured in minutes per day).{shape} "
                          "More active people may also differ in other ways (age, job, health), so this does not show that exercise changes sleep.")

    with tabs[1]:
        if have(df, "Daily Steps"):
            r = sd.spearman(df["Daily Steps"], df[DURATION])
            c1, c2 = st.columns(2)
            with c1:
                show(viz.scatter(df, "Daily Steps", DURATION, color="Gender", jy=0.03, hover=["Occupation"],
                                 title="Daily steps vs. sleep duration"), "lf_steps")
            bm = sd.bin_means(df, "Daily Steps", DURATION)
            with c2:
                if not bm.empty:
                    show(viz.mean_bars(bm, "label", "mean", "n", "Sleep duration by daily steps (four equal-sized groups)", "Average sleep (hours)"), "lf_steps_bins")
            if not np.isnan(r):
                theme.callout(f"{sd.plain_link('daily steps', 'sleep duration', r)}. "
                              "Step counts and sleep hours are both shaped by work schedules and routines, so any link may be indirect.")
        else:
            theme.callout("This file has no <b>Daily Steps</b> column, so this chart is unavailable.", "Missing column", "warn")

    with tabs[2]:
        if have(df, "BMI Category"):
            d = df[df["BMI Category"] != "Unknown"]
            order = [b for b in sd.BMI_ORDER if b in set(d["BMI Category"])]
            c1, c2 = st.columns(2)
            with c1:
                show(viz.box(d, "BMI Category", TARGET, "Sleep quality by BMI category", order), "lf_bmi_q")
            with c2:
                show(viz.box(d, "BMI Category", DURATION, "Sleep duration by BMI category", order), "lf_bmi_d")
            st.caption(BOX_NOTE)
            g = sd.group_summary(d, "BMI Category")
            g["BMI Category"] = g["BMI Category"].astype(str)
            g = g.set_index("BMI Category").reindex(order).reset_index()
            group_table(g)
            small = [f"{esc(r['BMI Category'])} ({int(r['n'])} people)" for _, r in g.iterrows() if r["n"] < 20]
            theme.callout("The BMI groups are different sizes" + (f"; small groups: {', '.join(small)}" if small else "")
                          + ". The averages only describe each group, and for small groups they can be shaky. "
                          "BMI also goes along with age and health conditions, which this site does not adjust for.")
        else:
            theme.callout("This file has no <b>BMI Category</b> column, so this comparison is unavailable.", "Missing column", "warn")


def page_demographics(df):
    theme.page_header("Demographic Insights", "Who sleeps better? Occupation, age group and gender compared on the filtered sample.", eyebrow="Explore · Who sleeps better")
    tabs = st.tabs(["Occupation", "Age group", "Gender"])

    with tabs[0]:
        g = sd.group_summary(df, "Occupation")
        metric = st.radio("Metric", ["Sleep quality", "Sleep duration", "Stress level"], horizontal=True, key="dm_metric")
        col, label = {"Sleep quality": ("quality", "Average sleep quality"), "Sleep duration": ("duration", "Average sleep (h)"),
                      "Stress level": ("stress", "Average stress")}[metric]
        show(viz.category_bars(g, "Occupation", col, f"{metric} by occupation", label), "dm_occ")
        big = g[g["n"] >= 10]
        if len(big) >= 2:
            hi, lo = big.loc[big[col].idxmax()], big.loc[big[col].idxmin()]
            theme.callout(f"Among occupations with at least 10 people, <b>{esc(hi['Occupation'])}</b> has the highest average "
                          f"({hi[col]:.2f}) and <b>{esc(lo['Occupation'])}</b> the lowest ({lo[col]:.2f}). "
                          "Greyed bars have fewer than 10 people and should be read with caution.")
        else:
            theme.callout("Greyed bars have fewer than 10 people and should be read with caution.")

    with tabs[1]:
        g = sd.group_summary(df, "Age Group")
        show(viz.multi_bars(g, "Age Group", [("duration", "Sleep (h)"), ("quality", "Quality (1–10)"), ("stress", "Stress (1–10)")],
                            "Averages by age group"), "dm_age")
        small = [f"{r['Age Group']} ({int(r['n'])} people)" for _, r in g.iterrows() if r["n"] < 20]
        theme.callout("Age groups are simple age bands (under 30, 30–39, 40–49 and 50+). Older and younger groups may also differ in "
                      "their jobs and health, so age differences may partly reflect who is in each group."
                      + (f" Small groups: {esc(', '.join(small))}." if small else ""))

    with tabs[2]:
        if df["Gender"].nunique() < 2:
            theme.callout("Only one gender appears in the current selection. Adjust the Gender filter to compare.", "Not enough groups", "warn")
        else:
            c1, c2 = st.columns(2)
            with c1:
                show(viz.box(df, "Gender", TARGET, "Sleep quality by gender"), "dm_g_q")
            with c2:
                show(viz.box(df, "Gender", DURATION, "Sleep duration by gender"), "dm_g_d")
            st.caption(BOX_NOTE)
            group_table(sd.group_summary(df, "Gender"))
            theme.callout("Men and women in this data may also differ in their jobs and ages, so any gap here only describes the groups — "
                          "it can't be put down to gender itself.")


def _profile_lookup(df):
    """(profiles, metrics, {name: mask}) with an 'All participants' baseline for comparisons."""
    metrics = sd.profile_metrics(df)
    profs = sd.profile_defs(df)
    masks = {"All participants": df[DURATION].notna()}
    masks.update({p["name"]: p["mask"] for p in profs})
    return profs, metrics, masks


def page_profiles(df):
    theme.page_header("Sleep Profiles", "Groups of people who stand out in this data, compared with everyone else. Each group is defined from the data itself — for example, the quarter of people with the highest stress.",
                      eyebrow="Discover · Profiles")
    profs, metrics, masks = _profile_lookup(df)
    if not profs:
        theme.callout("Profiles need at least 16 people in view. Widen the sidebar filters to see them.", "Not enough data", "warn")
        return
    sums = {p["name"]: sd.profile_summary(df, p, metrics) for p in profs}

    theme.section("How the profiles differ", "Pick a measure to rank all profiles by its average.")
    opts = {m[1]: m for m in metrics}
    pick = st.radio("Measure", list(opts), horizontal=True, label_visibility="collapsed", key="pf_metric")
    col, label, unit, _ = opts[pick]
    g = pd.DataFrame([("All participants", float(df[col].mean()), len(df))] + [(n, next(r["group"] for r in s["rows"] if r["col"] == col), s["n"])
                                                                          for n, s in sums.items()],
                     columns=["profile", "value", "n"])
    show(viz.category_bars(g, "profile", "value", f"Average {label.lower()} by profile", f"{label}{unit}", min_n=8), "pf_bars")

    theme.section("Profile cards", "Each card compares a group with everyone else and points out up to three of the biggest differences on measures that weren't used to define the group.")
    cards = []
    for p in profs:
        s = sums[p["name"]]
        want = {DURATION: "Sleep", TARGET: "Quality", STRESS: "Stress", ACTIVITY: "Activity"}
        stats = [(want[r["col"]], f"{r['group']:.{r['dec']}f}", f"vs {r['rest']:.{r['dec']}f}") for r in s["rows"] if r["col"] in want]
        body = ("Compared with everyone else: " + "; ".join(esc(x) for x in s["notes"]) + "."
                if s["notes"] else "No notable differences from everyone else on the measures that did not define this group.")
        meta = []
        if s["top_occ"]:
            meta.append(f"Most common occupation: <b>{esc(s['top_occ'][0])}</b> ({s['top_occ'][1]} of {s['n']})")
        if s["disorder"] is not None and p["key"] != "disorder":
            meta.append(f"{s['disorder']:.0%} have a recorded sleep disorder")
        cards.append(dict(name=p["name"], rule=p["rule"], n_text=f"{s['n']} people · {s['share']:.0%}", stats=stats,
                          body=body, meta=" · ".join(meta)))
    theme.profile_cards(cards)
    theme.callout("One person can belong to several profiles, and the profiles come from this data, so they describe who stands out here — "
                  "not why. <b>They show what goes together, not what causes what.</b> Small groups can be unreliable.",
                  "How to read profiles", "good")
    st.button("Compare two profiles →", on_click=lambda: st.session_state.update(page="Compare Profiles"), key="pf_to_cmp")


def page_compare(df):
    theme.page_header("Compare Two Profiles", "Put two groups side by side on sleep, stress, activity and body measures.", eyebrow="Discover · Compare")
    profs, metrics, masks = _profile_lookup(df)
    if not profs:
        theme.callout("Profiles need at least 16 people in view. Widen the sidebar filters to compare them.", "Not enough data", "warn")
        return
    names = list(masks)
    for k in ("cp_a", "cp_b"):                       # filters can remove a profile: never keep a stale choice
        if st.session_state.get(k) not in names:
            st.session_state.pop(k, None)
    pref = {"cp_a": "High-stress sleepers", "cp_b": "Low-stress sleepers"}
    c1, c2 = st.columns(2)
    with c1:
        na = st.selectbox("Profile A", names, index=names.index(pref["cp_a"]) if pref["cp_a"] in names else 0, key="cp_a")
    with c2:
        nb = st.selectbox("Profile B", names, index=names.index(pref["cp_b"]) if pref["cp_b"] in names else min(1, len(names) - 1), key="cp_b")
    if na == nb:
        theme.callout("Choose two different profiles to compare.", "Same profile selected", "warn")
        return
    ma, mb = masks[na], masks[nb]
    rows, both = sd.compare_profiles(df, ma, mb, metrics)
    rule = {p["name"]: p["rule"] for p in profs} | {"All participants": "Everyone in the current view"}
    theme.kpi_grid([(f"A · {na}", f"{int(ma.sum()):,} people", rule[na], "people"),
                    (f"B · {nb}", f"{int(mb.sum()):,} people", rule[nb], "people")])

    theme.section("Side by side", "The average for each profile. “Size of difference” says whether the gap is tiny or large compared with how much people vary within the groups.")
    theme.compare_table(rows, na, nb)
    theme.spacer(10)
    show(viz.compare_bars(rows, na, nb, "Profile averages"), "cp_bars")
    show(viz.compare_dist(df, ma, mb, na, nb, TARGET, "Sleep quality distribution (% of each profile)"), "cp_dist")

    ranked = rows.assign(abs_d=rows["d"].abs()).dropna(subset=["abs_d"]).sort_values("abs_d", ascending=False)
    if not ranked.empty:
        top = ranked.iloc[0]
        hi = na if top["diff"] > 0 else nb
        notes = [f"The largest difference is in <b>{esc(top['label'].lower())}</b>: {esc(na)} averages {top['a']:.{int(top['dec'])}f}{esc(top['unit'])} "
                 f"vs {top['b']:.{int(top['dec'])}f}{esc(top['unit'])} for {esc(nb)} (a {sd.effect_word(top['d'])} gap, higher for {esc(hi)})."]
        small = [r.label.lower() for r in ranked.itertuples() if r.abs_d < 0.2]
        if small:
            notes.append("Almost no difference in: " + ", ".join(esc(x) for x in small) + ".")
        if both:
            notes.append(f"<b>{both:,}</b> people belong to both profiles, so the two groups overlap.")
        theme.callout(theme.bullets(notes), "What stands out")
    theme.callout("These differences show what goes together in this data. They do <b>not</b> show that stress, activity or any other trait "
                  "causes better or worse sleep. The groups are not matched on age, occupation or other factors.", "How to read this", "good")


def page_final(df, df_all, report):
    theme.page_header("Final Discoveries", "Research question: what matters more for sleep quality — stress, physical activity, or lifestyle?", eyebrow="Answer · Evidence & limits")
    contrib = sd.group_contributions(df)
    findings = sd.build_findings(df, contrib)
    if contrib:
        v1, v2 = st.columns([2, 3])
        with v1:
            theme.suspects(contrib["table"], "The verdict", "How much of the differences in sleep quality each group accounts for on its own")
        with v2:
            theme.card("In one line", sd.headline(contrib))
    theme.finding_cards(findings)

    c1, c2 = st.columns(2)
    drivers = sd.driver_table(df)
    with c1:
        if not drivers.empty:
            show(viz.driver_bar(drivers, "How closely each factor lines up with sleep quality"), "fd_driver")
    with c2:
        if contrib:
            show(viz.contribution_bar(contrib["table"], "How much each group accounts for"), "fd_contrib")
    if contrib:
        defs = "; ".join(f"<b>{esc(r.group)}</b> = {esc(r.factors)}" for r in contrib["table"].itertuples())
        theme.callout(f"Groups: {defs}. “On its own” is how much of the differences in sleep quality a group could account for if it were "
                      "the only thing we knew. “Only this group” is how much would be lost if we took that group away but kept the other two. "
                      "When the groups overlap, “only this group” is smaller than “on its own”.", "How to read these")

    nr = df[~df["Repeat Profile"]]
    if contrib and report["repeat_profiles"] and len(nr) != len(df) and len(nr) >= 30:
        c2 = sd.group_contributions(nr)
        if c2:
            t = c2["table"].sort_values("alone", ascending=False)
            parts = ", ".join(f"{esc(r.group)} {r.alone:.0%}" for r in t.itertuples())
            theme.callout(f"Without the repeated profiles ({len(nr):,} of {len(df):,} people), the “on its own” shares are: {parts}. "
                          f"{sd.same_leader(contrib, c2)}", "Robustness check", "good")

    theme.section("What the data suggests")
    theme.callout("The findings above describe <b>what goes together in this sample</b>. They show which measures line up most closely "
                  "with sleep quality, not what would happen if someone changed their stress or activity. <b>A link is not proof of cause.</b> "
                  "Link scores run from −1 to +1: the closer to either end, the stronger the link; 0 means no link.",
                  "How to read this", "good")

    theme.section("Limitations")
    theme.callout(theme.bullets(sd.limitations(report, df_all, df)), "Keep in mind", "warn")

    with st.expander("How these numbers are calculated (technical notes)"):
        st.markdown(
            "- **Link score** = Spearman rank correlation (ρ), from −1 to +1. For categories such as occupation or gender we use the "
            "correlation ratio (η), from 0 to 1, so those bars have no direction.\n"
            "- **“Accounts for”** = the R² of a linear model for sleep quality, using each group alone (“on its own”) and the drop in R² when "
            "the group is removed from the full model (“only this group”). Lifestyle = daily steps, BMI category and heart rate.\n"
            "- **Size of difference** (Compare Profiles) = Cohen’s d, the gap between two averages divided by their pooled standard deviation. "
            "Under 0.2 is called tiny, 0.2–0.5 small, 0.5–0.8 medium, above 0.8 large. Hover over a label to see the exact value.\n"
            "- **Repeated profiles** are records identical on every column except Person ID.\n"
            "- **Equal-sized groups** are quartiles. **Dots** in scatter charts are jittered for display only; hover shows true values.")

    theme.section("Take the data with you")
    st.download_button("Download filtered dataset (CSV)", data=export_csv(df), file_name="somnia_filtered.csv",
                       mime="text/csv", key="dl_final")


def export_csv(df) -> bytes:
    return df.drop(columns=["BMI Score"], errors="ignore").to_csv(index=False).encode("utf-8")


# --------------------------------------------------------------------------- main
def main():
    theme.inject_css()
    with st.sidebar:
        theme.brand()
        if "raw" not in st.session_state:
            theme.spacer(16)
            st.caption("Launch the demo or upload a CSV to unlock the dashboard.")
        else:
            theme.side_label("Workspace")
            theme.spacer(4)
            page = st.radio("Navigate", PAGES, key="page", label_visibility="collapsed")
            filters_slot = st.container()          # filled once the data is parsed (keeps filters above the dataset card)
            theme.spacer(10)
            theme.side_label("Dataset")
            theme.spacer(4)
            card_slot = st.container()
            theme.spacer(8)
            with st.expander("Replace dataset"):
                ingest(st.file_uploader("Upload a new file (.csv)", type=["csv"], key="side_up", label_visibility="collapsed"))

    if "raw" not in st.session_state:
        landing()
        return

    try:
        if st.session_state.pop("_splash", False):
            run_splash(lambda: parse_upload(st.session_state["raw"]), DEMO_STEPS)
        df_all, report = parse_upload(st.session_state["raw"])
    except sd.DataError as exc:  # should not happen (validated on upload) but never crash
        st.session_state.pop("raw")
        st.session_state["upload_error"] = str(exc)
        st.rerun()
        return

    with filters_slot:
        df = sidebar_filters(df_all)
    with card_slot:
        theme.dataset_card(st.session_state.get("name", "uploaded.csv"), len(df_all), len(df),
                           len([c for c in df_all.columns if c in sd.ALIASES]))
        theme.spacer(16)
        st.download_button("Download filtered data (.csv)", data=export_csv(df), file_name="somnia_filtered.csv",
                           mime="text/csv", key="dl_side")

    err = st.session_state.pop("upload_error", None)
    if err:
        theme.callout(esc(err) + " The previous dataset is still loaded.", "The new file couldn't be used", "error")

    if st.session_state.get("demo"):
        demo_banner(df, df_all)
    theme.chips([f"{len(df):,} of {len(df_all):,} participants in view"])
    if df.empty:
        theme.callout("No records match the current filters. Select at least one gender, widen the age range, "
                      "or press <b>Reset filters</b>.", "Nothing to show", "warn")
        return

    {"Overview": lambda: page_overview(df, df_all, report), "Sleep Patterns": lambda: page_sleep(df),
     "Stress Analysis": lambda: page_stress(df), "Lifestyle Analysis": lambda: page_lifestyle(df),
     "Demographic Insights": lambda: page_demographics(df),
     "Sleep Profiles": lambda: page_profiles(df), "Compare Profiles": lambda: page_compare(df),
     "Final Discoveries": lambda: page_final(df, df_all, report)}[page]()


main()