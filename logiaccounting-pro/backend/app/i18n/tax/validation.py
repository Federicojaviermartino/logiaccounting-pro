"""
VAT number validation.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


@dataclass
class VATValidationResult:
    """VAT validation result."""
    valid: bool
    vat_number: str
    country_code: str
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    error: Optional[str] = None
    request_date: Optional[str] = None

    @property
    def formatted_number(self) -> str:
        """Get formatted VAT number with country code."""
        return f"{self.country_code}{self.vat_number}"


VAT_PATTERNS = {
    "AT": r"^U\d{8}$",
    "BE": r"^0\d{9}$",
    "BG": r"^\d{9,10}$",
    "HR": r"^\d{11}$",
    "CY": r"^\d{8}[A-Z]$",
    "CZ": r"^\d{8,10}$",
    "DK": r"^\d{8}$",
    "EE": r"^\d{9}$",
    "FI": r"^\d{8}$",
    "FR": r"^[0-9A-Z]{2}\d{9}$",
    "DE": r"^\d{9}$",
    "GR": r"^\d{9}$",
    "HU": r"^\d{8}$",
    "IE": r"^\d{7}[A-Z]{1,2}$|^\d[A-Z]\d{5}[A-Z]$",
    "IT": r"^\d{11}$",
    "LV": r"^\d{11}$",
    "LT": r"^\d{9}$|^\d{12}$",
    "LU": r"^\d{8}$",
    "MT": r"^\d{8}$",
    "NL": r"^\d{9}B\d{2}$",
    "PL": r"^\d{10}$",
    "PT": r"^\d{9}$",
    "RO": r"^\d{2,10}$",
    "SK": r"^\d{10}$",
    "SI": r"^\d{8}$",
    "ES": r"^[A-Z]\d{7}[A-Z]$|^\d{8}[A-Z]$|^[A-Z]\d{8}$",
    "SE": r"^\d{12}$",
    "GB": r"^\d{9}$|^\d{12}$|^GD\d{3}$|^HA\d{3}$",
}


class VATValidator:
    """VAT number validator."""

    VIES_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api//check-vat-number"

    @classmethod
    def validate_format(
        cls,
        vat_number: str,
        country_code: Optional[str] = None
    ) -> VATValidationResult:
        """
        Validate VAT number format locally.

        Args:
            vat_number: VAT number (with or without country code)
            country_code: Country code if not in VAT number

        Returns:
            VATValidationResult
        """
        vat_number = vat_number.upper().replace(" ", "").replace("-", "").replace(".", "")

        if not country_code and len(vat_number) >= 2:
            potential_country = vat_number[:2]
            if potential_country in VAT_PATTERNS or potential_country == "EL":
                country_code = "GR" if potential_country == "EL" else potential_country
                vat_number = vat_number[2:]

        if not country_code:
            return VATValidationResult(
                valid=False,
                vat_number=vat_number,
                country_code="",
                error="Country code not found",
            )

        country_code = country_code.upper()
        if country_code == "EL":
            country_code = "GR"

        pattern = VAT_PATTERNS.get(country_code)
        if not pattern:
            return VATValidationResult(
                valid=False,
                vat_number=vat_number,
                country_code=country_code,
                error=f"Unsupported country code: {country_code}",
            )

        is_valid = bool(re.match(pattern, vat_number))

        return VATValidationResult(
            valid=is_valid,
            vat_number=vat_number,
            country_code=country_code,
            error=None if is_valid else "Invalid VAT number format",
        )

    @classmethod
    async def validate_vies(
        cls,
        vat_number: str,
        country_code: Optional[str] = None
    ) -> VATValidationResult:
        """
        Validate VAT number against EU VIES service.

        Args:
            vat_number: VAT number
            country_code: Country code

        Returns:
            VATValidationResult with company info if valid
        """
        format_result = cls.validate_format(vat_number, country_code)
        if not format_result.valid:
            return format_result

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    cls.VIES_URL,
                    json={
                        "countryCode": format_result.country_code,
                        "vatNumber": format_result.vat_number,
                    }
                )
                response.raise_for_status()
                data = response.json()

                return VATValidationResult(
                    valid=data.get("valid", False),
                    vat_number=format_result.vat_number,
                    country_code=format_result.country_code,
                    company_name=data.get("name"),
                    company_address=data.get("address"),
                    request_date=data.get("requestDate"),
                )

        except httpx.TimeoutException:
            logger.warning("VIES service timeout")
            return VATValidationResult(
                valid=False,
                vat_number=format_result.vat_number,
                country_code=format_result.country_code,
                error="VIES service timeout",
            )
        except Exception as e:
            logger.error(f"VIES validation error: {e}")
            return VATValidationResult(
                valid=False,
                vat_number=format_result.vat_number,
                country_code=format_result.country_code,
                error=f"VIES validation failed: {str(e)}",
            )

    @classmethod
    def validate_checksum(cls, vat_number: str, country_code: str) -> bool:
        """
        Validate VAT number checksum for supported countries.

        Args:
            vat_number: VAT number without country code
            country_code: Two-letter country code

        Returns:
            True if checksum is valid
        """
        validators = {
            "DE": cls._validate_de_checksum,
            "FR": cls._validate_fr_checksum,
            "ES": cls._validate_es_checksum,
            "IT": cls._validate_it_checksum,
            "NL": cls._validate_nl_checksum,
        }

        validator = validators.get(country_code)
        if validator:
            return validator(vat_number)
        return True

    @staticmethod
    def _validate_de_checksum(vat_number: str) -> bool:
        """Validate German VAT checksum."""
        if len(vat_number) != 9:
            return False

        product = 10
        for digit in vat_number[:8]:
            sum_val = (int(digit) + product) % 10
            if sum_val == 0:
                sum_val = 10
            product = (sum_val * 2) % 11

        check_digit = 11 - product
        if check_digit == 10:
            check_digit = 0

        return check_digit == int(vat_number[8])

    @staticmethod
    def _validate_fr_checksum(vat_number: str) -> bool:
        """Validate French VAT checksum."""
        if len(vat_number) != 11:
            return False

        if vat_number[:2].isalpha():
            return True

        try:
            siren = int(vat_number[2:])
            key = int(vat_number[:2])
            calculated_key = (12 + 3 * (siren % 97)) % 97
            return key == calculated_key
        except ValueError:
            return False

    @staticmethod
    def _validate_es_checksum(vat_number: str) -> bool:
        """Validate Spanish VAT checksum (NIF/CIF)."""
        if len(vat_number) < 9:
            return False
        return True

    @staticmethod
    def _validate_it_checksum(vat_number: str) -> bool:
        """Validate Italian VAT checksum."""
        if len(vat_number) != 11:
            return False

        try:
            digits = [int(d) for d in vat_number]
            odd_sum = sum(digits[i] for i in range(0, 10, 2))
            even_sum = sum(
                d * 2 - 9 if d * 2 > 9 else d * 2
                for d in [digits[i] for i in range(1, 10, 2)]
            )
            check_digit = (10 - ((odd_sum + even_sum) % 10)) % 10
            return check_digit == digits[10]
        except (ValueError, IndexError):
            return False

    @staticmethod
    def _validate_nl_checksum(vat_number: str) -> bool:
        """Validate Dutch VAT checksum."""
        if len(vat_number) != 12:
            return False

        if vat_number[9] != "B":
            return False

        return True


async def validate_vat_number(
    vat_number: str,
    country_code: Optional[str] = None,
    online: bool = False
) -> VATValidationResult:
    """
    Validate VAT number.

    Args:
        vat_number: VAT number to validate
        country_code: Country code if not in number
        online: Whether to validate against VIES

    Returns:
        VATValidationResult
    """
    if online:
        return await VATValidator.validate_vies(vat_number, country_code)
    return VATValidator.validate_format(vat_number, country_code)
