# CO2 time series lab

A small automated pipeline that downloads a real time series, cleans it, smooths it, projects it a few days ahead, and shows the result on a web page.

**Live dashboard:** https://jaures-business-intelligence.github.io/time-series/

## What it does

1. **Fetch**: `scripts/fetch_series.py` calls the free [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) and gets 90 days of hourly CO2 values (ppm). It retries 4 times, then fails loudly if the API is not reachable. It writes one value per day in `data/series.csv`.
2. **Analyze**: `scripts/analyze_series.py` detects missing days, computes a 7-day rolling mean, an exponential smoothing (alpha 0.3) and a 7-day linear projection. It writes `docs/data/series_analysis.json`.
3. **Show**: `docs/index.html` reads the JSON and draws four KPI cards, an honesty note and a chart with four series.
4. **Automate**: `.github/workflows/update_series.yml` runs the two scripts every Monday at 06:00 UTC (and on demand) and commits the new files.

## Current location

The series is for a grid cell near **Yaoundé** (`LAT, LON = 3.8480, 11.5021`). It was first run for Le Mans (48.0061, 0.1996). Only the coordinates changed; the analysis code did not.

## Limits (please read)

- The values come from a **model** (CAMS reanalysis) on a grid of several tens of kilometres. They are **not** measurements from a sensor in a city.
- The projection is a straight line fitted on 90 days. It is very sensitive to the last days and it ignores the yearly cycle of CO2. It should be trusted for a few days at most, and only as a direction.
- If the API fails, the Action stops and the old files stay in place. The dashboard then shows older data and displays its age.
- The honesty note is written in the analysis script and is not adapted to each location.

## Files

| File | Role |
|---|---|
| `scripts/fetch_series.py` | download and daily aggregation |
| `scripts/analyze_series.py` | cleaning, smoothing, projection |
| `data/series.csv` | daily series (generated) |
| `docs/data/series_analysis.json` | analysis result (generated) |
| `docs/index.html` | dashboard (GitHub Pages) |
| `.github/workflows/update_series.yml` | weekly automation |
| `REFLECTIONS.md` | answers to the 7 reflection questions |

## Run it yourself

```bash
pip install requests
python scripts/fetch_series.py
python scripts/analyze_series.py
```

Then open `docs/index.html` through a local web server, for example `python -m http.server` from the `docs` folder.
