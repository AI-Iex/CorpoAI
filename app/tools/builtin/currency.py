import logging
from typing import Any
import httpx
from app.tools.interfaces import ITool
from app.core.exceptions import ToolExecutionError

logger = logging.getLogger(__name__)

# Common currency codes and their names for reference
CURRENCY_INFO = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "GBP": "British Pound",
    "JPY": "Japanese Yen",
    "CHF": "Swiss Franc",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
    "CNY": "Chinese Yuan",
    "HKD": "Hong Kong Dollar",
    "SGD": "Singapore Dollar",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "DKK": "Danish Krone",
    "MXN": "Mexican Peso",
    "BRL": "Brazilian Real",
    "INR": "Indian Rupee",
    "KRW": "South Korean Won",
    "ZAR": "South African Rand",
    "TRY": "Turkish Lira",
    "PLN": "Polish Zloty",
    "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint",
    "ILS": "Israeli Shekel",
    "THB": "Thai Baht",
    "MYR": "Malaysian Ringgit",
    "PHP": "Philippine Peso",
    "IDR": "Indonesian Rupiah",
}


class CurrencyTool(ITool):
    """
    Convert between currencies using real-time exchange rates.
    """

    API_URL = "https://api.frankfurter.app"

    @property
    def name(self) -> str:
        return "convert_currency"

    @property
    def description(self) -> str:
        return "Convert an amount from one currency to another using real-time exchange rates"

    def validate_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Validate currency conversion arguments."""
        # Check required fields
        if "amount" not in args:
            raise ToolExecutionError("Missing required argument: amount")
        if "from_currency" not in args:
            raise ToolExecutionError("Missing required argument: from_currency")
        if "to_currency" not in args:
            raise ToolExecutionError("Missing required argument: to_currency")

        # Validate amount
        try:
            amount = float(args["amount"])
            if amount <= 0:
                raise ToolExecutionError("Amount must be greater than 0")
        except (TypeError, ValueError):
            raise ToolExecutionError("Amount must be a valid number")

        # Normalize currency codes to uppercase
        from_currency = str(args["from_currency"]).upper().strip()
        to_currency = str(args["to_currency"]).upper().strip()

        if not from_currency or len(from_currency) != 3:
            raise ToolExecutionError("Invalid source currency code. Use 3-letter codes like USD, EUR, GBP")
        if not to_currency or len(to_currency) != 3:
            raise ToolExecutionError("Invalid target currency code. Use 3-letter codes like USD, EUR, GBP")

        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
        }

    async def execute(
        self, amount: float, from_currency: str, to_currency: str
    ) -> dict[str, Any]:
        """
        Convert an amount from one currency to another.
        """
        # Handle same currency case
        if from_currency == to_currency:
            return {
                "amount": amount,
                "from_currency": from_currency,
                "from_currency_name": CURRENCY_INFO.get(from_currency, from_currency),
                "to_currency": to_currency,
                "to_currency_name": CURRENCY_INFO.get(to_currency, to_currency),
                "converted_amount": amount,
                "exchange_rate": 1.0,
                "message": f"{amount} {from_currency} = {amount} {to_currency} (same currency)",
            }

        # Build API URL
        url = f"{self.API_URL}/latest?amount={amount}&from={from_currency}&to={to_currency}"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ToolExecutionError(
                    "Invalid currency code. Supported currencies include: USD, EUR, GBP, JPY, etc."
                )
            if e.response.status_code == 422:
                error_detail = "Invalid currency code or amount"
                try:
                    error_data = e.response.json()
                    error_detail = error_data.get("message", error_detail)
                except Exception:
                    pass
                raise ToolExecutionError(error_detail)
            raise ToolExecutionError(f"Currency service error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise ToolExecutionError(f"Failed to connect to currency service: {e}")
        except Exception as e:
            logger.error(f"Currency API error: {e}")
            raise ToolExecutionError(f"Failed to convert currency: {e}")

        # Extract conversion data
        try:
            converted_amount = data["rates"].get(to_currency)
            if converted_amount is None:
                raise ToolExecutionError(f"Currency {to_currency} not supported")

            # Calculate exchange rate
            exchange_rate = converted_amount / amount if amount > 0 else 0

            # Format the result
            return {
                "amount": amount,
                "from_currency": from_currency,
                "from_currency_name": CURRENCY_INFO.get(from_currency, from_currency),
                "to_currency": to_currency,
                "to_currency_name": CURRENCY_INFO.get(to_currency, to_currency),
                "converted_amount": round(converted_amount, 2),
                "exchange_rate": round(exchange_rate, 6),
                "date": data.get("date", "unknown"),
                "message": f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}",
            }

        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")
            raise ToolExecutionError("Invalid response from currency service")
