import csv, os, time
import requests

# API Open-Meteo "Air Quality" : gratuite, sans clé. Elle donne le CO2 (en ppm) heure
# par heure, issu d'un MODÈLE de reconstruction de l'atmosphère (pas d'un capteur).
# "past_days" donne de l'historique réel en UN seul appel (90 jours).
LAT, LON = 48.0061, 0.1996  # Le Mans
PAST_DAYS = 90
URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

def fetch_hourly_co2(retries=4, backoff=5):
    # On demande les données à l'API ; si ça échoue, on réessaie jusqu'à 4 fois.
    params = {
        "latitude": LAT, "longitude": LON,
        "hourly": "carbon_dioxide",
        "past_days": PAST_DAYS,
        "forecast_days": 0,
        "timezone": "auto",
    }
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(URL, params=params, timeout=(15, 30))
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  fetch attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)
    # Après 4 échecs : erreur VISIBLE, le job s'arrête (pas d'échec silencieux)
    raise RuntimeError(f"Open-Meteo Air Quality API unreachable after {retries} attempts") from last_error

def aggregate_to_daily(times, values):
    # Mesures horaires -> une ligne par jour (moyenne des heures disponibles).
    # Un jour avec moins de 24 heures réelles est SIGNALÉ, pas moyenné en silence.
    by_day = {}
    for t, v in zip(times, values):
        day = t[:10]  # "AAAA-MM-JJTHH:MM" -> "AAAA-MM-JJ"
        by_day.setdefault(day, []).append(v)

    rows = []
    for day in sorted(by_day):
        hours = by_day[day]
        real_hours = [h for h in hours if h is not None]
        rows.append({
            "date": day,
            "co2_ppm": round(sum(real_hours) / len(real_hours), 1) if real_hours else "",
            "n_hours_observed": len(real_hours),
        })
    return rows

def main():
    print(f"Fetching {PAST_DAYS} days of real hourly CO2 (ppm) for Le Mans "
          f"({LAT}, {LON}) from Open-Meteo Air Quality API...")
    data = fetch_hourly_co2()
    times = data["hourly"]["time"]
    values = data["hourly"]["carbon_dioxide"]
    print(f"Received {len(times)} real hourly readings "
          f"({times[0]} to {times[-1]})")

    rows = aggregate_to_daily(times, values)
    incomplete = [r for r in rows if r["n_hours_observed"] < 24]
    print(f"Aggregated to {len(rows)} daily values -- "
          f"{len(incomplete)} day(s) with fewer than 24 real hourly readings")
    for r in incomplete:
        print(f"  incomplete day: {r['date']} ({r['n_hours_observed']}/24 hours)")

    os.makedirs("data", exist_ok=True)
    with open("data/series.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "co2_ppm", "n_hours_observed"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote data/series.csv ({len(rows)} days)")

if __name__ == "__main__":
    main()
