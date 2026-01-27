"""
Currency Management routes
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.currency_service import currency_service
from app.utils.auth import get_current_user, require_roles

router = APIRouter()


class SetRateRequest(BaseModel):
    code: str
    rate: float
    date: Optional[str] = None


class ConvertRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    date: Optional[str] = None


class AddCurrencyRequest(BaseModel):
    code: str
    name: str
    symbol: str
    decimal_places: int = 2


@router.get("")
async def get_currencies(current_user: dict = Depends(get_current_user)):
    """Get all currencies"""
    return {
        "currencies": currency_service.get_currencies(),
        "base_currency": currency_service.get_base_currency()
    }


@router.get("/rates")
async def get_rates(
    date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all exchange rates"""
    return {
        "rates": currency_service.get_all_rates(date),
        "date": date or "today",
        "base_currency": currency_service.get_base_currency()
    }


@router.post("/rates")
async def set_rate(
    request: SetRateRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Set exchange rate"""
    return currency_service.set_rate(request.code, request.rate, request.date)


@router.post("/convert")
async def convert(
    request: ConvertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Convert between currencies"""
    return currency_service.convert(
        request.amount,
        request.from_currency,
        request.to_currency,
        request.date
    )


@router.get("/{code}")
async def get_currency(
    code: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific currency"""
    currency = currency_service.get_currency(code.upper())
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return currency


@router.get("/{code}/history")
async def get_history(
    code: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get historical rates"""
    return {"history": currency_service.get_historical_rates(code.upper(), days)}


@router.post("")
async def add_currency(
    request: AddCurrencyRequest,
    current_user: dict = Depends(require_roles("admin"))
):
    """Add a new currency"""
    return currency_service.add_currency(
        request.code,
        request.name,
        request.symbol,
        request.decimal_places
    )


@router.post("/base/{code}")
async def set_base_currency(
    code: str,
    current_user: dict = Depends(require_roles("admin"))
):
    """Set base currency"""
    if currency_service.set_base_currency(code.upper()):
        return {"message": f"Base currency set to {code.upper()}"}
    raise HTTPException(status_code=404, detail="Currency not found")
