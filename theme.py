"""Design system: custom CSS + small HTML components (glass cards, KPIs, callouts)."""
from __future__ import annotations

from html import escape as esc
from urllib.parse import quote

import numpy as np
import streamlit as st

ACCENTS = ["#8B5CF6", "#3B82F6", "#22D3EE", "#F472B6"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--panel:rgba(255,255,255,.045);--line:rgba(255,255,255,.09);--text:#E7EAF6;--muted:#9AA3C0;
      --purple:#8B5CF6;--blue:#3B82F6;--cyan:#22D3EE;--pink:#F472B6;}
.stApp,.stApp p,.stApp label,.stApp button,.stApp input,.stApp li,.stApp h1,.stApp h2,.stApp h3,.stApp h4{
  font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;}
.stApp{color:var(--text);
  background:radial-gradient(1100px 560px at 6% -8%,rgba(139,92,246,.24),transparent 60%),
             radial-gradient(900px 520px at 100% 0%,rgba(59,130,246,.18),transparent 55%),
             radial-gradient(700px 500px at 60% 110%,rgba(34,211,238,.07),transparent 60%),#0B0F19;}
header[data-testid="stHeader"]{background:transparent;height:2.25rem !important;min-height:0 !important;}
#MainMenu,footer,.stDeployButton,.stAppDeployButton,[data-testid="stMainMenu"],[data-testid="stToolbarActions"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{visibility:hidden !important;display:none !important;}
[data-testid="stSidebarCollapsedControl"],[data-testid="stExpandSidebarButton"],[data-testid="collapsedControl"],[data-testid="stSidebarCollapseButton"]{display:flex !important;visibility:visible !important;opacity:1 !important;z-index:1000150 !important;}
[data-testid="stSidebarCollapsedControl"] button,[data-testid="stExpandSidebarButton"],[data-testid="collapsedControl"] button{background:rgba(139,92,246,.22) !important;border:1px solid rgba(139,92,246,.55) !important;border-radius:12px !important;color:#E7EAF6 !important;}
header[data-testid="stHeader"]{z-index:1000100 !important;pointer-events:none;}
header[data-testid="stHeader"] *{pointer-events:auto;}
footer{height:0;}
.block-container{padding-top:.75rem !important;padding-bottom:4rem;max-width:1280px;}
h1,h2,h3,h4{letter-spacing:-.02em;}

/* sidebar */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0F1530 0%,#0B0F19 100%);border-right:1px solid var(--line);}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:.2rem;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label{padding:.55rem .8rem;border-radius:12px;
  border:1px solid transparent;transition:all .2s ease;width:100%;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:hover{background:rgba(139,92,246,.13);transform:translateX(2px);}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:has(input:checked){
  background:linear-gradient(135deg,rgba(124,58,237,.38),rgba(59,130,246,.26));border-color:rgba(139,92,246,.55);}
.brand{display:flex;align-items:center;gap:.7rem;margin:.2rem 0 1.1rem;}
.brand-logo{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font-size:1.15rem;
  background:linear-gradient(135deg,#7C3AED,#3B82F6);box-shadow:0 8px 24px rgba(124,58,237,.45);}
.brand-name{font-weight:800;font-size:1.05rem;line-height:1.1;}
.brand-sub{color:var(--muted);font-size:.72rem;}
.side-label{color:var(--muted);font-size:.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin:1.1rem 0 .35rem;}

/* hero */
.hero{padding:2.2rem 2.4rem;border-radius:26px;margin-bottom:1.1rem;position:relative;overflow:hidden;
  background:linear-gradient(135deg,rgba(124,58,237,.22),rgba(59,130,246,.12) 55%,rgba(34,211,238,.07));
  border:1px solid rgba(139,92,246,.3);box-shadow:0 20px 60px rgba(8,10,30,.55);}
.hero:after{content:"";position:absolute;right:-80px;top:-80px;width:300px;height:300px;border-radius:50%;
  background:radial-gradient(circle,rgba(139,92,246,.35),transparent 65%);}
.eyebrow{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:#C4B5FD;background:rgba(139,92,246,.16);border:1px solid rgba(139,92,246,.35);padding:.25rem .7rem;border-radius:999px;}
.hero h1{font-size:3.2rem;font-weight:800;margin:.7rem 0 .4rem;line-height:1.05;
  background:linear-gradient(90deg,#fff,#C4B5FD 55%,#7DD3FC);-webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;}
.hero p{color:#B6BED8;font-size:1.05rem;max-width:720px;margin:0;line-height:1.55;position:relative;z-index:1;}
.page-title{font-size:2rem;font-weight:800;margin:.2rem 0 .2rem;}
.page-sub{color:var(--muted);margin:0 0 1rem;max-width:760px;line-height:1.5;}
.section{margin:1.6rem 0 .6rem;}
.section h3{margin:0;font-size:1.15rem;font-weight:700;}
.section p{margin:.15rem 0 0;color:var(--muted);font-size:.9rem;}

/* chips */
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin:.2rem 0 1rem;}
.chip{font-size:.78rem;color:#C9D0EA;background:var(--panel);border:1px solid var(--line);padding:.3rem .75rem;border-radius:999px;}

/* KPI */
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1rem;margin:.4rem 0 1rem;}
.kpi{position:relative;padding:1.15rem 1.3rem;border-radius:20px;background:var(--panel);border:1px solid var(--line);
  backdrop-filter:blur(14px);box-shadow:0 10px 30px rgba(5,8,25,.4);transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease;overflow:hidden;}
.kpi:before{content:"";position:absolute;left:0;top:0;right:0;height:3px;background:linear-gradient(90deg,var(--accent),transparent);}
.kpi:hover{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 16px 40px rgba(5,8,25,.55);}
.kpi-label{color:var(--muted);font-size:.78rem;font-weight:600;letter-spacing:.05em;text-transform:uppercase;}
.kpi-value{font-size:2.1rem;font-weight:800;margin:.25rem 0 .1rem;letter-spacing:-.03em;}
.kpi-sub{color:#8C95B3;font-size:.8rem;}

/* cards, callouts, findings */
.card,.callout,.finding{background:var(--panel);border:1px solid var(--line);border-radius:18px;backdrop-filter:blur(14px);
  box-shadow:0 10px 30px rgba(5,8,25,.35);}
.card{padding:1.2rem 1.4rem;height:100%;transition:border-color .25s ease,transform .25s ease;}
.card:hover{border-color:rgba(139,92,246,.45);transform:translateY(-2px);}
.card h4{margin:0 0 .5rem;font-size:1rem;}
.card ul{margin:.2rem 0 0;padding-left:1.1rem;color:#C0C7E0;font-size:.9rem;line-height:1.6;}
.card p{color:#C0C7E0;font-size:.92rem;line-height:1.6;margin:0 0 .4rem;}
.callout{padding:.95rem 1.2rem;margin:.6rem 0 1rem;border-left:3px solid var(--purple);border-radius:14px;}
.callout.warn{border-left-color:#FBBF24;}.callout.error{border-left-color:#FB7185;}.callout.good{border-left-color:#34D399;}
.callout-title{font-size:.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A5B0D6;margin-bottom:.25rem;}
.callout div:last-child{color:#CDD3EA;font-size:.93rem;line-height:1.6;}
.callout b,.card b,.finding b{color:#fff;}
.find-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1rem;margin:.4rem 0 1rem;}
.finding{padding:1.2rem 1.4rem;transition:transform .25s ease,border-color .25s ease;}
.finding:hover{transform:translateY(-3px);border-color:rgba(139,92,246,.5);}
.finding.lead{grid-column:1/-1;background:linear-gradient(135deg,rgba(124,58,237,.2),rgba(59,130,246,.1));border-color:rgba(139,92,246,.4);}
.finding h4{margin:.5rem 0 .35rem;font-size:1.05rem;}
.finding p{margin:0;color:#C0C7E0;line-height:1.6;font-size:.93rem;}
.tag{font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C4B5FD;
  background:rgba(139,92,246,.16);padding:.2rem .6rem;border-radius:999px;}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin-top:1.2rem;}
.step-n{width:30px;height:30px;border-radius:10px;display:grid;place-items:center;font-weight:800;margin-bottom:.6rem;
  background:linear-gradient(135deg,#7C3AED,#3B82F6);}

/* Streamlit widgets */
div[data-testid="stPlotlyChart"]{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:10px 10px 4px;
  backdrop-filter:blur(14px);box-shadow:0 10px 30px rgba(5,8,25,.4);transition:border-color .25s ease,box-shadow .25s ease;}
div[data-testid="stPlotlyChart"]:hover{border-color:rgba(139,92,246,.45);box-shadow:0 16px 44px rgba(5,8,25,.55);}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;}
.stButton>button,.stDownloadButton>button{background:linear-gradient(135deg,#7C3AED,#3B82F6);color:#fff;border:0;border-radius:12px;
  padding:.55rem 1.1rem;font-weight:600;box-shadow:0 8px 22px rgba(99,70,240,.35);transition:transform .2s ease,box-shadow .2s ease;}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(99,70,240,.5);color:#fff;}
section[data-testid="stSidebar"] .stButton>button{background:rgba(255,255,255,.06);border:1px solid var(--line);box-shadow:none;width:100%;}
div[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.04);border:1.5px dashed rgba(139,92,246,.55);border-radius:16px;}
button[role="tab"]{font-weight:600;}
div[data-baseweb="tab-list"]{gap:.4rem;}
@media (max-width:760px){.hero{padding:1.4rem 1.3rem;}.hero h1{font-size:2.2rem;}.page-title{font-size:1.6rem;}}
</style>
"""



# Consistent stroke icons (24x24, Lucide-style). Used in navigation, KPI cards and the dataset card.
ICONS = {
    "overview": "<rect x='3' y='3' width='7' height='9' rx='1'/><rect x='14' y='3' width='7' height='5' rx='1'/><rect x='14' y='12' width='7' height='9' rx='1'/><rect x='3' y='16' width='7' height='5' rx='1'/>",
    "sleep": "<path d='M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z'/>",
    "stress": "<path d='M22 12h-4l-3 9L9 3l-3 9H2'/>",
    "lifestyle": "<path d='M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7Z'/>",
    "people": "<path d='M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2'/><circle cx='9' cy='7' r='4'/><path d='M22 21v-2a4 4 0 0 0-3-3.9'/><path d='M16 3.1a4 4 0 0 1 0 7.8'/>",
    "search": "<circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/>",
    "clock": "<circle cx='12' cy='12' r='9'/><path d='M12 7v5l3 2'/>",
    "star": "<path d='m12 3 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.8 6.2 20.9l1.1-6.5L2.6 9.8l6.5-.9Z'/>",
    "bolt": "<path d='M13 2 3 14h9l-1 8 10-12h-9Z'/>",
    "compare": "<path d='M8 3 4 7l4 4'/><path d='M4 7h16'/><path d='m16 21 4-4-4-4'/><path d='M20 17H4'/>",
    "file": "<path d='M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z'/><path d='M14 3v5h5'/>",
}
NAV_ICONS = ["overview", "sleep", "stress", "lifestyle", "people", "star", "compare", "search"]  # same order as PAGES in app.py


def svg(name: str, size: int = 18) -> str:
    return (f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
            f"stroke-linecap='round' stroke-linejoin='round'>{ICONS[name]}</svg>")


def _mask(name: str) -> str:
    uri = ("data:image/svg+xml;utf8," + quote(
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8' "
        f"stroke-linecap='round' stroke-linejoin='round'>{ICONS[name]}</svg>"))
    return f'url("{uri}") center/contain no-repeat'


SIDEBAR_CSS = """
<style>
/* ---- sidebar: narrow, compact, premium ---- */
section[data-testid="stSidebar"][aria-expanded="true"]{width:276px !important;min-width:276px !important;}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{padding:1.1rem .9rem .8rem;}
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"]{gap:.45rem;}
section[data-testid="stSidebar"] label p{font-size:.78rem;color:var(--muted);font-weight:500;}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:.15rem;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label{padding:.5rem .7rem;border-radius:12px;display:flex;align-items:center;gap:.65rem;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label>div:first-child{display:none;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label p{font-size:.9rem;font-weight:500;color:#B8C0DC;margin:0;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:hover p{color:#fff;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label::before{content:"";width:18px;height:18px;flex:none;background:#8B93B3;transition:background .2s ease;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:hover::before{background:#C4B5FD;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:has(input:checked){
  background:linear-gradient(135deg,rgba(124,58,237,.34),rgba(99,102,241,.16));border-color:rgba(139,92,246,.5);
  box-shadow:inset 3px 0 0 #8B5CF6;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:has(input:checked) p{color:#fff;font-weight:600;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label:has(input:checked)::before{background:#C4B5FD;}
__NAVICONS__
.side-label{margin:.9rem 0 .15rem;display:flex;align-items:center;gap:.5rem;}
.side-label:after{content:"";flex:1;height:1px;background:var(--line);}
.brand{padding-bottom:.3rem;margin-bottom:.2rem;}
.brand-logo{color:#fff;}
.ds-card{padding:.7rem .8rem;border-radius:14px;background:rgba(255,255,255,.045);border:1px solid var(--line);}
.ds-row{display:flex;gap:.6rem;align-items:center;}
.ds-ico{width:32px;height:32px;border-radius:10px;display:grid;place-items:center;color:#C4B5FD;background:rgba(139,92,246,.16);flex:none;}
.ds-name{font-size:.82rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:170px;}
.ds-meta{font-size:.72rem;color:var(--muted);}
.ds-status{margin-top:.55rem;font-size:.72rem;color:#A7F3D0;display:flex;align-items:center;gap:.4rem;}
.dot{width:7px;height:7px;border-radius:50%;background:#34D399;box-shadow:0 0 0 3px rgba(52,211,153,.18);}
section[data-testid="stSidebar"] details{border:1px solid var(--line);border-radius:12px;background:rgba(255,255,255,.03);}
section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzone"]{padding:.7rem;}
section[data-testid="stSidebar"] [data-baseweb="tag"]{background:rgba(139,92,246,.28);border-radius:8px;}
/* ---- sidebar fixes: dropdown reliability + spacing ---- */
/* Dropdown menus render in a portal outside the sidebar: keep them on top and clickable. */
div[data-baseweb="popover"],div[data-baseweb="popover"] *{pointer-events:auto !important;}
div[data-baseweb="popover"]{z-index:1000160 !important;max-width:min(92vw,380px);}  /* above the transparent header (1000100) so menus are never cut off */
div[data-baseweb="popover"] ul[role="listbox"]{background:#141B34;border:1px solid rgba(139,92,246,.5);border-radius:12px;max-height:min(60vh,440px);overflow-y:auto;}  /* only scrolls on short screens */
div[data-baseweb="popover"] li[role="option"]{font-size:.85rem;padding:.45rem .8rem;cursor:pointer;white-space:normal;}
div[data-baseweb="popover"] li[role="option"]:hover,div[data-baseweb="popover"] li[aria-selected="true"]{background:rgba(139,92,246,.25);}
/* Keep the select control itself clickable and never clipped by ancestors. */
section[data-testid="stSidebar"] [data-baseweb="select"],section[data-testid="stSidebar"] [data-baseweb="select"] *{pointer-events:auto;cursor:pointer;}
section[data-testid="stSidebar"] [data-baseweb="select"] input{cursor:text;}
section[data-testid="stSidebar"] [data-baseweb="select"]>div{min-height:40px;border-radius:12px;background:rgba(255,255,255,.05);border:1px solid var(--line);}
section[data-testid="stSidebar"] [data-baseweb="select"]>div:focus-within{border-color:rgba(139,92,246,.75);}
section[data-testid="stSidebar"] div[data-testid="stSidebarContent"]{overflow-x:hidden;}  /* one scroller only: the inner wrapper must not scroll too */
section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"]{overflow:visible;}
section[data-testid="stSidebar"] div[data-testid="stSelectbox"],section[data-testid="stSidebar"] div[data-testid="stMultiSelect"],
section[data-testid="stSidebar"] div[data-testid="stSlider"]{overflow:visible;}
/* Spacing rhythm */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"]{gap:.75rem;}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:.3rem;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label{min-height:40px;padding:.45rem .75rem;}
section[data-testid="stSidebar"] div[role="radiogroup"]>label p{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.side-label{margin:1.5rem 0 .4rem !important;}
section[data-testid="stSidebar"] div[data-testid="stSlider"]{padding:0 .5rem .6rem;}
section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"]{margin-bottom:.3rem;}
section[data-testid="stSidebar"] div[data-testid="stSlider"] div[data-testid="stTickBar"]{padding-bottom:.2rem;}
section[data-testid="stSidebar"] div[data-testid="stToggle"]{padding:.15rem 0;}
section[data-testid="stSidebar"] .stButton>button,section[data-testid="stSidebar"] .stDownloadButton>button{
  width:100%;min-height:40px;padding:.45rem .7rem;font-size:.85rem;white-space:nowrap;}
section[data-testid="stSidebar"] .stDownloadButton>button{background:rgba(255,255,255,.06);border:1px solid var(--line);box-shadow:none;}
section[data-testid="stSidebar"] .stDownloadButton>button p{font-size:.85rem;margin:0;}
.ds-card{padding:.9rem 1rem !important;margin-bottom:.1rem;}
.ds-row{gap:.75rem !important;}
.ds-row>div:last-child{min-width:0;}
.ds-name{max-width:150px !important;}
.ds-status{margin-top:.75rem !important;padding-top:.65rem;border-top:1px solid var(--line);}
section[data-testid="stSidebar"] details summary{padding:.6rem .8rem;}
/* ---- v3 overrides: version-tolerant selectors, purple accent, rhythm ---- */
[data-testid="stSidebar"] [data-baseweb="radio"]>div:first-child,[data-testid="stSidebar"] [data-baseweb="radio"] input{display:none !important;}
[data-testid="stSidebar"] [data-baseweb="radio"]{display:flex !important;align-items:center;gap:.7rem;width:100%;margin:0 !important;}
[data-testid="stSidebar"] [data-baseweb="radio"]::before{content:"";width:18px;height:18px;flex:none;background:#8B93B3;}
[data-testid="stSidebar"] [data-baseweb="radio"]:has(input:checked)::before{background:#C4B5FD;}
[data-testid="stSidebar"] [data-testid="stElementContainer"],[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.75rem;}
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"]{gap:.3rem;}
[data-testid="stSidebar"] [data-testid="stSlider"]{padding:0 .6rem .5rem;margin-bottom:.4rem;}
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"]{color:#C4B5FD !important;font-weight:600;}
[data-testid="stSidebar"] [role="slider"]{background:#8B5CF6 !important;box-shadow:0 0 0 4px rgba(139,92,246,.25);}
[data-testid="stSidebar"] [data-testid="stSegmentedControl"]{margin-bottom:.4rem;}
[data-testid="stSidebar"] button[kind="segmented_controlActive"]{background:rgba(139,92,246,.35) !important;border-color:#8B5CF6 !important;color:#fff !important;}
[data-testid="stSidebar"] button[kind="segmented_control"]{border-color:var(--line) !important;color:#B8C0DC !important;}
[data-testid="stSidebar"] [data-baseweb="tag"]{background:rgba(139,92,246,.3) !important;color:#EDE9FE !important;border-radius:8px !important;}
[data-testid="stSidebar"] [data-testid="stMultiSelect"],[data-testid="stSidebar"] [data-testid="stSegmentedControl"],[data-testid="stSidebar"] [data-testid="stSlider"]{margin-bottom:.35rem;}
[data-testid="stSidebar"] [data-testid="stCheckbox"] [data-baseweb="checkbox"] [role="checkbox"],[data-testid="stSidebar"] [data-testid="stToggle"] label>div:first-child{accent-color:#8B5CF6;}
[data-testid="stSidebar"] [data-testid="stToggle"] input:checked+div,[data-testid="stSidebar"] [data-testid="stToggle"] [aria-checked="true"]{background:#8B5CF6 !important;}
[data-testid="stSidebar"] [data-testid="stToggle"]{margin:.2rem 0 .4rem;}
[data-testid="stSidebar"] .stDownloadButton{margin-top:.9rem;}
[data-testid="stSidebar"] .stDownloadButton>button,[data-testid="stSidebar"] [data-testid="stDownloadButton"] button{
  background:linear-gradient(135deg,#7C3AED,#3B82F6) !important;border:0 !important;color:#fff !important;width:100%;min-height:40px;font-size:.85rem;box-shadow:0 6px 18px rgba(99,70,240,.35);}
[data-testid="stSidebar"] [data-testid="stExpander"]{margin-top:.6rem;}
.ds-name{white-space:normal !important;word-break:break-all;max-width:100% !important;line-height:1.25;font-size:.8rem !important;}
.ds-meter{height:6px;border-radius:99px;background:rgba(255,255,255,.08);margin-top:.6rem;overflow:hidden;}
.ds-meter i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#8B5CF6,#22D3EE);}
.ds-status{margin-top:.6rem !important;padding-top:0 !important;border-top:0 !important;}
/* ---- KPI v2 ---- */
.kpi>*{position:relative;z-index:1;}
.kpi-top{display:flex;justify-content:space-between;align-items:center;}
.kpi-ico{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;color:var(--accent);
  background:color-mix(in srgb,var(--accent) 16%,transparent);border:1px solid color-mix(in srgb,var(--accent) 30%,transparent);}
.kpi:after{content:"";position:absolute;right:-40px;top:-40px;width:120px;height:120px;border-radius:50%;
  background:radial-gradient(circle,color-mix(in srgb,var(--accent) 22%,transparent),transparent 70%);pointer-events:none;}
.spark{width:100%;height:30px;margin-top:.6rem;display:block;}
.kpi-cap{font-size:.66rem;color:#6F7899;letter-spacing:.08em;text-transform:uppercase;margin-top:.2rem;}
/* ---- suspects panel ---- */
.sus-wrap{padding:1.2rem 1.4rem;border-radius:20px;background:var(--panel);border:1px solid var(--line);backdrop-filter:blur(14px);
  box-shadow:0 10px 30px rgba(5,8,25,.4);height:100%;}
.sus-wrap h4{margin:0 0 .15rem;font-size:1.05rem;}
.sus-wrap .sub{color:var(--muted);font-size:.84rem;margin-bottom:.9rem;}
.sus{margin:.75rem 0;}
.sus-top{display:flex;justify-content:space-between;font-size:.9rem;}
.sus-top b{font-size:1.05rem;}
.bar{height:9px;border-radius:99px;background:rgba(255,255,255,.07);margin:.35rem 0 .2rem;overflow:hidden;}
.bar i{display:block;height:100%;border-radius:99px;transition:width .6s ease;}
.sus-sub{font-size:.74rem;color:#7F88A8;}
.eyebrow-sm{font-size:.7rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#A78BFA;margin-bottom:.15rem;}
.page-title{margin-top:0;}
</style>
"""


PRO_CSS = """
<style>
.hero2{padding:2.6rem 2.8rem 2.2rem;border-radius:28px;margin-bottom:1.4rem;position:relative;overflow:hidden;
  background:linear-gradient(135deg,rgba(124,58,237,.26),rgba(59,130,246,.13) 55%,rgba(34,211,238,.07));
  border:1px solid rgba(139,92,246,.35);box-shadow:0 24px 70px rgba(8,10,30,.6);}
.hero2:before{content:"";position:absolute;left:-120px;bottom:-160px;width:380px;height:380px;border-radius:50%;background:radial-gradient(circle,rgba(34,211,238,.14),transparent 65%);}
.hero2:after{content:"";position:absolute;right:-90px;top:-100px;width:340px;height:340px;border-radius:50%;background:radial-gradient(circle,rgba(139,92,246,.38),transparent 65%);}
.hero2>*{position:relative;z-index:1;}
.hero2 h1{font-size:3.1rem;font-weight:800;line-height:1.06;letter-spacing:-.03em;margin:.9rem 0 1.1rem;max-width:780px;
  background:linear-gradient(90deg,#fff,#C4B5FD 55%,#7DD3FC);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
.rq{max-width:720px;padding:.85rem 1.1rem;border-radius:16px;background:rgba(11,15,25,.55);border:1px solid var(--line);border-left:3px solid #8B5CF6;color:#D5DAEE;font-size:1.02rem;line-height:1.5;}
.rq b{display:block;font-size:.68rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#A78BFA;margin-bottom:.2rem;}
.hero-stats{display:flex;flex-wrap:wrap;gap:1.2rem 2.6rem;margin-top:1.6rem;padding-top:1.3rem;border-top:1px solid var(--line);}
.hstat b{display:block;font-size:1.7rem;font-weight:800;letter-spacing:-.02em;color:#fff;line-height:1.1;}
.hstat span{font-size:.74rem;color:var(--muted);letter-spacing:.04em;}
.prof-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:1rem;margin:.4rem 0 1rem;}
.prof{padding:1.15rem 1.25rem;border-radius:20px;background:var(--panel);border:1px solid var(--line);box-shadow:0 10px 30px rgba(5,8,25,.4);}
.prof:hover{border-color:rgba(139,92,246,.5);}
.prof-top{display:flex;justify-content:space-between;align-items:flex-start;gap:.6rem;}
.prof h4{margin:0;font-size:1.05rem;font-weight:700;}
.prof-n{font-size:.72rem;color:#C4B5FD;background:rgba(139,92,246,.16);border:1px solid rgba(139,92,246,.3);padding:.12rem .55rem;border-radius:999px;white-space:nowrap;}
.prof-rule{font-size:.76rem;color:var(--muted);margin:.3rem 0 .9rem;}
.prof-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin-bottom:.9rem;}
.pstat{padding:.5rem .55rem;border-radius:12px;background:rgba(255,255,255,.04);border:1px solid var(--line);min-width:0;}
.pstat span{display:block;font-size:.62rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.pstat b{display:block;font-size:1.05rem;font-weight:700;margin-top:.1rem;}
.pstat i{display:block;font-style:normal;font-size:.68rem;color:#7F88A8;}
.prof p{margin:0 0 .45rem;font-size:.86rem;line-height:1.5;color:#C3CAE3;}
.prof .meta{font-size:.76rem;color:#8A93B2;}
.cmp{width:100%;border-collapse:separate;border-spacing:0;border-radius:16px;overflow:hidden;border:1px solid var(--line);background:var(--panel);font-size:.88rem;}
.cmp th{padding:.7rem .9rem;text-align:right;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);background:rgba(255,255,255,.04);}
.cmp td{padding:.65rem .9rem;text-align:right;border-top:1px solid var(--line);font-variant-numeric:tabular-nums;}
.cmp th:first-child,.cmp td:first-child{text-align:left;font-weight:600;}
.cmp .eff{font-size:.74rem;color:#A78BFA;}
/* ---- layout polish: balanced grids, no text overload ---- */
.kpi-grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));}
.find-grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));align-items:stretch;}
.prof-grid{grid-template-columns:repeat(auto-fit,minmax(min(100%,330px),1fr));align-items:stretch;}
.prof{display:flex;flex-direction:column;}
.prof-stats{grid-template-columns:repeat(auto-fit,minmax(72px,1fr));}
.prof .meta{margin-top:auto;padding-top:.5rem;}
.prof h4{overflow-wrap:anywhere;}
.hero2 h1{font-size:clamp(2rem,4.2vw,3.1rem);}
.hero2{padding:clamp(1.4rem,3vw,2.6rem);}
/* ---- no red: force the violet accent everywhere Streamlit would fall back to its default primary ---- */
:root{--primary-color:#8B5CF6;}
[data-baseweb="slider"] div[style*="255, 75, 75"]{filter:hue-rotate(262deg) saturate(.9);}
[data-testid="stSlider"] [role="slider"]{background:#8B5CF6 !important;border-color:#8B5CF6 !important;box-shadow:0 0 0 4px rgba(139,92,246,.25) !important;}
[data-testid="stSliderThumbValue"],[data-testid="stSliderTickBarMin"],[data-testid="stSliderTickBarMax"]{color:#C4B5FD !important;}
.stButton>button:hover,.stButton>button:focus:not(:active),.stDownloadButton>button:hover,[data-testid="stExpander"] summary:hover{border-color:#8B5CF6 !important;color:#C4B5FD !important;}
.stButton>button:active{background:rgba(139,92,246,.3) !important;border-color:#8B5CF6 !important;color:#fff !important;}
.stDownloadButton>button:hover{color:#fff !important;}
button[kind="primary"],button[data-testid="stBaseButton-primary"]{background:linear-gradient(135deg,#7C3AED,#3B82F6) !important;border:0 !important;color:#fff !important;}
*:focus-visible{outline-color:#8B5CF6 !important;}
[data-baseweb="select"]>div:hover,[data-baseweb="select"]>div:focus-within,[data-baseweb="input"]:focus-within{border-color:#8B5CF6 !important;}
[data-baseweb="radio"]:has(input:checked)>div:first-child{background-color:#8B5CF6 !important;border-color:#8B5CF6 !important;}
[data-testid="stMain"] [data-baseweb="radio"]:has(input:checked)>div:first-child{display:block !important;}
[data-baseweb="checkbox"]:has(input:checked)>span:first-child{background-color:#8B5CF6 !important;border-color:#8B5CF6 !important;}
[data-baseweb="checkbox"]:has(input:checked)>div:first-child{background-color:#8B5CF6 !important;}
[data-testid="stToggle"] [role="checkbox"][aria-checked="true"],[data-testid="stToggle"] input:checked+div{background-color:#8B5CF6 !important;}
[data-baseweb="tag"]{background:rgba(139,92,246,.3) !important;color:#EDE9FE !important;}
button[kind="segmented_controlActive"],[data-testid="stBaseButton-segmented_controlActive"]{background:rgba(139,92,246,.35) !important;border-color:#8B5CF6 !important;color:#fff !important;}
[data-testid="stBaseButton-segmented_control"]{border-color:rgba(255,255,255,.12) !important;color:#B8C0DC !important;}
a,a:visited{color:#A78BFA;}
::selection{background:rgba(139,92,246,.4);}
progress,[data-testid="stProgress"] div[role="progressbar"]>div{accent-color:#8B5CF6;}
</style>
"""


SIDEBAR_TOP_CSS = """
<style>
[data-testid="stSidebarUserContent"]{padding-top:1rem !important;}
[data-testid="stSidebarContent"]{position:relative;}
/* collapse button: pinned fully inside the sidebar's top-right corner, out of the logo's way */
[data-testid="stSidebarHeader"]{position:absolute !important;top:.6rem !important;right:.6rem !important;left:auto !important;width:auto !important;height:2rem !important;min-height:0 !important;padding:0 !important;margin:0 !important;display:flex !important;align-items:center;overflow:visible !important;z-index:1000150;}
[data-testid="stSidebarHeader"] [data-testid="stLogoSpacer"]{display:none !important;}
[data-testid="stSidebarCollapseButton"] button{width:2rem;height:2rem;color:#E7EAF6 !important;}
[data-testid="stSidebarCollapseButton"] button svg,[data-testid="stSidebarCollapseButton"] button span{color:#E7EAF6 !important;fill:currentColor;}
[data-testid="stSidebarUserContent"] .brand{margin-top:0 !important;padding-right:2.6rem;}  /* never run under the button */
</style>
"""


MOBILE_CSS = """
<style>
.cmp-wrap{border-radius:16px;}
@media (max-width:760px){.cmp-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;}.cmp-wrap .cmp{min-width:560px;}}
@media (max-width:900px){
  /* side-by-side columns get cramped before Streamlit stacks them: stack earlier */
  [data-testid="stHorizontalBlock"]{flex-wrap:wrap !important;}
  [data-testid="stColumn"],[data-testid="column"]{flex:1 1 100% !important;width:100% !important;min-width:100% !important;}
  [data-testid="stMainBlockContainer"],.block-container{padding:1rem 1rem 3rem !important;}
  .kpi-grid{grid-template-columns:repeat(2,1fr) !important;gap:.7rem;}
  .find-grid,.prof-grid{grid-template-columns:1fr !important;}
}
@media (max-width:640px){
  [data-testid="stMainBlockContainer"],.block-container{padding:.75rem .75rem 2.5rem !important;}
  .hero2{padding:1.3rem 1.15rem 1.15rem;border-radius:20px;}
  .hero2 h1{font-size:1.85rem !important;margin:.7rem 0 .9rem;}
  .rq{font-size:.92rem;padding:.7rem .9rem;}
  .hero-stats{display:grid;grid-template-columns:1fr 1fr;gap:1rem 1.2rem;margin-top:1.2rem;padding-top:1rem;}
  .hstat b{font-size:1.35rem;}
  .kpi-grid{grid-template-columns:1fr 1fr !important;}
  .prof-stats{grid-template-columns:repeat(2,1fr) !important;}
  h1{font-size:1.7rem !important;}
  h2,h3{font-size:1.15rem !important;}
  [data-testid="stSidebar"] [data-baseweb="radio"]{min-height:44px;}
  .stButton>button,.stDownloadButton>button{min-height:44px;width:100%;}
  [data-testid="stHorizontalBlock"]{gap:.75rem !important;}
  [data-testid="stRadio"] [role="radiogroup"]{flex-wrap:wrap;gap:.4rem;}
  .js-plotly-plot .legend text{font-size:11px !important;}
  .ld-name{font-size:1.6rem;}
  .steps,.step-grid{grid-template-columns:1fr !important;}
}
@media (hover:none){
  .prof:hover{border-color:var(--line);}
  [data-testid="stSidebar"] div[role="radiogroup"]>label:hover{transform:none !important;}
}
</style>
"""


DEMO_CSS = """
<style>
.st-key-launch_demo button{min-height:62px;width:100%;border-radius:16px;box-shadow:0 14px 38px rgba(124,58,237,.55);}
.st-key-launch_demo button p{font-size:1.15rem;font-weight:700;margin:0;}
.st-key-launch_demo button:hover{box-shadow:0 18px 46px rgba(124,58,237,.7);}
.cta-note{text-align:center;color:var(--muted);font-size:.86rem;margin:.6rem 0 0;}
.cta-or{display:flex;align-items:center;gap:.8rem;color:var(--muted);font-size:.74rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;margin:1.4rem 0 .8rem;}
.cta-or:before,.cta-or:after{content:"";flex:1;height:1px;background:var(--line);}
.st-key-exit_demo_main button{background:rgba(255,255,255,.06) !important;border:1px solid rgba(139,92,246,.5) !important;box-shadow:none !important;width:100%;}
</style>
"""


CHART_FIX_CSS = """
<style>
/* Chart panels: Streamlit reserves exactly the figure's height, so the panel must not add padding/border on top of it
   (that extra is what overflowed, scrolled and later overlapped the text below). The 1px outline is an inset shadow instead. */
div[data-testid="stPlotlyChart"]{box-sizing:border-box !important;padding:0 !important;border:0 !important;max-width:100%;overflow:hidden;
  box-shadow:inset 0 0 0 1px var(--line),0 10px 30px rgba(5,8,25,.4);}
div[data-testid="stPlotlyChart"]:hover{box-shadow:inset 0 0 0 1px rgba(139,92,246,.45),0 16px 44px rgba(5,8,25,.55);}
div[data-testid="stPlotlyChart"] .svg-container{max-width:100%;}
div[data-testid="stPlotlyChart"],div[data-testid="stPlotlyChart"] *{scrollbar-width:none !important;-ms-overflow-style:none !important;}
div[data-testid="stPlotlyChart"]::-webkit-scrollbar,div[data-testid="stPlotlyChart"] *::-webkit-scrollbar{display:none !important;width:0 !important;height:0 !important;}
</style>
"""


def _nav_icon_css() -> str:
    return "\n".join(
        f'section[data-testid="stSidebar"] div[role="radiogroup"]>label:nth-of-type({i}):before'
        f'{{-webkit-mask:{_mask(n)};mask:{_mask(n)};}}' for i, n in enumerate(NAV_ICONS, 1))


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(SIDEBAR_CSS.replace("__NAVICONS__", _nav_icon_css()), unsafe_allow_html=True)
    st.markdown(PRO_CSS, unsafe_allow_html=True)
    st.markdown(SIDEBAR_TOP_CSS, unsafe_allow_html=True)
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    st.markdown(CHART_FIX_CSS, unsafe_allow_html=True)
    st.markdown(DEMO_CSS, unsafe_allow_html=True)


def _flat(s: str) -> str:
    # Markdown treats indented / blank-line-separated HTML as code, so collapse to one line.
    return "".join(line.strip() for line in s.strip().splitlines())


def render(html: str) -> None:
    st.markdown(_flat(html), unsafe_allow_html=True)


def brand() -> None:
    render(f'<div class="brand"><div class="brand-logo">{svg("sleep", 20)}</div><div><div class="brand-name">Somnia</div>'
           '<div class="brand-sub">Decode your nights</div></div></div>')


def spacer(px: int = 12) -> None:
    render(f'<div style="height:{px}px"></div>')


def side_label(text: str) -> None:
    render(f'<div class="side-label">{esc(text)}</div>')


def hero(title: str, subtitle: str, eyebrow: str = "Somnia · Decode your nights") -> None:
    render(f'<div class="hero"><span class="eyebrow">{esc(eyebrow)}</span><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>')


def page_header(title: str, subtitle: str, eyebrow: str = "") -> None:
    top = f'<div class="eyebrow-sm">{esc(eyebrow)}</div>' if eyebrow else ""
    render(f'{top}<div class="page-title">{esc(title)}</div><p class="page-sub">{esc(subtitle)}</p>')


def section(title: str, sub: str | None = None) -> None:
    render(f'<div class="section"><h3>{esc(title)}</h3>{f"<p>{esc(sub)}</p>" if sub else ""}</div>')


def chips(items) -> None:
    render('<div class="chips">' + "".join(f'<span class="chip">{esc(i)}</span>' for i in items) + "</div>")


def spark(values, color, bins: int = 14) -> str:
    """Tiny distribution chart (histogram) of the real column — no invented data."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) < 3 or np.ptp(v) == 0:
        return ""
    h, _ = np.histogram(v, bins=bins)
    m, w = h.max(), 100 / bins
    rects = "".join(f"<rect x='{i * w + .8:.2f}' y='{30 - n / m * 28:.2f}' width='{w - 1.6:.2f}' height='{max(n / m * 28, .8):.2f}' "
                    f"rx='1.5' fill='{color}' opacity='{.3 + .7 * n / m:.2f}'/>" for i, n in enumerate(h))
    return f"<svg class='spark' viewBox='0 0 100 30' preserveAspectRatio='none'>{rects}</svg><div class='kpi-cap'>how values are spread</div>"


def kpi_grid(items) -> None:
    """items: [(label, value, sub)] or [(label, value, sub, icon, series)]"""
    cells = ""
    for i, it in enumerate(items):
        label, value, sub = it[:3]
        icon = it[3] if len(it) > 3 else None
        series = it[4] if len(it) > 4 else None
        color = ACCENTS[i % 4]
        ico = f'<div class="kpi-ico">{svg(icon, 17)}</div>' if icon else ""
        sp = spark(series, color) if series is not None else ""
        cells += (f'<div class="kpi" style="--accent:{color}"><div class="kpi-top"><div class="kpi-label">{esc(label)}</div>{ico}</div>'
                  f'<div class="kpi-value">{esc(value)}</div><div class="kpi-sub">{esc(sub)}</div>{sp}</div>')
    render(f'<div class="kpi-grid">{cells}</div>')


def dataset_card(name: str, total: int, in_view: int, ncols: int) -> None:
    render(f'<div class="ds-card"><div class="ds-row"><div class="ds-ico">{svg("file", 16)}</div><div>'
           f'<div class="ds-name" title="{esc(name)}">{esc(name)}</div>'
           f'<div class="ds-meta">{total:,} records · {ncols} columns</div></div></div>'
           f'<div class="ds-meter"><i style="width:{(in_view / max(total, 1)) * 100:.0f}%"></i></div>'
           f'<div class="ds-status"><span class="dot"></span>Loaded · {in_view:,} of {total:,} in view</div></div>')


def suspects(table, title="Three suspects, one question", sub="How much of the differences in sleep quality each group accounts for on its own") -> None:
    colors = {"Stress": "#F472B6", "Physical activity": "#22D3EE", "Lifestyle & body profile": "#8B5CF6"}
    rows = ""
    for r in table.sort_values("alone", ascending=False).itertuples():
        rows += (f'<div class="sus"><div class="sus-top"><span>{esc(r.group)}</span><b>{r.alone:.0%}</b></div>'
                 f'<div class="bar"><i style="width:{max(r.alone, 0) * 100:.1f}%;background:linear-gradient(90deg,{colors.get(r.group, "#8B5CF6")},'
                 f'{colors.get(r.group, "#8B5CF6")}99)"></i></div><div class="sus-sub">{esc(r.factors)}</div></div>')
    render(f'<div class="sus-wrap"><h4>{esc(title)}</h4><div class="sub">{esc(sub)}</div>{rows}</div>')


def divider_or(text: str = "or") -> None:
    render(f'<div class="cta-or">{esc(text)}</div>')


def note(text: str) -> None:
    render(f'<div class="cta-note">{esc(text)}</div>')


def table(df) -> None:
    """Small read-only table in the site style. Replaces st.dataframe so there is no scroll area inside the table."""
    def cell(v):
        if isinstance(v, (int, np.integer)):
            return f"{int(v):,}"
        if isinstance(v, (float, np.floating)):
            return "–" if v != v else f"{v:,.2f}"
        return esc(str(v))
    head = "".join(f"<th>{esc(str(c))}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{cell(v)}</td>" for v in row) + "</tr>" for row in df.itertuples(index=False))
    render(f'<div class="cmp-wrap"><table class="cmp"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def callout(body_html: str, title: str = "What this shows", kind: str = "") -> None:
    render(f'<div class="callout {kind}"><div class="callout-title">{esc(title)}</div><div>{body_html}</div></div>')


def card(title: str, body_html: str) -> None:
    render(f'<div class="card"><h4>{esc(title)}</h4>{body_html}</div>')


def bullets(items_html) -> str:
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items_html) + "</ul>"


def finding_cards(findings) -> None:
    cells = "".join(
        f'<div class="finding {"lead" if i == 0 and tag == "Research question" else ""}"><span class="tag">{esc(tag)}</span>'
        f"<h4>{esc(title)}</h4><p>{body}</p></div>"
        for i, (tag, title, body) in enumerate(findings))
    render(f'<div class="find-grid">{cells}</div>')


def steps(items) -> None:
    cells = "".join(f'<div class="card"><div class="step-n">{i}</div><h4>{esc(t)}</h4><p>{esc(d)}</p></div>'
                    for i, (t, d) in enumerate(items, 1))
    render(f'<div class="steps">{cells}</div>')


def hero_pro(headline: str, question: str, stats, eyebrow: str = "Somnia · Decode your nights") -> None:
    """Landing hero: headline, research question and a strip of key statistics [(value, label)]."""
    st_html = "".join(f'<div class="hstat"><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in stats)
    render(f'<div class="hero2"><span class="eyebrow">{esc(eyebrow)}</span><h1>{esc(headline)}</h1>'
           f'<div class="rq"><b>Research question</b>{esc(question)}</div>'
           f'{f"<div class=hero-stats>{st_html}</div>" if st_html else ""}</div>')


def profile_cards(cards) -> None:
    """cards: [dict(name, rule, n_text, stats=[(label, value, vs_text)], body, meta)]"""
    out = ""
    for c in cards:
        stats = "".join(f'<div class="pstat"><span>{esc(l)}</span><b>{esc(v)}</b><i>{esc(d)}</i></div>' for l, v, d in c["stats"])
        out += (f'<div class="prof"><div class="prof-top"><h4>{esc(c["name"])}</h4><span class="prof-n">{esc(c["n_text"])}</span></div>'
                f'<div class="prof-rule">{esc(c["rule"])}</div><div class="prof-stats">{stats}</div>'
                f'<p>{c["body"]}</p><div class="meta">{c["meta"]}</div></div>')
    render(f'<div class="prof-grid">{out}</div>')


def compare_table(rows, name_a: str, name_b: str) -> None:
    """rows: DataFrame from sleepdata.compare_profiles"""
    import sleepdata as sd
    body = ""
    for r in rows.itertuples():
        sign = "+" if r.diff > 0 else "−" if r.diff < 0 else ""
        tip = "" if r.d != r.d else f' title="Cohen’s d = {r.d:+.2f}"'   # exact value on hover
        body += (f'<tr><td>{esc(r.label)}</td><td>{r.a:,.{r.dec}f}{esc(r.unit)}</td><td>{r.b:,.{r.dec}f}{esc(r.unit)}</td>'
                 f'<td>{sign}{abs(r.diff):,.{r.dec}f}{esc(r.unit)}</td>'
                 f'<td><span class="eff"{tip}>{sd.effect_word(r.d)}</span></td></tr>')
    render(f'<div class="cmp-wrap"><table class="cmp"><thead><tr><th>Metric</th><th>{esc(name_a)}</th><th>{esc(name_b)}</th><th>Difference (A − B)</th>'
           f'<th>Size of difference</th></tr></thead><tbody>{body}</tbody></table></div>')


LOADER_CSS = """
<style>
.ld{position:fixed;inset:0;z-index:1000200;display:flex;align-items:center;justify-content:center;flex-direction:column;text-align:center;
  background:radial-gradient(800px 520px at 50% 38%,rgba(124,58,237,.30),transparent 62%),radial-gradient(600px 400px at 70% 85%,rgba(34,211,238,.10),transparent 60%),#0B0F19;
  animation:ldin .25s ease-out;}
@keyframes ldin{from{opacity:0}to{opacity:1}}
.ld-orb{position:relative;width:96px;height:96px;margin-bottom:1.6rem;display:grid;place-items:center;}
.ld-orb:before,.ld-orb:after{content:"";position:absolute;inset:0;border-radius:50%;border:1px solid rgba(139,92,246,.55);animation:ldring 2.2s ease-out infinite;}
.ld-orb:after{animation-delay:1.1s;}
@keyframes ldring{from{transform:scale(.7);opacity:.9}to{transform:scale(1.9);opacity:0}}
.ld-moon{width:68px;height:68px;border-radius:22px;display:grid;place-items:center;color:#fff;background:linear-gradient(135deg,#7C3AED,#3B82F6);
  box-shadow:0 0 50px rgba(139,92,246,.55);animation:ldfloat 3s ease-in-out infinite;}
@keyframes ldfloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
.ld-name{font-size:1.9rem;font-weight:800;letter-spacing:-.02em;color:#fff;}
.ld-tag{font-size:.85rem;color:#9AA3C0;margin:.15rem 0 1.8rem;letter-spacing:.04em;}
.ld-step{font-size:.95rem;color:#E7EAF6;min-height:1.4rem;}
.ld-bar{width:min(280px,70vw);height:5px;border-radius:99px;background:rgba(255,255,255,.08);margin:1rem 0 .8rem;overflow:hidden;}
.ld-bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#8B5CF6,#22D3EE);transition:width .4s ease;}
.ld-dots{display:flex;gap:.45rem;}
.ld-dots b{width:7px;height:7px;border-radius:50%;background:rgba(255,255,255,.15);}
.ld-dots b.on{background:#8B5CF6;box-shadow:0 0 10px rgba(139,92,246,.8);}
</style>
"""


def loading_screen(step: int, steps) -> None:
    """Full-screen branded loader. `step` is the index of the current step in `steps` (list of labels)."""
    pct = int((step + 1) / len(steps) * 100)
    dots = "".join(f'<b class="{"on" if i <= step else ""}"></b>' for i in range(len(steps)))
    render(f'{LOADER_CSS}<div class="ld"><div class="ld-orb"><div class="ld-moon">{svg("sleep", 30)}</div></div>'
           f'<div class="ld-name">Somnia</div><div class="ld-tag">Decode your nights</div>'
           f'<div class="ld-step">{esc(steps[step])}…</div><div class="ld-bar"><i style="width:{pct}%"></i></div>'
           f'<div class="ld-dots">{dots}</div></div>')