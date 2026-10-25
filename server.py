"""Weather MCP server (stdio transport).

Exposes one tool, `get_weather`, backed by Open-Meteo.
"""

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes -> human text
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


# ---------------------------------------------------------------------------
# THE TOOL - Weather fetch tool.
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_weather(city: str) -> str:
    """Get the current live weather for a city.

    Args:
        city: City name, e.g. 'Kozhikode', 'Bangalore' or 'London'.
    """
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            geo = await client.get(
                GEO_URL, params={"name": city, "count": 1, "language": "en", "format": "json"}
            )
            geo.raise_for_status()
            results = geo.json().get("results")
            if not results:
                return f"Could not find a location named '{city}'."

            place = results[0]
            wx = await client.get(
                FORECAST_URL,
                params={
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                               "weather_code,wind_speed_10m",
                    "timezone": "auto",
                },
            )
            wx.raise_for_status()
            cur = wx.json()["current"]
        except httpx.HTTPError as exc:
            return f"Weather service error: {exc}"

    condition = WMO_CODES.get(cur["weather_code"], f"Code {cur['weather_code']}")
    where = ", ".join(p for p in (place["name"], place.get("admin1"), place.get("country")) if p)
    return (
        f"Weather in {where} (as of {cur['time']} local time):\n"
        f"- Condition: {condition}\n"
        f"- Temperature: {cur['temperature_2m']} °C (feels like {cur['apparent_temperature']} °C)\n"
        f"- Humidity: {cur['relative_humidity_2m']} %\n"
        f"- Wind speed: {cur['wind_speed_10m']} km/h"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
