"""M3: rainfall-based climate risk index using Open-Meteo."""

from datetime import datetime

import requests

from app import fixtures
from app.config import (
    ALERT_RAIN_THRESHOLD_MM,
    DEMO_MODE,
    ELDORET_LAT,
    ELDORET_LON,
    OPEN_METEO_URL,
)


def get_risk() -> dict:
    if DEMO_MODE:
        return dict(fixtures.RISK)

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": ELDORET_LAT,
                "longitude": ELDORET_LON,
                "hourly": "precipitation",
                "forecast_days": 3,
                "timezone": "Africa/Nairobi",
            },
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        precipitation = hourly.get("precipitation", [])

        if not times or len(times) != len(precipitation):
            raise ValueError("Invalid rainfall forecast from Open-Meteo")

        current_hour = datetime.now().strftime("%Y-%m-%dT%H:00")
        start = next(
            (i for i, timestamp in enumerate(times) if timestamp >= current_hour),
            None,
        )

        if start is None or len(precipitation) - start < 48:
            raise ValueError("Open-Meteo did not provide the next 48 hours")

        rainfall = [
            max(0.0, float(value or 0))
            for value in precipitation[start : start + 48]
        ]

        rain_24h = round(sum(rainfall[:24]), 1)
        rain_48h = round(sum(rainfall), 1)

        threshold = max(ALERT_RAIN_THRESHOLD_MM, 1.0)
        score = round(
            min(
                1.0,
                max(
                    rain_24h / threshold,
                    rain_48h / (2 * threshold),
                ),
            ),
            2,
        )

        if score >= 0.8:
            level = "HIGH"
        elif score >= 0.4:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "risk_level": level,
            "risk_score": score,
            "rain_mm_24h": rain_24h,
            "rain_mm_next_48h": rain_48h,
            "source": "open-meteo",
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
    ) as exc:
        print(f"Open-Meteo unavailable; using demo fallback: {exc}")
        result = dict(fixtures.RISK)
        result["source"] = "demo-fallback"
        return result
