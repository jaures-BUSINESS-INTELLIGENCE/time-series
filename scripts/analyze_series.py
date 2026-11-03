import csv, json, os, time
from datetime import date, timedelta

WINDOW = 7          # taille de la fenêtre de la moyenne glissante (jours)
PROJECT_STEPS = 7   # nombre de jours projetés vers l'avenir

def load_series(path="data/series.csv"):
    # Lit le fichier des valeurs journalières
    with open(path) as f:
        rows = []
        for r in csv.DictReader(f):
            if r["co2_ppm"] == "":
                continue  # jour sans aucune mesure réelle : rien à moyenner
            rows.append({"date": r["date"], "value": float(r["co2_ppm"])})
    return rows

def clean_series(rows):
    # On liste TOUS les jours entre le premier et le dernier jour, et on note les trous.
    # On ne remplit pas les trous en silence : un vrai pipeline dit ce qu'il a fait.
    by_date = {r["date"]: r["value"] for r in rows}
    start = date.fromisoformat(rows[0]["date"])
    end = date.fromisoformat(rows[-1]["date"])
    n_days = (end - start).days + 1

    cleaned = []
    gaps = []
    for i in range(n_days):
        d = (start + timedelta(days=i)).isoformat()
        if d in by_date:
            cleaned.append({"day": i, "date": d, "value": by_date[d]})
        else:
            gaps.append(i)

    # On regroupe les jours manquants consécutifs en "plages" (ex : du 3 au 5)
    gap_ranges = []
    if gaps:
        seg_start = prev = gaps[0]
        for g in gaps[1:]:
            if g == prev + 1:
                prev = g
            else:
                gap_ranges.append((seg_start, prev))
                seg_start = prev = g
        gap_ranges.append((seg_start, prev))
    return cleaned, gap_ranges, start

def rolling_mean(values, window=WINDOW):
    # Moyenne glissante : pour chaque jour, moyenne des (au plus) 7 derniers jours
    out = []
    for i in range(len(values)):
        lo = max(0, i - window + 1)
        chunk = values[lo:i + 1]
        out.append(round(sum(chunk) / len(chunk), 2))
    return out

def exponential_smoothing(values, alpha=0.3):
    # Lissage exponentiel : nouvelle valeur = 30 % du jour + 70 % du lissage précédent
    out = [values[0]]
    for v in values[1:]:
        out.append(round(alpha * v + (1 - alpha) * out[-1], 2))
    return out

def linear_trend_projection(days, values, start, steps=PROJECT_STEPS):
    # Droite des moindres carrés à travers les points (jour, valeur), puis prolongée.
    # Volontairement la prévision la plus simple, pas un modèle sophistiqué.
    n = len(days)
    mean_x = sum(days) / n
    mean_y = sum(values) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(days, values))
    den = sum((x - mean_x) ** 2 for x in days)
    slope = num / den if den else 0.0          # pente en ppm par jour
    intercept = mean_y - slope * mean_x
    last_day = days[-1]
    projection = []
    for i in range(1, steps + 1):
        day_idx = last_day + i
        projection.append({
            "day": day_idx,
            "date": (start + timedelta(days=day_idx)).isoformat(),
            "value": round(intercept + slope * day_idx, 2),
        })
    return projection, slope

def main():
    raw = load_series()
    cleaned, gap_ranges, start = clean_series(raw)

    print(f"Loaded {len(raw)} real daily CO2 readings "
          f"({raw[0]['date']} to {raw[-1]['date']}).")
    if gap_ranges:
        for seg_start, seg_end in gap_ranges:
            span = seg_end - seg_start + 1
            d1 = (start + timedelta(days=seg_start)).isoformat()
            d2 = (start + timedelta(days=seg_end)).isoformat()
            print(f"  Gap detected: {d1} to {d2} ({span} missing day(s)) -- "
                  f"flagged, not silently filled.")
    else:
        print("  No gaps detected -- this real pull is a complete daily series "
              "(Open-Meteo's air-quality model backfills every hour, unlike raw "
              "sensor telemetry, which can and does drop readings -- the "
              "gap-detection logic stays in for that reason, see the manual).")

    days = [c["day"] for c in cleaned]
    values = [c["value"] for c in cleaned]

    smoothed_ma = rolling_mean(values)
    smoothed_exp = exponential_smoothing(values)
    projection, slope = linear_trend_projection(days, values, start)

    print(f"\nLast 5 raw values (ppm):      {values[-5:]}")
    print(f"Last 5 rolling-mean (ppm):    {smoothed_ma[-5:]}")
    print(f"Last 5 exp-smoothed (ppm):    {smoothed_exp[-5:]}")
    print(f"\nLinear trend slope: {slope:+.3f} ppm/day")
    print(f"Projection (next {PROJECT_STEPS} days, ppm): {[p['value'] for p in projection]}")

    # La note d'honnêteté : ce que la projection peut et ne peut pas dire
    honest_note = (
        f"Projection covers {PROJECT_STEPS} days ahead from {len(cleaned)} days of "
        f"real CO2 history ({len(gap_ranges)} known gap(s) in the source data). "
        "This is a straight line through one seasonal window of real atmospheric "
        "data -- CO2 has a well-known yearly cycle (lower in the Northern "
        "Hemisphere's growing season, higher in winter), so a trend measured over "
        "90 summer/autumn days should NOT be extrapolated across season boundaries. "
        "Trust this projection only a few days out."
    )
    print(f"\nHonesty note: {honest_note}")

    output = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "unit": "ppm",
        "raw": [{"day": c["day"], "date": c["date"], "value": c["value"]} for c in cleaned],
        "gaps": [
            {"start_day": s, "end_day": e,
             "start_date": (start + timedelta(days=s)).isoformat(),
             "end_date": (start + timedelta(days=e)).isoformat()}
            for s, e in gap_ranges
        ],
        "rolling_mean": [{"day": d, "value": v} for d, v in zip(days, smoothed_ma)],
        "exp_smoothed": [{"day": d, "value": v} for d, v in zip(days, smoothed_exp)],
        "projection": projection,
        "trend_slope_per_day": round(slope, 4),
        "honest_note": honest_note,
    }
    os.makedirs("docs/data", exist_ok=True)  # crée le dossier de sortie s'il manque
    with open("docs/data/series_analysis.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\nWrote docs/data/series_analysis.json")

if __name__ == "__main__":
    main()
