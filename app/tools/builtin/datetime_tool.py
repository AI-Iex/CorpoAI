import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, available_timezones
from app.tools.interfaces import ITool
from app.core.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)


class DateTimeTool(ITool):
    """
    Get current date and time for a timezone.
    """

    @property
    def name(self) -> str:
        return "get_datetime"

    @property
    def description(self) -> str:
        return "Get current date and time for a specific timezone"

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate datetime arguments."""
        timezone = args.get("timezone", "UTC")

        # Validate timezone exists
        if timezone not in available_timezones():
            # Try to find a close match
            suggestions = self._find_timezone_suggestions(timezone)
            if suggestions:
                raise ToolExecutionError(
                    f"Invalid timezone: '{timezone}'. Did you mean: {', '.join(suggestions[:3])}?"
                )
            raise ToolExecutionError(
                f"Invalid timezone: '{timezone}'. Use format like 'Europe/Madrid', 'America/New_York', 'Asia/Tokyo'"
            )

        return {
            "timezone": timezone,
            "format": args.get("format", "full"),
        }

    def _find_timezone_suggestions(self, query: str) -> list[str]:
        """Find timezone suggestions based on partial input."""
        query_lower = query.lower()
        suggestions = []

        for tz in available_timezones():
            if query_lower in tz.lower():
                suggestions.append(tz)

        return sorted(suggestions)[:5]

    async def execute(self, timezone: str = "UTC", format: str = "full") -> dict[str, Any]:
        """
        Get current date and time for the specified timezone.
        """
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)

            # Format based on requested format
            if format == "iso":
                formatted = now.isoformat()
            elif format == "date":
                formatted = now.strftime("%Y-%m-%d")
            elif format == "time":
                formatted = now.strftime("%H:%M:%S")
            else:  # full
                formatted = now.strftime("%A, %B %d, %Y at %H:%M:%S")

            return {
                "timezone": timezone,
                "datetime": formatted,
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "timestamp": int(now.timestamp()),
                "utc_offset": now.strftime("%z"),
                "is_dst": bool(now.dst()),
            }

        except Exception as e:
            logger.error(f"DateTime error: {e}")
            raise ToolExecutionError(f"Failed to get datetime for {timezone}: {e}")

    @staticmethod
    def get_common_timezones() -> list[str]:
        """Get list of common timezones for reference."""
        return [
            "UTC",
            "Europe/London",
            "Europe/Paris",
            "Europe/Madrid",
            "Europe/Berlin",
            "America/New_York",
            "America/Los_Angeles",
            "America/Chicago",
            "America/Sao_Paulo",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Singapore",
            "Asia/Dubai",
            "Australia/Sydney",
            "Pacific/Auckland",
        ]
