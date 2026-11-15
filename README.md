# 🌙 Somnia Analytics

Premium-style analytics dashboard for the **"Sleep on It" Sleep, Health & Lifestyle Data Analytics Challenge**.
Research question: *What matters more for sleep quality — stress, physical activity, or lifestyle?*

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure
| File | Purpose |
|---|---|
| `app.py` | Streamlit UI: upload, sidebar filters, six pages |
| `sleepdata.py` | Loading, cleaning, statistics, auto-generated findings (pandas + numpy only) |
| `viz.py` | Plotly chart functions, one consistent dark style |
| `theme.py` | Custom CSS + HTML components (glass cards, KPIs, callouts) |
| `data/` | Bundled Kaggle CSV (optional; you can upload your own) |

## Method notes
- All figures are calculated from the loaded CSV; nothing is simulated.
- Association strength uses rank (Spearman) correlation; categorical factors use the correlation ratio η.
- "Stress vs Activity vs Lifestyle" uses linear-model R² (alone and unique). Lifestyle = daily steps, BMI, heart rate.
- Records identical on every column except Person ID are flagged as *repeated profiles*; a sidebar toggle excludes them.
- Scatter points are jittered for display only; hover shows true values.
