"""MCP server exposing exactly two Open-Meteo-backed tools."""

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from Tools import geocode_location_api, get_weather_forecast_api

mcp = FastMCP("outdoor-activity-weather")


@mcp.tool()
def geocode_location(
    city: Annotated[
        str,
        Field(description="City or place name, e.g. 'Vienna', 'Paris', or 'Springfield'. Use this first to resolve a place into coordinates."),
    ],
) -> str:
    """Find a city's coordinates using the Open-Meteo Geocoding API.

    Use this before requesting a forecast. The result may contain several
    matches; inspect country and administrative area. If the intended place
    is ambiguous, ask the user to choose instead of guessing.
    """
    return geocode_location_api(city)


@mcp.tool()
def get_weather_forecast(
    latitude: Annotated[float, Field(description="Latitude from geocode_location, between -90 and 90.")],
    longitude: Annotated[float, Field(description="Longitude from geocode_location, between -180 and 180.")],
    forecast_date: Annotated[str, Field(description="Date to forecast in YYYY-MM-DD format. Use the user's requested local date.")],
) -> str:
    """Get real hourly and daily weather for a location and date.

    Call only after geocode_location has resolved the city. Returns local
    hourly temperature, feels-like temperature, precipitation probability
    and amount, wind speed, weather description, plus daily summary and
    sunrise/sunset. Use this for weather-based outdoor activity planning.
    """
    return get_weather_forecast_api(latitude, longitude, forecast_date)


if __name__ == "__main__":
    # stdio is the default transport. Do not print to stdout here:
    # stdout is reserved for the MCP protocol.
    mcp.run()
