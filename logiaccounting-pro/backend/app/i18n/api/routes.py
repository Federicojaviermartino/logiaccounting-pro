"""
API routes for internationalization features.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.i18n.config import I18nConfig
from app.i18n.currency.config import CurrencyConfig
from app.i18n.currency.exchange import exchange_service
from app.i18n.currency.converter import CurrencyConverter
from app.i18n.tax.eu_vat import EUVATEngine, EU_VAT_RATES
from app.i18n.tax.us_sales import USSalesTaxEngine, US_STATE_RATES
from app.i18n.tax.validation import validate_vat_number
from app.i18n.translation.loader import TranslationLoader
from app.i18n.datetime.timezone import TimezoneManager

router = APIRouter(prefix="/i18n", tags=["Internationalization"])


# ============ Response Models ============

class LanguageResponse(BaseModel):
    code: str
    name: str
    native_name: str
    direction: str
    fallback: Optional[str] = None


class CurrencyResponse(BaseModel):
    code: str
    name: str
    symbol: str
    decimal_places: int
    symbol_position: str


class ExchangeRateResponse(BaseModel):
    from_currency: str
    to_currency: str
    rate: float
    timestamp: str
    provider: str


class ConversionResponse(BaseModel):
    original_amount: float
    converted_amount: float
    from_currency: str
    to_currency: str
    rate: float
    formatted_original: str
    formatted_converted: str


class VATRateResponse(BaseModel):
    country_code: str
    country_name: str
    standard_rate: float
    reduced_rate: float
    reduced_rate_2: float
    super_reduced_rate: float


class TaxCalculationRequest(BaseModel):
    amount: float = Field(..., gt=0)
    country_code: str = Field(..., min_length=2, max_length=2)
    category: Optional[str] = None
    is_tax_included: bool = False


class TaxCalculationResponse(BaseModel):
    gross_amount: float
    net_amount: float
    tax_amount: float
    tax_rate: float
    tax_type: str
    region: str
    is_exempt: bool
    exempt_reason: Optional[str] = None


class VATValidationRequest(BaseModel):
    vat_number: str
    country_code: Optional[str] = None
    online: bool = False


class VATValidationResponse(BaseModel):
    valid: bool
    vat_number: str
    country_code: str
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    error: Optional[str] = None


class TimezoneResponse(BaseModel):
    id: str
    name: str
    offset: str
    label: str


# ============ Locale Routes ============

@router.get("/languages", response_model=List[LanguageResponse])
async def get_languages():
    """Get all supported languages."""
    languages = []
    for lang in I18nConfig.SUPPORTED_LANGUAGES:
        languages.append(LanguageResponse(
            code=lang.code,
            name=lang.name,
            native_name=lang.native_name,
            direction=lang.direction.value,
            fallback=lang.fallback,
        ))
    return languages


@router.get("/languages/{code}", response_model=LanguageResponse)
async def get_language(code: str):
    """Get a specific language."""
    lang = I18nConfig.get_language(code)
    if not lang:
        raise HTTPException(status_code=404, detail=f"Language not found: {code}")
    return LanguageResponse(
        code=lang.code,
        name=lang.name,
        native_name=lang.native_name,
        direction=lang.direction.value,
        fallback=lang.fallback,
    )


@router.get("/translations/{language}/{namespace}")
async def get_translations(language: str, namespace: str):
    """Get translations for a language and namespace."""
    translations = await TranslationLoader.load(language, namespace)
    if not translations:
        raise HTTPException(
            status_code=404,
            detail=f"Translations not found: {language}/{namespace}"
        )
    return translations


# ============ Currency Routes ============

@router.get("/currencies", response_model=List[CurrencyResponse])
async def get_currencies():
    """Get all supported currencies."""
    currencies = []
    for currency in CurrencyConfig.get_all_currencies():
        currencies.append(CurrencyResponse(
            code=currency.code,
            name=currency.name,
            symbol=currency.symbol,
            decimal_places=currency.decimal_places,
            symbol_position=currency.symbol_position.value,
        ))
    return currencies


@router.get("/currencies/{code}", response_model=CurrencyResponse)
async def get_currency(code: str):
    """Get a specific currency."""
    currency = CurrencyConfig.get_currency(code)
    if not currency:
        raise HTTPException(status_code=404, detail=f"Currency not found: {code}")
    return CurrencyResponse(
        code=currency.code,
        name=currency.name,
        symbol=currency.symbol,
        decimal_places=currency.decimal_places,
        symbol_position=currency.symbol_position.value,
    )


@router.get("/exchange-rate", response_model=ExchangeRateResponse)
async def get_exchange_rate(
    from_currency: str = Query(..., min_length=3, max_length=3),
    to_currency: str = Query(..., min_length=3, max_length=3)
):
    """Get exchange rate between two currencies."""
    rate = await exchange_service.get_rate(from_currency.upper(), to_currency.upper())
    if not rate:
        raise HTTPException(
            status_code=404,
            detail=f"Exchange rate not found: {from_currency} to {to_currency}"
        )
    return ExchangeRateResponse(
        from_currency=rate.from_currency,
        to_currency=rate.to_currency,
        rate=rate.rate,
        timestamp=rate.timestamp.isoformat(),
        provider=rate.provider,
    )


@router.post("/convert", response_model=ConversionResponse)
async def convert_currency(
    amount: float = Query(..., gt=0),
    from_currency: str = Query(..., min_length=3, max_length=3),
    to_currency: str = Query(..., min_length=3, max_length=3)
):
    """Convert amount between currencies."""
    result = await CurrencyConverter.convert(
        amount,
        from_currency.upper(),
        to_currency.upper()
    )
    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"Conversion failed: {from_currency} to {to_currency}"
        )
    return ConversionResponse(
        original_amount=result.original_amount,
        converted_amount=result.converted_amount,
        from_currency=result.from_currency,
        to_currency=result.to_currency,
        rate=result.rate,
        formatted_original=result.formatted_original,
        formatted_converted=result.formatted_converted,
    )


# ============ Tax Routes ============

@router.get("/tax/eu-vat-rates", response_model=List[VATRateResponse])
async def get_eu_vat_rates():
    """Get all EU VAT rates."""
    rates = []
    for code, rate in EU_VAT_RATES.items():
        rates.append(VATRateResponse(
            country_code=rate.country_code,
            country_name=rate.country_name,
            standard_rate=rate.standard_rate,
            reduced_rate=rate.reduced_rate,
            reduced_rate_2=rate.reduced_rate_2,
            super_reduced_rate=rate.super_reduced_rate,
        ))
    return rates


@router.get("/tax/us-sales-tax-rates")
async def get_us_sales_tax_rates():
    """Get all US state sales tax rates."""
    rates = []
    for code, rate in US_STATE_RATES.items():
        rates.append({
            "state_code": rate.state_code,
            "state_name": rate.state_name,
            "state_rate": rate.state_rate,
            "has_local_tax": rate.has_local_tax,
            "max_local_rate": rate.max_local_rate,
            "exempt_food": rate.exempt_food,
            "exempt_clothing": rate.exempt_clothing,
        })
    return rates


@router.post("/tax/calculate/eu-vat", response_model=TaxCalculationResponse)
async def calculate_eu_vat(request: TaxCalculationRequest):
    """Calculate EU VAT for an amount."""
    try:
        engine = EUVATEngine(request.country_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = engine.calculate(
        request.amount,
        category=request.category,
        is_tax_included=request.is_tax_included,
    )

    return TaxCalculationResponse(
        gross_amount=result.gross_amount,
        net_amount=result.net_amount,
        tax_amount=result.tax_amount,
        tax_rate=result.tax_rate,
        tax_type=result.tax_type.value,
        region=result.region,
        is_exempt=result.is_exempt,
        exempt_reason=result.exempt_reason,
    )


@router.post("/tax/calculate/us-sales", response_model=TaxCalculationResponse)
async def calculate_us_sales_tax(
    amount: float = Query(..., gt=0),
    state_code: str = Query(..., min_length=2, max_length=2),
    local_rate: float = Query(0, ge=0),
    category: Optional[str] = None,
    is_tax_included: bool = False
):
    """Calculate US Sales Tax for an amount."""
    try:
        engine = USSalesTaxEngine(state_code, local_rate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = engine.calculate(
        amount,
        category=category,
        is_tax_included=is_tax_included,
    )

    return TaxCalculationResponse(
        gross_amount=result.gross_amount,
        net_amount=result.net_amount,
        tax_amount=result.tax_amount,
        tax_rate=result.tax_rate,
        tax_type=result.tax_type.value,
        region=result.region,
        is_exempt=result.is_exempt,
        exempt_reason=result.exempt_reason,
    )


@router.post("/tax/validate-vat", response_model=VATValidationResponse)
async def validate_vat(request: VATValidationRequest):
    """Validate a VAT number."""
    result = await validate_vat_number(
        request.vat_number,
        request.country_code,
        online=request.online,
    )

    return VATValidationResponse(
        valid=result.valid,
        vat_number=result.vat_number,
        country_code=result.country_code,
        company_name=result.company_name,
        company_address=result.company_address,
        error=result.error,
    )


# ============ Timezone Routes ============

@router.get("/timezones", response_model=List[TimezoneResponse])
async def get_timezones():
    """Get common timezones."""
    timezones = TimezoneManager.get_common_timezones()
    return [TimezoneResponse(**tz) for tz in timezones]
