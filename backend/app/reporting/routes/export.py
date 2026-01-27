"""Report export API routes (PDF, Excel)."""
from datetime import date
from typing import Optional
from uuid import UUID
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.reporting.services.financial_statement_service import FinancialStatementService
from app.reporting.generators.excel_generator import ExcelReportGenerator
from app.reporting.generators.pdf_generator import PDFReportGenerator

router = APIRouter(prefix="/export", tags=["Report Export"])


@router.get("/balance-sheet/excel")
async def export_balance_sheet_excel(
    as_of_date: date = Query(...),
    compare_prior_period: bool = Query(False),
    department_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export Balance Sheet to Excel."""
    service = FinancialStatementService(db, current_user.customer_id)
    data = await service.generate_balance_sheet(
        as_of_date=as_of_date,
        compare_prior_period=compare_prior_period,
        department_id=department_id
    )
    
    generator = ExcelReportGenerator()
    buffer = generator.generate_balance_sheet(data)
    
    filename = f"balance_sheet_{as_of_date.isoformat()}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/income-statement/excel")
async def export_income_statement_excel(
    start_date: date = Query(...),
    end_date: date = Query(...),
    compare_prior_period: bool = Query(False),
    department_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export Income Statement to Excel."""
    service = FinancialStatementService(db, current_user.customer_id)
    data = await service.generate_income_statement(
        start_date=start_date,
        end_date=end_date,
        compare_prior_period=compare_prior_period,
        department_id=department_id
    )
    
    generator = ExcelReportGenerator()
    buffer = generator.generate_income_statement(data)
    
    filename = f"income_statement_{start_date.isoformat()}_to_{end_date.isoformat()}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/trial-balance/excel")
async def export_trial_balance_excel(
    as_of_date: date = Query(...),
    department_id: Optional[UUID] = None,
    show_zero_balances: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export Trial Balance to Excel."""
    service = FinancialStatementService(db, current_user.customer_id)
    data = await service.generate_trial_balance(
        as_of_date=as_of_date,
        department_id=department_id,
        show_zero_balances=show_zero_balances
    )
    
    generator = ExcelReportGenerator()
    buffer = generator.generate_trial_balance(data)
    
    filename = f"trial_balance_{as_of_date.isoformat()}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/balance-sheet/pdf")
async def export_balance_sheet_pdf(
    as_of_date: date = Query(...),
    compare_prior_period: bool = Query(False),
    department_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export Balance Sheet to PDF."""
    service = FinancialStatementService(db, current_user.customer_id)
    data = await service.generate_balance_sheet(
        as_of_date=as_of_date,
        compare_prior_period=compare_prior_period,
        department_id=department_id
    )
    
    generator = PDFReportGenerator()
    buffer = generator.generate_balance_sheet(data)
    
    filename = f"balance_sheet_{as_of_date.isoformat()}.pdf"
    
    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/income-statement/pdf")
async def export_income_statement_pdf(
    start_date: date = Query(...),
    end_date: date = Query(...),
    compare_prior_period: bool = Query(False),
    department_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export Income Statement to PDF."""
    service = FinancialStatementService(db, current_user.customer_id)
    data = await service.generate_income_statement(
        start_date=start_date,
        end_date=end_date,
        compare_prior_period=compare_prior_period,
        department_id=department_id
    )
    
    generator = PDFReportGenerator()
    buffer = generator.generate_income_statement(data)
    
    filename = f"income_statement_{start_date.isoformat()}_to_{end_date.isoformat()}.pdf"
    
    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
