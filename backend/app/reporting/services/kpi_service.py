"""KPI calculation service."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.accounting.models import Account, AccountType, JournalEntry, JournalEntryLine
from app.reporting.schemas.kpi import KPIValue, DashboardSummary


class KPIService:
    """Service for KPI calculations."""
    
    def __init__(self, db: Session, customer_id: UUID):
        self.db = db
        self.customer_id = customer_id
    
    async def get_dashboard_summary(self, as_of_date: Optional[date] = None) -> DashboardSummary:
        """Get executive dashboard summary."""
        if not as_of_date:
            as_of_date = date.today()
        
        year_start = date(as_of_date.year, 1, 1)
        
        total_revenue = await self._get_account_balance_ytd(
            year_start, as_of_date, [AccountType.REVENUE]
        )
        total_revenue = abs(total_revenue)
        
        total_expenses = await self._get_account_balance_ytd(
            year_start, as_of_date, [AccountType.EXPENSE]
        )
        
        net_income = total_revenue - total_expenses
        
        gross_margin = None
        cogs = await self._get_cogs_ytd(year_start, as_of_date)
        if total_revenue > 0:
            gross_profit = total_revenue - cogs
            gross_margin = (gross_profit / total_revenue * 100).quantize(Decimal("0.01"))
        
        net_margin = None
        if total_revenue > 0:
            net_margin = (net_income / total_revenue * 100).quantize(Decimal("0.01"))
        
        cash_balance = await self._get_account_balance("1000", as_of_date, prefix=True)
        ar_balance = await self._get_account_balance("1200", as_of_date, prefix=True)
        ap_balance = abs(await self._get_account_balance("2100", as_of_date, prefix=True))
        
        current_assets = await self._get_current_assets(as_of_date)
        current_liabilities = abs(await self._get_current_liabilities(as_of_date))
        
        current_ratio = None
        if current_liabilities > 0:
            current_ratio = (current_assets / current_liabilities).quantize(Decimal("0.01"))
        
        quick_assets = current_assets - await self._get_inventory_balance(as_of_date)
        quick_ratio = None
        if current_liabilities > 0:
            quick_ratio = (quick_assets / current_liabilities).quantize(Decimal("0.01"))
        
        revenue_trend = await self._get_monthly_trend(AccountType.REVENUE, as_of_date, 6)
        expense_trend = await self._get_monthly_trend(AccountType.EXPENSE, as_of_date, 6)
        
        kpis = await self.calculate_all_kpis(as_of_date)
        
        return DashboardSummary(
            as_of_date=datetime.combine(as_of_date, datetime.min.time()),
            total_revenue=total_revenue,
            total_expenses=total_expenses,
            net_income=net_income,
            gross_margin=gross_margin,
            net_margin=net_margin,
            cash_balance=cash_balance,
            ar_balance=ar_balance,
            ap_balance=ap_balance,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            revenue_trend=revenue_trend,
            expense_trend=expense_trend,
            kpis=kpis
        )
    
    async def calculate_all_kpis(self, as_of_date: date) -> List[KPIValue]:
        """Calculate all defined KPIs."""
        kpis = []
        kpis.extend(await self._calculate_liquidity_kpis(as_of_date))
        kpis.extend(await self._calculate_profitability_kpis(as_of_date))
        kpis.extend(await self._calculate_efficiency_kpis(as_of_date))
        return kpis
    
    async def _calculate_liquidity_kpis(self, as_of_date: date) -> List[KPIValue]:
        """Calculate liquidity KPIs."""
        kpis = []
        
        current_assets = await self._get_current_assets(as_of_date)
        current_liabilities = abs(await self._get_current_liabilities(as_of_date))
        inventory = await self._get_inventory_balance(as_of_date)
        cash = await self._get_account_balance("1000", as_of_date, prefix=True)
        
        if current_liabilities > 0:
            current_ratio = (current_assets / current_liabilities).quantize(Decimal("0.01"))
            status = "normal"
            if current_ratio < Decimal("1.0"):
                status = "critical"
            elif current_ratio < Decimal("1.5"):
                status = "warning"
            
            kpis.append(KPIValue(
                kpi_id=UUID("00000000-0000-0000-0000-000000000001"),
                code="CURRENT_RATIO",
                name="Current Ratio",
                category="liquidity",
                value=current_ratio,
                formatted_value=f"{current_ratio}x",
                target=Decimal("2.0"),
                status=status
            ))
        
        if current_liabilities > 0:
            quick_ratio = ((current_assets - inventory) / current_liabilities).quantize(Decimal("0.01"))
            status = "normal"
            if quick_ratio < Decimal("0.5"):
                status = "critical"
            elif quick_ratio < Decimal("1.0"):
                status = "warning"
            
            kpis.append(KPIValue(
                kpi_id=UUID("00000000-0000-0000-0000-000000000002"),
                code="QUICK_RATIO",
                name="Quick Ratio",
                category="liquidity",
                value=quick_ratio,
                formatted_value=f"{quick_ratio}x",
                target=Decimal("1.0"),
                status=status
            ))
        
        if current_liabilities > 0:
            cash_ratio = (cash / current_liabilities).quantize(Decimal("0.01"))
            kpis.append(KPIValue(
                kpi_id=UUID("00000000-0000-0000-0000-000000000003"),
                code="CASH_RATIO",
                name="Cash Ratio",
                category="liquidity",
                value=cash_ratio,
                formatted_value=f"{cash_ratio}x",
                status="normal"
            ))
        
        return kpis
    
    async def _calculate_profitability_kpis(self, as_of_date: date) -> List[KPIValue]:
        """Calculate profitability KPIs."""
        kpis = []
        year_start = date(as_of_date.year, 1, 1)
        
        revenue = abs(await self._get_account_balance_ytd(year_start, as_of_date, [AccountType.REVENUE]))
        expenses = await self._get_account_balance_ytd(year_start, as_of_date, [AccountType.EXPENSE])
        cogs = await self._get_cogs_ytd(year_start, as_of_date)
        
        if revenue > 0:
            gross_profit = revenue - cogs
            gross_margin = (gross_profit / revenue * 100).quantize(Decimal("0.01"))
            kpis.append(KPIValue(
                kpi_id=UUID("00000000-0000-0000-0000-000000000004"),
                code="GROSS_MARGIN",
                name="Gross Margin",
                category="profitability",
                value=gross_margin,
                formatted_value=f"{gross_margin}%",
                target=Decimal("40.0"),
                status="normal" if gross_margin >= 30 else "warning"
            ))
            
            net_income = revenue - expenses
            net_margin = (net_income / revenue * 100).quantize(Decimal("0.01"))
            kpis.append(KPIValue(
                kpi_id=UUID("00000000-0000-0000-0000-000000000005"),
                code="NET_MARGIN",
                name="Net Profit Margin",
                category="profitability",
                value=net_margin,
                formatted_value=f"{net_margin}%",
                target=Decimal("15.0"),
                status="normal" if net_margin >= 10 else "warning"
            ))
            
            operating_expenses = expenses - cogs
            operating_income = gross_profit - operating_expenses
            operating_margin = (operating_income / revenue * 100).quantize(Decimal("0.01"))
            kpis.append(KPIValue(
                kpi_id=UUID("00000000-0000-0000-0000-000000000006"),
                code="OPERATING_MARGIN",
                name="Operating Margin",
                category="profitability",
                value=operating_margin,
                formatted_value=f"{operating_margin}%",
                target=Decimal("20.0"),
                status="normal"
            ))
        
        return kpis
    
    async def _calculate_efficiency_kpis(self, as_of_date: date) -> List[KPIValue]:
        """Calculate efficiency KPIs."""
        kpis = []
        year_start = date(as_of_date.year, 1, 1)
        
        revenue = abs(await self._get_account_balance_ytd(year_start, as_of_date, [AccountType.REVENUE]))
        ar_balance = await self._get_account_balance("1200", as_of_date, prefix=True)
        ap_balance = abs(await self._get_account_balance("2100", as_of_date, prefix=True))
        cogs = await self._get_cogs_ytd(year_start, as_of_date)
        
        days_in_year = (as_of_date - year_start).days + 1
        
        if revenue > 0:
            daily_sales = revenue / days_in_year
            if daily_sales > 0:
                dso = (ar_balance / daily_sales).quantize(Decimal("0.1"))
                kpis.append(KPIValue(
                    kpi_id=UUID("00000000-0000-0000-0000-000000000007"),
                    code="DSO",
                    name="Days Sales Outstanding",
                    category="efficiency",
                    value=dso,
                    formatted_value=f"{dso} days",
                    target=Decimal("45.0"),
                    status="normal" if dso <= 45 else "warning"
                ))
        
        if cogs > 0:
            daily_cogs = cogs / days_in_year
            if daily_cogs > 0:
                dpo = (ap_balance / daily_cogs).quantize(Decimal("0.1"))
                kpis.append(KPIValue(
                    kpi_id=UUID("00000000-0000-0000-0000-000000000008"),
                    code="DPO",
                    name="Days Payable Outstanding",
                    category="efficiency",
                    value=dpo,
                    formatted_value=f"{dpo} days",
                    status="normal"
                ))
        
        return kpis
    
    async def _get_account_balance(
        self,
        account_code: str,
        as_of_date: date,
        prefix: bool = False
    ) -> Decimal:
        """Get account balance as of date."""
        query = (
            select(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date <= as_of_date,
                JournalEntry.status == "posted"
            )
        )
        
        if prefix:
            query = query.where(Account.code.like(f"{account_code}%"))
        else:
            query = query.where(Account.code == account_code)
        
        result = self.db.execute(query)
        balance = result.scalar()
        return balance if balance else Decimal(0)
    
    async def _get_account_balance_ytd(
        self,
        start_date: date,
        end_date: date,
        account_types: List[AccountType]
    ) -> Decimal:
        """Get account balance for period."""
        query = (
            select(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.status == "posted",
                Account.account_type.in_(account_types)
            )
        )
        
        result = self.db.execute(query)
        balance = result.scalar()
        return balance if balance else Decimal(0)
    
    async def _get_cogs_ytd(self, start_date: date, end_date: date) -> Decimal:
        """Get Cost of Goods Sold YTD."""
        query = (
            select(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date,
                JournalEntry.status == "posted",
                Account.code.like("51%")
            )
        )
        
        result = self.db.execute(query)
        return result.scalar() or Decimal(0)
    
    async def _get_current_assets(self, as_of_date: date) -> Decimal:
        """Get total current assets."""
        query = (
            select(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date <= as_of_date,
                JournalEntry.status == "posted",
                Account.account_type == AccountType.ASSET,
                Account.code.like("1%"),
                Account.code < "1500"
            )
        )
        
        result = self.db.execute(query)
        return result.scalar() or Decimal(0)
    
    async def _get_current_liabilities(self, as_of_date: date) -> Decimal:
        """Get total current liabilities."""
        query = (
            select(func.sum(JournalEntryLine.debit - JournalEntryLine.credit))
            .join(JournalEntry)
            .join(Account)
            .where(
                JournalEntry.customer_id == self.customer_id,
                JournalEntry.entry_date <= as_of_date,
                JournalEntry.status == "posted",
                Account.account_type == AccountType.LIABILITY,
                Account.code.like("2%"),
                Account.code < "2500"
            )
        )
        
        result = self.db.execute(query)
        return result.scalar() or Decimal(0)
    
    async def _get_inventory_balance(self, as_of_date: date) -> Decimal:
        """Get inventory balance."""
        return await self._get_account_balance("1300", as_of_date, prefix=True)
    
    async def _get_monthly_trend(
        self,
        account_type: AccountType,
        as_of_date: date,
        months: int
    ) -> List[dict]:
        """Get monthly trend data."""
        trend = []
        
        for i in range(months - 1, -1, -1):
            month = as_of_date.month - i
            year = as_of_date.year
            while month <= 0:
                month += 12
                year -= 1
            
            from calendar import monthrange
            _, last_day = monthrange(year, month)
            month_start = date(year, month, 1)
            month_end = date(year, month, last_day)
            
            balance = await self._get_account_balance_ytd(month_start, month_end, [account_type])
            if account_type == AccountType.REVENUE:
                balance = abs(balance)
            
            trend.append({
                "period": f"{year}-{month:02d}",
                "value": float(balance)
            })
        
        return trend
