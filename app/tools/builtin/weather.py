import logging
from typing import Any
import httpx
from app.tools.interfaces import ITool
from app.core.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)


class WeatherTool(ITool):
    """
    Get current weather for a city.
    """

    WTTR_URL = "https://wttr.in"

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get current weather conditions for a city"

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate weather arguments."""
        if "city" not in args:
            raise ToolExecutionError("Missing required argument: city")

        city = args["city"].strip()
        if not city:
            raise ToolExecutionError("City cannot be empty")

        return {
            "city": city,
            "units": args.get("units", "metric"),
            "lang": args.get("lang", "en"),
        }

    async def execute(self, city: str, units: str = "metric", lang: str = "en") -> dict[str, Any]:
        """
        Get weather for the specified city.
        """
        # Build wttr.in URL with JSON format
        # Format: ?format=j1 returns JSON format
        url = f"{self.WTTR_URL}/{city}?format=j1&lang={lang}"

        if units == "imperial":
            url += "&u"  # Use USCS/imperial units

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ToolExecutionError(f"City not found: {city}")
            raise ToolExecutionError(f"Weather service error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise ToolExecutionError(f"Failed to connect to weather service: {e}")
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            raise ToolExecutionError(f"Failed to get weather: {e}")

        # Extract relevant data from wttr.in response
        try:
            current = data["current_condition"][0]
            location = data["nearest_area"][0]

            # Get temperature based on units
            if units == "imperial":
                temp = current.get("temp_F", "N/A")
                feels_like = current.get("FeelsLikeF", "N/A")
                temp_unit = "°F"
            else:
                temp = current.get("temp_C", "N/A")
                feels_like = current.get("FeelsLikeC", "N/A")
                temp_unit = "°C"

            # Get weather description in requested language
            weather_desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            if lang != "en":
                # Try to get localized description
                lang_key = f"lang_{lang}"
                if lang_key in current:
                    weather_desc = current[lang_key][0].get("value", weather_desc)

            return {
                "city": location.get("areaName", [{}])[0].get("value", city),
                "country": location.get("country", [{}])[0].get("value", "Unknown"),
                "temperature": f"{temp}{temp_unit}",
                "feels_like": f"{feels_like}{temp_unit}",
                "condition": weather_desc,
                "humidity": f"{current.get('humidity', 'N/A')}%",
                "wind_speed": f"{current.get('windspeedKmph', 'N/A')} km/h",
                "wind_direction": current.get("winddir16Point", "N/A"),
                "visibility": f"{current.get('visibility', 'N/A')} km",
                "uv_index": current.get("uvIndex", "N/A"),
                "observation_time": current.get("observation_time", "N/A"),
            }

        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse weather data: {e}")
            raise ToolExecutionError(f"Failed to parse weather data for {city}")
