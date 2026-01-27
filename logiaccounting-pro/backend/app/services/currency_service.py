"""
Multi-Currency Service
Handle multiple currencies and conversions
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP


class CurrencyService:
    """Manages currencies and exchange rates"""

    _instance = None
    _currencies: Dict[str, dict] = {}
    _rates: Dict[str, Dict[str, float]] = {}  # date -> {currency: rate}
    _base_currency = "USD"

    DEFAULT_CURRENCIES = [
        {"code": "USD", "name": "US Dollar", "symbol": "$", "decimal_places": 2},
        {"code": "EUR", "name": "Euro", "symbol": "E", "decimal_places": 2},
        {"code": "GBP", "name": "British Pound", "symbol": "L", "decimal_places": 2},
        {"code": "JPY", "name": "Japanese Yen", "symbol": "Y", "decimal_places": 0},
        {"code": "ARS", "name": "Argentine Peso", "symbol": "$", "decimal_places": 2},
        {"code": "BRL", "name": "Brazilian Real", "symbol": "R$", "decimal_places": 2},
        {"code": "MXN", "name": "Mexican Peso", "symbol": "$", "decimal_places": 2},
        {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$", "decimal_places": 2},
        {"code": "AUD", "name": "Australian Dollar", "symbol": "A$", "decimal_places": 2},
        {"code": "CHF", "name": "Swiss Franc", "symbol": "CHF", "decimal_places": 2},
        {"code": "CNY", "name": "Chinese Yuan", "symbol": "Y", "decimal_places": 2}
    ]

    # Sample exchange rates (USD base)
    DEFAULT_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 148.50,
        "ARS": 850.00,
        "BRL": 4.95,
        "MXN": 17.15,
        "CAD": 1.35,
        "AUD": 1.53,
        "CHF": 0.87,
        "CNY": 7.18
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._currencies = {c["code"]: c for c in cls.DEFAULT_CURRENCIES}
            cls._rates = {}
            cls._set_default_rates()
        return cls._instance

    @classmethod
    def _set_default_rates(cls):
        """Set default rates for today"""
        today = date.today().isoformat()
        cls._rates[today] = cls.DEFAULT_RATES.copy()

    def get_base_currency(self) -> str:
        """Get base currency code"""
        return self._base_currency

    def set_base_currency(self, code: str) -> bool:
        """Set base currency"""
        if code in self._currencies:
            self._base_currency = code
            return True
        return False

    def get_currencies(self, active_only: bool = True) -> List[dict]:
        """Get all currencies"""
        currencies = list(self._currencies.values())
        for c in currencies:
            c["is_base"] = c["code"] == self._base_currency
            c["current_rate"] = self.get_rate(c["code"])
        return currencies

    def get_currency(self, code: str) -> Optional[dict]:
        """Get a specific currency"""
        return self._currencies.get(code)

    def add_currency(self, code: str, name: str, symbol: str, decimal_places: int = 2) -> dict:
        """Add a new currency"""
        currency = {
            "code": code.upper(),
            "name": name,
            "symbol": symbol,
            "decimal_places": decimal_places,
            "active": True
        }
        self._currencies[code.upper()] = currency
        return currency

    def set_rate(self, code: str, rate: float, rate_date: str = None) -> dict:
        """Set exchange rate for a currency"""
        if rate_date is None:
            rate_date = date.today().isoformat()

        if rate_date not in self._rates:
            self._rates[rate_date] = {}

        self._rates[rate_date][code] = rate

        return {
            "code": code,
            "rate": rate,
            "date": rate_date
        }

    def get_rate(self, code: str, rate_date: str = None) -> float:
        """Get exchange rate for a currency"""
        if rate_date is None:
            rate_date = date.today().isoformat()

        # Try exact date
        if rate_date in self._rates and code in self._rates[rate_date]:
            return self._rates[rate_date][code]

        # Fallback to most recent rate
        for d in sorted(self._rates.keys(), reverse=True):
            if code in self._rates[d]:
                return self._rates[d][code]

        # Default rate
        return self.DEFAULT_RATES.get(code, 1.0)

    def get_all_rates(self, rate_date: str = None) -> Dict[str, float]:
        """Get all exchange rates for a date"""
        if rate_date is None:
            rate_date = date.today().isoformat()

        rates = self._rates.get(rate_date, {})
        if not rates:
            rates = self.DEFAULT_RATES.copy()

        return rates

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        rate_date: str = None
    ) -> dict:
        """Convert amount between currencies"""
        if from_currency == to_currency:
            return {
                "original_amount": amount,
                "converted_amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "rate": 1.0
            }

        from_rate = self.get_rate(from_currency, rate_date)
        to_rate = self.get_rate(to_currency, rate_date)

        # Convert through base currency
        base_amount = amount / from_rate if from_rate else amount
        converted = base_amount * to_rate

        # Round to currency decimal places
        to_currency_data = self.get_currency(to_currency)
        decimal_places = to_currency_data.get("decimal_places", 2) if to_currency_data else 2
        converted = round(converted, decimal_places)

        return {
            "original_amount": amount,
            "converted_amount": converted,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": to_rate / from_rate if from_rate else to_rate,
            "rate_date": rate_date or date.today().isoformat()
        }

    def convert_to_base(self, amount: float, from_currency: str, rate_date: str = None) -> float:
        """Convert amount to base currency"""
        result = self.convert(amount, from_currency, self._base_currency, rate_date)
        return result["converted_amount"]

    def format_currency(self, amount: float, currency_code: str) -> str:
        """Format amount with currency symbol"""
        currency = self.get_currency(currency_code)
        if not currency:
            return f"{amount:.2f}"

        decimal_places = currency.get("decimal_places", 2)
        symbol = currency.get("symbol", "")

        formatted = f"{amount:,.{decimal_places}f}"
        return f"{symbol}{formatted}"

    def get_historical_rates(self, currency_code: str, days: int = 30) -> List[dict]:
        """Get historical rates for a currency"""
        history = []
        today = date.today()

        for i in range(days):
            d = (today - timedelta(days=i)).isoformat()
            rate = self.get_rate(currency_code, d)
            history.append({
                "date": d,
                "rate": rate
            })

        return list(reversed(history))


currency_service = CurrencyService()
