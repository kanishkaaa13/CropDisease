"""
Weather Service
---------------
Fetches weather data and computes an agricultural risk level.
Uses OpenWeatherMap API when WEATHER_API_KEY is set; otherwise returns mock data.
"""
import httpx
from app.config import settings


def get_weather_risk(lat: float, lon: float) -> dict:
    """
    Fetch current weather for (lat, lon) and return structured risk data.
    """
    if settings.weather_api_key and settings.weather_api_key != "your_openweathermap_api_key_here":
        return _fetch_live_weather(lat, lon)
    return _mock_weather(lat, lon)


def _fetch_live_weather(lat: float, lon: float) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": settings.weather_api_key, "units": "metric"}
    try:
        resp = httpx.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        desc = data["weather"][0]["description"]
        risk = _compute_risk(temp, humidity)
        return {"temperature": temp, "humidity": humidity, "wind_speed": wind, "description": desc, "risk_level": risk}
    except Exception:
        return _mock_weather(lat, lon)


def _mock_weather(lat: float, lon: float) -> dict:
    return {
        "temperature": 28.5,
        "humidity": 72.0,
        "wind_speed": 12.3,
        "description": "partly cloudy (mock)",
        "risk_level": "medium",
    }


def _compute_risk(temp: float, humidity: float) -> str:
    if humidity > 80 and 20 < temp < 35:
        return "high"
    elif humidity > 60:
        return "medium"
    return "low"
