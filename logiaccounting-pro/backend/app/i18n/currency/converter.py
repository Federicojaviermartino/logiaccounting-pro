"""
Currency conversion service.
"""
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from app.i18n.currency.config import CurrencyConfig, Currency
from app.i18n.currency.exchange import exchange_service, ExchangeRate


@dataclass
class ConversionResult:
    """Result of currency conversion."""
    original_amount: float
    converted_amount: float
    from_currency: str
    to_currency: str
    rate: float
    rate_timestamp: str

    @property
    def formatted_original(self) -> str:
        """Get formatted original amount."""
        currency = CurrencyConfig.get_currency(self.from_currency)
        if currency:
            return currency.format(self.original_amount)
        return f"{self.original_amount:.2f} {self.from_currency}"

    @property
    def formatted_converted(self) -> str:
        """Get formatted converted amount."""
        currency = CurrencyConfig.get_currency(self.to_currency)
        if currency:
            return currency.format(self.converted_amount)
        return f"{self.converted_amount:.2f} {self.to_currency}"


class CurrencyConverter:
    """Currency conversion operations."""

    @classmethod
    async def convert(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str,
        rate: Optional[ExchangeRate] = None
    ) -> Optional[ConversionResult]:
        """
        Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            rate: Optional exchange rate (fetches if not provided)

        Returns:
            ConversionResult or None if conversion failed
        """
        if from_currency == to_currency:
            return ConversionResult(
                original_amount=amount,
                converted_amount=amount,
                from_currency=from_currency,
                to_currency=to_currency,
                rate=1.0,
                rate_timestamp="",
            )

        if not rate:
            rate = await exchange_service.get_rate(from_currency, to_currency)

        if not rate:
            return None

        to_currency_config = CurrencyConfig.get_currency(to_currency)
        decimal_places = to_currency_config.decimal_places if to_currency_config else 2

        converted = Decimal(str(amount)) * Decimal(str(rate.rate))
        converted = float(converted.quantize(
            Decimal(10) ** -decimal_places,
            rounding=ROUND_HALF_UP
        ))

        return ConversionResult(
            original_amount=amount,
            converted_amount=converted,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate.rate,
            rate_timestamp=rate.timestamp.isoformat(),
        )

    @classmethod
    def convert_sync(
        cls,
        amount: float,
        from_currency: str,
        to_currency: str,
        rate: float
    ) -> ConversionResult:
        """
        Synchronous conversion with known rate.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            rate: Exchange rate

        Returns:
            ConversionResult
        """
        to_currency_config = CurrencyConfig.get_currency(to_currency)
        decimal_places = to_currency_config.decimal_places if to_currency_config else 2

        converted = Decimal(str(amount)) * Decimal(str(rate))
        converted = float(converted.quantize(
            Decimal(10) ** -decimal_places,
            rounding=ROUND_HALF_UP
        ))

        return ConversionResult(
            original_amount=amount,
            converted_amount=converted,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            rate_timestamp="",
        )

    @classmethod
    async def convert_to_base(
        cls,
        amount: float,
        from_currency: str
    ) -> Optional[ConversionResult]:
        """Convert to base currency (USD)."""
        return await cls.convert(
            amount,
            from_currency,
            CurrencyConfig.BASE_CURRENCY
        )

    @classmethod
    async def convert_from_base(
        cls,
        amount: float,
        to_currency: str
    ) -> Optional[ConversionResult]:
        """Convert from base currency (USD)."""
        return await cls.convert(
            amount,
            CurrencyConfig.BASE_CURRENCY,
            to_currency
        )


async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str
) -> Optional[ConversionResult]:
    """Shorthand for currency conversion."""
    return await CurrencyConverter.convert(amount, from_currency, to_currency)
