"""External API tools for the outdoor activity planning agent."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from typing import Any

import requests

GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 15


def _json(data: dict[str, Any]) -> str:
    """Serialize tool results consistently for the agent."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def _weather_description(code: int | None) -> str:
    """Convert a WMO weather interpretation code into a readable label."""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Unknown weather condition")


def geocode_location_api(city: str) -> str:
    """Find a city's geographic coordinates using Open-Meteo Geocoding API.

    Use this tool first when a user asks for a weather forecast or outdoor
    activity plan for a named city. The result may contain multiple matches;
    inspect country and administrative area before selecting coordinates.
    Do not guess if the city is ambiguous: ask the user to choose a result.

    Args:
        city: City or place name, for example 'Vienna' or 'Springfield'.
    """
    city = city.strip()
    if not city:
        return _json({"ok": False, "error": "City name cannot be empty."})

    try:
        response = requests.get(
            GEOCODING_API_URL,
            params={"name": city, "count": 5, "language": "en", "format": "json"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return _json({"ok": False, "error": "Geocoding API request failed.", "details": str(exc)})
    except ValueError:
        return _json({"ok": False, "error": "Geocoding API returned invalid JSON."})

    matches = payload.get("results", [])
    if not matches:
        return _json({"ok": False, "error": f"No location found for '{city}'. Check the spelling or provide a nearby larger city."})

    results = []
    for item in matches:
        results.append(
            {
                "name": item.get("name"),
                "admin1": item.get("admin1"),
                "country": item.get("country"),
                "country_code": item.get("country_code"),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "timezone": item.get("timezone"),
            }
        )

    return _json({"ok": True, "query": city, "matches": results})


def get_weather_forecast_api(latitude: float, longitude: float, forecast_date: str) -> str:
    """Get real hourly and daily weather forecast for a location and date.

    Call this after geocode_location and pass the latitude and longitude of
    the selected city. Use an exact date in YYYY-MM-DD format. The API returns
    local hourly times, temperature, feels-like temperature, precipitation
    probability and amount, wind speed, and daily sunrise/sunset information.

    Args:
        latitude: Latitude from geocode_location, between -90 and 90.
        longitude: Longitude from geocode_location, between -180 and 180.
        forecast_date: Requested local date in YYYY-MM-DD format.
    """
    if not -90 <= latitude <= 90:
        return _json({"ok": False, "error": "latitude must be between -90 and 90."})
    if not -180 <= longitude <= 180:
        return _json({"ok": False, "error": "longitude must be between -180 and 180."})

    try:
        requested_date = datetime.strptime(forecast_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return _json({"ok": False, "error": "forecast_date must use YYYY-MM-DD format."})

    today = date.today()
    if requested_date < today or requested_date > today + timedelta(days=15):
        return _json({"ok": False, "error": "Choose a date from today through the next 15 days; this API request is for forecast data."})

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "wind_speed_10m",
                "weather_code",
            ]
        ),
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "sunrise",
                "sunset",
            ]
        ),
        "start_date": forecast_date,
        "end_date": forecast_date,
        "timezone": "auto",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    try:
        response = requests.get(FORECAST_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return _json({"ok": False, "error": "Weather API request failed.", "details": str(exc)})
    except ValueError:
        return _json({"ok": False, "error": "Weather API returned invalid JSON."})

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    hourly_forecast = []
    for index, timestamp in enumerate(times):
        code = _at(hourly, "weather_code", index)
        hourly_forecast.append(
            {
                "time": timestamp,
                "temperature_c": _at(hourly, "temperature_2m", index),
                "feels_like_c": _at(hourly, "apparent_temperature", index),
                "precipitation_probability_percent": _at(hourly, "precipitation_probability", index),
                "precipitation_mm": _at(hourly, "precipitation", index),
                "wind_speed_kmh": _at(hourly, "wind_speed_10m", index),
                "weather_code": code,
                "weather_description": _weather_description(code),
            }
        )

    daily = payload.get("daily", {})
    daily_summary = {
        "date": _at(daily, "time", 0),
        "weather_code": _at(daily, "weather_code", 0),
        "weather_description": _weather_description(_at(daily, "weather_code", 0)),
        "temperature_max_c": _at(daily, "temperature_2m_max", 0),
        "temperature_min_c": _at(daily, "temperature_2m_min", 0),
        "precipitation_probability_max_percent": _at(daily, "precipitation_probability_max", 0),
        "wind_speed_max_kmh": _at(daily, "wind_speed_10m_max", 0),
        "sunrise_local": _at(daily, "sunrise", 0),
        "sunset_local": _at(daily, "sunset", 0),
    }

    return _json(
        {
            "ok": True,
            "coordinates": {"latitude": latitude, "longitude": longitude},
            "timezone": payload.get("timezone"),
            "daily_summary": daily_summary,
            "hourly_forecast": hourly_forecast,
            "source": "Open-Meteo Forecast API",
        }
    )


def _at(data: dict[str, Any], key: str, index: int) -> Any:
    """Safely read one value from an Open-Meteo response array."""
    values = data.get(key, [])
    return values[index] if index < len(values) else None
