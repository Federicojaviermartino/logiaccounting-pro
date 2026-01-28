"""
Exchange rate providers and management.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional
import httpx

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class ExchangeRate:
    """Exchange rate data."""
    from_currency: str
    to_currency: str
    rate: float
    timestamp: datetime = field(default_factory=utc_now)
    provider: str = "unknown"

    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Check if rate is stale."""
        age = utc_now() - self.timestamp
        return age > timedelta(hours=max_age_hours)

    def convert(self, amount: float) -> float:
        """Convert amount using this rate."""
        return amount * self.rate

    def inverse(self) -> "ExchangeRate":
        """Get inverse rate."""
        return ExchangeRate(
            from_currency=self.to_currency,
            to_currency=self.from_currency,
            rate=1.0 / self.rate if self.rate != 0 else 0,
            timestamp=self.timestamp,
            provider=self.provider,
        )


class ExchangeRateProvider(ABC):
    """Base class for exchange rate providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    async def get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Get exchange rate."""
        pass

    @abstractmethod
    async def get_rates(
        self,
        base_currency: str
    ) -> Dict[str, ExchangeRate]:
        """Get all rates for a base currency."""
        pass


class ECBProvider(ExchangeRateProvider):
    """European Central Bank exchange rate provider."""

    API_URL = "https://api.frankfurter.app"

    @property
    def name(self) -> str:
        return "ECB"

    async def get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Get exchange rate from ECB."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_URL}/latest",
                    params={"from": from_currency, "to": to_currency}
                )
                response.raise_for_status()
                data = response.json()

                rate = data.get("rates", {}).get(to_currency)
                if rate:
                    return ExchangeRate(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=float(rate),
                        timestamp=datetime.fromisoformat(data["date"]),
                        provider=self.name,
                    )
        except Exception as e:
            logger.error(f"ECB rate fetch failed: {e}")
        return None

    async def get_rates(
        self,
        base_currency: str
    ) -> Dict[str, ExchangeRate]:
        """Get all rates from ECB."""
        rates = {}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_URL}/latest",
                    params={"from": base_currency}
                )
                response.raise_for_status()
                data = response.json()

                timestamp = datetime.fromisoformat(data["date"])
                for currency, rate in data.get("rates", {}).items():
                    rates[currency] = ExchangeRate(
                        from_currency=base_currency,
                        to_currency=currency,
                        rate=float(rate),
                        timestamp=timestamp,
                        provider=self.name,
                    )
        except Exception as e:
            logger.error(f"ECB rates fetch failed: {e}")
        return rates


class OpenExchangeRatesProvider(ExchangeRateProvider):
    """Open Exchange Rates provider."""

    API_URL = "https://openexchangerates.org/api"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "OpenExchangeRates"

    async def get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Get exchange rate."""
        rates = await self.get_rates(from_currency)
        return rates.get(to_currency)

    async def get_rates(
        self,
        base_currency: str
    ) -> Dict[str, ExchangeRate]:
        """Get all rates."""
        rates = {}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_URL}/latest.json",
                    params={"app_id": self.api_key, "base": base_currency}
                )
                response.raise_for_status()
                data = response.json()

                timestamp = datetime.fromtimestamp(data["timestamp"])
                for currency, rate in data.get("rates", {}).items():
                    rates[currency] = ExchangeRate(
                        from_currency=base_currency,
                        to_currency=currency,
                        rate=float(rate),
                        timestamp=timestamp,
                        provider=self.name,
                    )
        except Exception as e:
            logger.error(f"OpenExchangeRates fetch failed: {e}")
        return rates


class ExchangeRateCache:
    """In-memory exchange rate cache."""

    def __init__(self, max_age_hours: int = 24):
        self._cache: Dict[str, ExchangeRate] = {}
        self.max_age_hours = max_age_hours

    def _key(self, from_currency: str, to_currency: str) -> str:
        return f"{from_currency}:{to_currency}"

    def get(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Get rate from cache."""
        key = self._key(from_currency, to_currency)
        rate = self._cache.get(key)
        if rate and not rate.is_stale(self.max_age_hours):
            return rate
        return None

    def set(self, rate: ExchangeRate) -> None:
        """Set rate in cache."""
        key = self._key(rate.from_currency, rate.to_currency)
        self._cache[key] = rate

    def set_all(self, rates: Dict[str, ExchangeRate]) -> None:
        """Set multiple rates."""
        for rate in rates.values():
            self.set(rate)

    def clear(self) -> None:
        """Clear all cached rates."""
        self._cache.clear()


class ExchangeRateService:
    """Exchange rate service with caching and fallback."""

    def __init__(
        self,
        providers: Optional[list] = None,
        cache_hours: int = 24
    ):
        self.providers = providers or [ECBProvider()]
        self.cache = ExchangeRateCache(cache_hours)

    async def get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Get exchange rate with caching."""
        if from_currency == to_currency:
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=1.0,
                provider="identity",
            )

        cached = self.cache.get(from_currency, to_currency)
        if cached:
            return cached

        for provider in self.providers:
            rate = await provider.get_rate(from_currency, to_currency)
            if rate:
                self.cache.set(rate)
                return rate

        return None

    async def refresh_rates(self, base_currency: str = "USD") -> None:
        """Refresh all rates from providers."""
        for provider in self.providers:
            rates = await provider.get_rates(base_currency)
            self.cache.set_all(rates)
            if rates:
                break


exchange_service = ExchangeRateService()
