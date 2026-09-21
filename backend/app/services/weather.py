"""
Weather Service Module.
Fetches weather data from Open-Meteo API, engineers features, and computes weather-based disease risk.
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, TypedDict
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

# Open-Meteo API endpoint
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Cache configuration
CACHE_DURATION_SECONDS = 3600  # 1 hour


@dataclass
class WeatherSnapshot:
    """Snapshot of current weather conditions."""
    latitude: float
    longitude: float
    temperature: float  # Celsius
    humidity: float  # Percentage (0-100)
    precipitation: float  # mm
    wind_speed: float  # km/h
    timestamp: datetime
    forecast: list  # 5-day forecast data


class WeatherFeatures(TypedDict):
    """Engineered weather features for disease risk assessment."""
    days_since_rain: int
    humidity_bucket: str  # "low", "medium", "high"
    leaf_wetness_proxy: float  # 0-100
    temp_suitability_for_disease: float  # 0-100
    recent_precipitation_total: float  # mm in last 3 days


# Simple in-memory cache (key: (lat, lng) -> (timestamp, snapshot))
_weather_cache: Dict[tuple, tuple] = {}


def _get_cache_key(lat: float, lng: float, forecast_days: int = 5) -> tuple:
    """Generate cache key for location."""
    return (round(lat, 4), round(lng, 4), forecast_days)


def _get_cached_weather(lat: float, lng: float, forecast_days: int = 5) -> Optional[WeatherSnapshot]:
    """Get cached weather if available and not expired."""
    key = _get_cache_key(lat, lng, forecast_days)
    if key in _weather_cache:
        cached_time, snapshot = _weather_cache[key]
        if time.time() - cached_time < CACHE_DURATION_SECONDS:
            logger.debug(f"Using cached weather for {lat}, {lng}")
            return snapshot
        else:
            # Expired, remove from cache
            del _weather_cache[key]
    return None


def _cache_weather(lat: float, lng: float, snapshot: WeatherSnapshot, forecast_days: int = 5):
    """Cache weather snapshot."""
    key = _get_cache_key(lat, lng, forecast_days)
    _weather_cache[key] = (time.time(), snapshot)
    logger.debug(f"Cached weather for {lat}, {lng}")


async def fetch_weather(lat: float, lng: float, forecast_days: int = 5) -> WeatherSnapshot:
    """
    Fetch current weather and 5-day forecast from Open-Meteo API.
    Caches responses per farm for 1 hour.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        WeatherSnapshot with current conditions and forecast
    """
    # Check cache first
    forecast_days = max(1, min(forecast_days, 16))
    cached = _get_cached_weather(lat, lng, forecast_days)
    if cached:
        return cached
    
    # Fetch from Open-Meteo API
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean",
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Parse current weather
        current = data["current"]
        daily = data["daily"]
        
        snapshot = WeatherSnapshot(
            latitude=lat,
            longitude=lng,
            temperature=current["temperature_2m"],
            humidity=current["relative_humidity_2m"],
            precipitation=current["precipitation"],
            wind_speed=current["wind_speed_10m"],
            timestamp=datetime.now(),
            forecast=[
                {
                    "date": daily["time"][i],
                    "precipitation_sum": daily["precipitation_sum"][i],
                    "temp_max": daily["temperature_2m_max"][i],
                    "temp_min": daily["temperature_2m_min"][i],
                    "humidity_mean": daily["relative_humidity_2m_mean"][i],
                }
                for i in range(len(daily["time"]))
            ]
        )
        
        # Cache the result
        _cache_weather(lat, lng, snapshot, forecast_days)
        
        logger.info(f"Fetched weather for {lat}, {lng}: {snapshot.temperature}°C, {snapshot.humidity}% humidity")
        return snapshot
        
    except httpx.HTTPError as exc:
        logger.error(f"Failed to fetch weather from Open-Meteo: {exc}")
        raise
    except Exception as exc:
        logger.error(f"Unexpected error fetching weather: {exc}")
        raise


def engineer_weather_features(snapshot: WeatherSnapshot) -> WeatherFeatures:
    """
    Engineer features from raw weather snapshot.
    
    Args:
        snapshot: WeatherSnapshot with raw weather data
    
    Returns:
        WeatherFeatures with engineered features
    """
    # Calculate days since rain (check forecast for recent precipitation)
    days_since_rain = 0
    recent_precipitation_total = 0.0
    
    # Check last 3 days of forecast for precipitation
    for i, day in enumerate(snapshot.forecast[:3]):
        if day["precipitation_sum"] > 0:
            if days_since_rain == 0:  # First day with rain
                days_since_rain = i
            recent_precipitation_total += day["precipitation_sum"]
    
    # If no rain in forecast, assume 3+ days since rain
    if days_since_rain == 0 and recent_precipitation_total == 0:
        days_since_rain = 3
    
    # Humidity bucket
    if snapshot.humidity < 40:
        humidity_bucket = "low"
    elif snapshot.humidity < 70:
        humidity_bucket = "medium"
    else:
        humidity_bucket = "high"
    
    # Leaf wetness proxy (humidity + recent rain combined heuristic)
    # Higher humidity + recent rain = higher leaf wetness
    leaf_wetness_proxy = min(100, (snapshot.humidity * 0.6) + (recent_precipitation_total * 10))
    
    # Temperature suitability for disease (bell curve peaking around 20-28°C)
    # Optimal range: 20-28°C for most fungal diseases
    temp = snapshot.temperature
    if temp < 10 or temp > 35:
        temp_suitability = 0.0
    elif 20 <= temp <= 28:
        # Peak suitability in optimal range
        temp_suitability = 100.0
    elif 10 <= temp < 20:
        # Linear increase from 10°C to 20°C
        temp_suitability = ((temp - 10) / 10) * 100
    else:  # 28 < temp <= 35
        # Linear decrease from 28°C to 35°C
        temp_suitability = ((35 - temp) / 7) * 100
    
    return WeatherFeatures(
        days_since_rain=days_since_rain,
        humidity_bucket=humidity_bucket,
        leaf_wetness_proxy=leaf_wetness_proxy,
        temp_suitability_for_disease=temp_suitability,
        recent_precipitation_total=recent_precipitation_total,
    )


def compute_weather_risk(features: WeatherFeatures) -> float:
    """
    Compute weather-based disease risk score (0-100) using rule-based scoring.
    
    Args:
        features: WeatherFeatures with engineered weather data
    
    Returns:
        Risk score from 0-100
    """
    risk_score = 0.0
    
    # Rule 1: Leaf wetness proxy (weight: 0.35) - tunable
    # Higher leaf wetness increases disease risk significantly
    leaf_wetness_risk = features["leaf_wetness_proxy"] * 0.35
    risk_score += leaf_wetness_risk
    
    # Rule 2: Temperature suitability (weight: 0.30) - tunable
    # Optimal temperatures for fungal growth increase risk
    temp_risk = features["temp_suitability_for_disease"] * 0.30
    risk_score += temp_risk
    
    # Rule 3: Recent precipitation (weight: 0.20) - tunable
    # Recent rain creates favorable conditions for disease spread
    precip_risk = min(100, features["recent_precipitation_total"] * 5) * 0.20
    risk_score += precip_risk
    
    # Rule 4: Humidity bucket (weight: 0.15) - tunable
    # High humidity promotes fungal growth
    humidity_risk = 0.0
    if features["humidity_bucket"] == "high":
        humidity_risk = 100 * 0.15
    elif features["humidity_bucket"] == "medium":
        humidity_risk = 50 * 0.15
    else:  # low
        humidity_risk = 20 * 0.15
    risk_score += humidity_risk
    
    # Ensure score is within 0-100 range
    risk_score = max(0.0, min(100.0, risk_score))
    
    logger.debug(f"Weather risk score: {risk_score:.2f} (leaf_wetness: {leaf_wetness_risk:.2f}, "
                 f"temp: {temp_risk:.2f}, precip: {precip_risk:.2f}, humidity: {humidity_risk:.2f})")
    
    return risk_score


def get_weather_risk(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch weather for a location and return the API-friendly risk summary."""
    snapshot = asyncio.run(fetch_weather(lat, lon))
    features = engineer_weather_features(snapshot)
    risk_score = compute_weather_risk(features)

    if risk_score < 35:
        risk_level = "low"
        description = "Conditions are relatively unfavorable for disease spread."
    elif risk_score < 70:
        risk_level = "medium"
        description = "Moderate disease pressure is expected under current weather conditions."
    else:
        risk_level = "high"
        description = "High humidity and moisture favor rapid disease development."

    return {
        "temperature": snapshot.temperature,
        "humidity": snapshot.humidity,
        "wind_speed": snapshot.wind_speed,
        "description": description,
        "risk_level": risk_level,
    }
