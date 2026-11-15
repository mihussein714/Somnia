"""Reusable Plotly figures with one consistent dark, glassy style."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PALETTE = ["#8B5CF6", "#3B82F6", "#22D3EE", "#F472B6", "#FBBF24", "#34D399", "#FB7185", "#A78BFA"]
INK, MUTED, GRID = "#E7EAF6", "#9AA3C0", "rgba(255,255,255,.07)"
GRADIENT = [[0, "#3B82F6"], [1, "#8B5CF6"]]
GROUP_COLORS = {"Stress": "#F472B6", "Physical activity": "#22D3EE",
                "Lifestyle & body profile": "#8B5CF6", "Context": "#64748B"}


def style(fig, height=380, title=None, legend=True):
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=INK, size=13), colorway=PALETTE,
        margin=dict(l=16, r=16, t=(88 if legend else 56) if title else (48 if legend else 20), b=28), showlegend=legend,
        hoverlabel=dict(bgcolor="#141B34", bordercolor="rgba(139,92,246,.7)", font=dict(color=INK)),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, title_text="", font=dict(size=12)))
    if title:
        fig.update_layout(title=dict(text=title, x=0.02, xanchor="left", y=0.97, yanchor="top", yref="container", font=dict(size=16)))
    fig.update_layout(bargap=0.28, hovermode="closest")
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, automargin=True,
                     title_font=dict(size=12, color=MUTED), tickfont=dict(size=12, color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, automargin=True,
                     title_font=dict(size=12, color=MUTED), tickfont=dict(size=12, color=MUTED))
    try:  # rounded bars need a recent Plotly; silently skip on older versions
        fig.update_traces(marker_cornerradius=6, selector=dict(type="bar"))
    except Exception:
        pass
    return fig


def histogram(df, col, title, nbins=None, color=PALETTE[0], unit=""):
    fig = go.Figure(go.Histogram(x=df[col], nbinsx=nbins, marker=dict(color=color, line=dict(color="rgba(255,255,255,.3)", width=1)),
                                 opacity=.9, hovertemplate=f"{col}: %{{x}}<br>Count: %{{y}}<extra></extra>"))
    mean = df[col].mean()
    fig.add_vline(x=mean, line_dash="dash", line_color=PALETTE[2], annotation_text=f"mean {mean:.2f}{unit}",
                  annotation_position="top right", annotation_font_color=PALETTE[2])
    fig.update_yaxes(title_text="Participants")
    fig.update_xaxes(title_text=col)
    return style(fig, 360, title, legend=False)


def count_bar(df, col, title):
    c = df[col].round().astype(int).value_counts().sort_index()
    fig = go.Figure(go.Bar(x=c.index.astype(str), y=c.values, text=c.values, textposition="outside",
                           marker=dict(color=c.values, colorscale=GRADIENT, line=dict(width=0)),
                           hovertemplate=f"{col} %{{x}}<br>Participants: %{{y}}<extra></extra>"))
    fig.update_xaxes(title_text=col, type="category")
    fig.update_yaxes(title_text="Participants")
    return style(fig, 360, title, legend=False)


def scatter(df, x, y, color=None, jx=0.0, jy=0.0, hover=(), title=None, height=420, trend=True):
    """Scatter with optional jitter (display only; hover shows the true values) and a linear trend line."""
    d = df.dropna(subset=[x, y]).copy()
    rng = np.random.default_rng(7)
    d["_x"] = d[x] + (rng.uniform(-jx, jx, len(d)) if jx else 0)
    d["_y"] = d[y] + (rng.uniform(-jy, jy, len(d)) if jy else 0)
    hd = {"_x": False, "_y": False}
    hd.update({c: True for c in [x, y, *hover] if c in d.columns})
    fig = px.scatter(d, x="_x", y="_y", color=color if color in d.columns else None, hover_data=hd,
                     color_discrete_sequence=PALETTE, opacity=.55, labels={"_x": x, "_y": y})
    fig.update_traces(marker=dict(size=6, line=dict(width=.4, color="rgba(255,255,255,.25)")))
    if trend and d[x].nunique() > 1 and len(d) > 2:
        slope, icpt = np.polyfit(d[x], d[y], 1)
        xs = np.array([d[x].min(), d[x].max()])
        fig.add_trace(go.Scatter(x=xs, y=slope * xs + icpt, mode="lines", name="Linear trend",
                                 line=dict(color="#FBBF24", width=2.5, dash="dash"), hoverinfo="skip"))
    fig.update_xaxes(title_text=x)
    fig.update_yaxes(title_text=y)
    return style(fig, height, title)


def mean_bars(g, label, mean, n, title, ytitle):
    """Bars of a mean per category/bin with n in the hover."""
    fig = go.Figure(go.Bar(x=g[label].astype(str), y=g[mean], customdata=g[n], text=g[mean].round(2), textposition="outside",
                           marker=dict(color=g[mean], colorscale=GRADIENT, line=dict(width=0)),
                           hovertemplate="%{x}<br>Mean: %{y:.2f}<br>n = %{customdata}<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text=ytitle, rangemode="tozero")
    return style(fig, 380, title, legend=False)


def heatmap_counts(df, x, y, title):
    ct = pd.crosstab(df[y], df[x])
    fig = go.Figure(go.Heatmap(z=ct.values, x=ct.columns.astype(str), y=ct.index.astype(str), text=ct.values,
                               texttemplate="%{text}", colorscale=[[0, "rgba(59,130,246,.05)"], [.5, "#3B82F6"], [1, "#8B5CF6"]],
                               hovertemplate=f"{x}: %{{x}}<br>{y}: %{{y}}<br>Participants: %{{z}}<extra></extra>", showscale=False))
    fig.update_xaxes(title_text=x, type="category")
    fig.update_yaxes(title_text=y, type="category")
    return style(fig, 380, title, legend=False)


def corr_heatmap(corr, title):
    fig = go.Figure(go.Heatmap(z=corr.values, x=list(corr.columns), y=list(corr.index), zmin=-1, zmax=1,
                               text=corr.round(2).values, texttemplate="%{text}",
                               colorscale=[[0, "#F472B6"], [.5, "#141B34"], [1, "#22D3EE"]],
                               hovertemplate="%{y} × %{x}<br>ρ = %{z:.2f}<extra></extra>",
                               colorbar=dict(title="ρ", thickness=10)))
    fig.update_yaxes(autorange="reversed")
    return style(fig, 430, title, legend=False)


def driver_bar(drivers, title):
    d = drivers.sort_values("strength")
    colors = [GROUP_COLORS.get(g, "#64748B") for g in d["Group"]]
    labels = [f"{s:.2f}" + (" (η)" if np.isnan(r) else (" ↓" if r < 0 else " ↑")) for s, r in zip(d["strength"], d["r"])]
    fig = go.Figure(go.Bar(y=d["Factor"], x=d["strength"], orientation="h", marker=dict(color=colors), text=labels,
                           textposition="outside", customdata=np.stack([d["Group"], d["Method"]], axis=-1),
                           hovertemplate="%{y}<br>Strength: %{x:.2f}<br>%{customdata[0]} · %{customdata[1]}<extra></extra>"))
    fig.update_xaxes(title_text="Association strength with sleep quality (0–1)", range=[0, min(1.15, max(0.4, d["strength"].max() * 1.25))])
    return style(fig, 400, title, legend=False)


def contribution_bar(table, title):
    t = table.sort_values("alone", ascending=False)
    fig = go.Figure()
    fig.add_bar(x=t["group"], y=t["alone"], name="Explains on its own", marker_color=PALETTE[0],
                hovertemplate="%{x}<br>On its own: %{y:.1%}<extra></extra>")
    fig.add_bar(x=t["group"], y=t["unique"], name="Unique (beyond the others)", marker_color=PALETTE[2],
                hovertemplate="%{x}<br>Unique: %{y:.1%}<extra></extra>")
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Share of variation in sleep quality", tickformat=".0%", rangemode="tozero")
    return style(fig, 400, title)


def category_bars(g, cat, val, title, xtitle, min_n=10, height=420):
    """Horizontal sorted bars; categories with n < min_n are greyed out."""
    g = g.sort_values(val)
    colors = [("#8B5CF6" if n >= min_n else "#4B5675") for n in g["n"]]
    fig = go.Figure(go.Bar(y=g[cat].astype(str), x=g[val], orientation="h", marker=dict(color=colors), customdata=g["n"],
                           text=g[val].round(2), textposition="outside",
                           hovertemplate="%{y}<br>Mean: %{x:.2f}<br>n = %{customdata}<extra></extra>"))
    fig.update_xaxes(title_text=xtitle, rangemode="tozero")
    return style(fig, max(height, 60 + 34 * len(g)), title, legend=False)


def multi_bars(g, cat, metrics, title):
    """metrics: [(column, label)] — small multiples of means per category."""
    fig = make_subplots(rows=1, cols=len(metrics), subplot_titles=[m[1] for m in metrics], horizontal_spacing=.09)
    for i, (col, _) in enumerate(metrics, 1):
        fig.add_trace(go.Bar(x=g[cat].astype(str), y=g[col], customdata=g["n"], text=g[col].round(1), textposition="outside",
                             marker_color=PALETTE[(i - 1) % len(PALETTE)],
                             hovertemplate="%{x}<br>Mean: %{y:.2f}<br>n = %{customdata}<extra></extra>"), row=1, col=i)
    fig.update_yaxes(rangemode="tozero")
    return style(fig, 380, title, legend=False)


def box(df, x, y, title, order=None, height=380):
    d = df.dropna(subset=[x, y]).copy()
    d[x] = d[x].astype(str)
    fig = px.box(d, x=x, y=y, color=x, color_discrete_sequence=PALETTE, points="outliers",
                 category_orders={x: [str(o) for o in order]} if order else None)
    return style(fig, height, title, legend=False)


def compare_bars(rows, name_a, name_b, title=None):
    """Small multiples: one panel per metric, two bars (profile A vs B). rows: sleepdata.compare_profiles output."""
    n = len(rows)
    cols = min(4, n)
    nrows = -(-n // cols)
    fig = make_subplots(rows=nrows, cols=cols, subplot_titles=list(rows["label"]), horizontal_spacing=.07, vertical_spacing=.24)
    for i, r in enumerate(rows.itertuples()):
        for nm, val, color in ((name_a, r.a, PALETTE[0]), (name_b, r.b, PALETTE[2])):
            fig.add_trace(go.Bar(x=[nm], y=[val], name=nm, marker_color=color, text=[f"{val:,.{r.dec}f}"], textposition="outside",
                                 cliponaxis=False, showlegend=(i == 0), legendgroup=nm,
                                 hovertemplate=f"{nm}<br>{r.label}: %{{y:,.{r.dec + 1}f}}{r.unit}<extra></extra>"),
                          row=i // cols + 1, col=i % cols + 1)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(barmode="group")
    style(fig, 250 * nrows + 100, title)
    # subplot titles sit just above the plots, so lift the legend onto the chart-title row (right-aligned)
    fig.update_layout(margin=dict(t=100), legend=dict(yref="container", y=0.97, yanchor="top", xanchor="right", x=1))
    return fig


def compare_dist(df, ma, mb, name_a, name_b, col, title):
    """% of each profile at every (rounded) score of `col` — comparable even when the profiles differ in size."""
    levels = sorted(df[col].round().astype(int).unique())
    fig = go.Figure()
    for nm, m, color in ((name_a, ma, PALETTE[0]), (name_b, mb, PALETTE[2])):
        c = df.loc[m, col].round().astype(int).value_counts(normalize=True).reindex(levels, fill_value=0) * 100
        fig.add_bar(x=[str(l) for l in levels], y=c.values, name=nm, marker_color=color,
                    hovertemplate=f"{nm}<br>{col} %{{x}}: %{{y:.0f}}% of this profile<extra></extra>")
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text=col, type="category")
    fig.update_yaxes(title_text="% of profile", rangemode="tozero")
    return style(fig, 380, title)