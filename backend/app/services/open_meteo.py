"""
Open-Meteo Live Weather & Forecast API Client.
Free API endpoint providing real-time current weather and 5-day daily forecasts
given latitude and longitude coordinates.
URL: https://api.open-meteo.com/v1/forecast
"""
import logging
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_open_meteo_weather(lat: float, lng: float) -> Dict[str, Any]:
    """
    Fetch current weather and 5-day daily forecast from Open-Meteo API.
    Returns structured weather dictionary with current conditions and 5-day daily forecasts.
    Falls back gracefully to realistic simulated weather if the API is offline/unreachable.
    """
    params = {
        "latitude": round(lat, 4),
        "longitude": round(lng, 4),
        "current": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,rain_sum,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": 5,
    }

    url = f"{OPEN_METEO_BASE_URL}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "KrushiRakshakAI/1.0 (Crop Disease Risk Engine)"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return parse_open_meteo_response(data)

    except Exception as exc:
        logger.warning("Open-Meteo API request failed (%s). Utilizing fallback weather data for lat=%.4f, lng=%.4f.", exc, lat, lng)

    return get_fallback_weather(lat, lng)


def parse_open_meteo_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse raw JSON response from Open-Meteo into clean structure."""
    current = data.get("current", {})
    daily = data.get("daily", {})

    temp_c = float(current.get("temperature_2m", 28.0))
    humidity_pct = float(current.get("relative_humidity_2m", 75.0))
    rain_mm = float(current.get("rain", 0.0))
    wind_kmh = float(current.get("wind_speed_10m", 12.0))

    # Daily forecasts (up to 5 days)
    days_times = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    humidities = daily.get("relative_humidity_2m_mean", [])
    rain_sums = daily.get("rain_sum", [])
    wind_maxs = daily.get("wind_speed_10m_max", [])

    forecast_days = []
    for i in range(min(5, len(days_times))):
        day_str = days_times[i]
        try:
            dt = datetime.strptime(day_str, "%Y-%m-%d")
            formatted_date = dt.strftime("%a, %b %d")
        except Exception:
            formatted_date = day_str

        forecast_days.append({
            "day": day_str,
            "date": formatted_date,
            "temp_max": float(max_temps[i]) if i < len(max_temps) else temp_c,
            "temp_min": float(min_temps[i]) if i < len(min_temps) else temp_c - 5.0,
            "humidity_pct": float(humidities[i]) if i < len(humidities) else humidity_pct,
            "rain_mm": float(rain_sums[i]) if i < len(rain_sums) else 0.0,
            "wind_kmh": float(wind_maxs[i]) if i < len(wind_maxs) else wind_kmh,
        })

    # Estimate days since rain based on recent daily rain sums
    days_since_rain = 0
    for day_fc in reversed(forecast_days):
        if day_fc["rain_mm"] > 1.0:
            break
        days_since_rain += 1

    return {
        "current": {
            "temp_c": temp_c,
            "humidity_pct": humidity_pct,
            "rain_mm": rain_mm,
            "wind_kmh": wind_kmh,
            "days_since_rain": days_since_rain,
        },
        "daily": forecast_days,
        "is_mock": False
    }


def get_fallback_weather(lat: float, lng: float) -> Dict[str, Any]:
    """Generate realistic fallback weather data if live API call fails."""
    today = datetime.now(timezone.utc)
    forecast_days = []

    # Simple deterministic variation based on coordinates
    base_temp = 27.5 + (lat % 3)
    base_humidity = 78.0 - (lng % 5)

    for i in range(5):
        day_dt = today + timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")
        formatted_date = day_dt.strftime("%a, %b %d")
        rain = 12.5 if i in (0, 1) else (2.0 if i == 2 else 0.0)

        forecast_days.append({
            "day": day_str,
            "date": formatted_date,
            "temp_max": round(base_temp + (i % 2) * 1.5, 1),
            "temp_min": round(base_temp - 6.0, 1),
            "humidity_pct": round(min(base_humidity - i * 4.0, 95.0), 1),
            "rain_mm": rain,
            "wind_kmh": 14.0,
        })

    return {
        "current": {
            "temp_c": round(base_temp, 1),
            "humidity_pct": round(base_humidity, 1),
            "rain_mm": 12.5,
            "wind_kmh": 14.0,
            "days_since_rain": 0,
        },
        "daily": forecast_days,
        "is_mock": True
    }
