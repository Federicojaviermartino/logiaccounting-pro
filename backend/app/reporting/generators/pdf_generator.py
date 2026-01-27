"""PDF report generator using ReportLab."""
from io import BytesIO
from decimal import Decimal

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.reporting.schemas.financial_statements import (
    BalanceSheetData, IncomeStatementData
)


class PDFReportGenerator:
    """Generate PDF reports for financial statements."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6
        ))
    
    def generate_balance_sheet(self, data: BalanceSheetData) -> BytesIO:
        """Generate Balance Sheet PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
        
        elements = []
        
        elements.append(Paragraph(data.company_name, self.styles['ReportTitle']))
        elements.append(Paragraph(
            f"Balance Sheet as of {data.report_date.strftime('%B %d, %Y')}",
            self.styles['Heading2']
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        table_data = [['Account', 'Amount']]
        
        table_data.append(['ASSETS', ''])
        table_data.append(['Current Assets', ''])
        for line in data.current_assets:
            indent = "    " * line.indent_level
            table_data.append([f'{indent}{line.label}', self._format_currency(line.current_period)])
        table_data.append(['Total Current Assets', self._format_currency(data.total_current_assets)])
        table_data.append(['', ''])
        
        table_data.append(['Non-Current Assets', ''])
        for line in data.non_current_assets:
            indent = "    " * line.indent_level
            table_data.append([f'{indent}{line.label}', self._format_currency(line.current_period)])
        table_data.append(['Total Non-Current Assets', self._format_currency(data.total_non_current_assets)])
        table_data.append(['', ''])
        
        table_data.append(['TOTAL ASSETS', self._format_currency(data.total_assets)])
        table_data.append(['', ''])
        
        table_data.append(['LIABILITIES', ''])
        table_data.append(['Current Liabilities', ''])
        for line in data.current_liabilities:
            indent = "    " * line.indent_level
            table_data.append([f'{indent}{line.label}', self._format_currency(line.current_period)])
        table_data.append(['Total Current Liabilities', self._format_currency(data.total_current_liabilities)])
        table_data.append(['', ''])
        
        table_data.append(['Non-Current Liabilities', ''])
        for line in data.non_current_liabilities:
            indent = "    " * line.indent_level
            table_data.append([f'{indent}{line.label}', self._format_currency(line.current_period)])
        table_data.append(['Total Non-Current Liabilities', self._format_currency(data.total_non_current_liabilities)])
        table_data.append(['', ''])
        
        table_data.append(['TOTAL LIABILITIES', self._format_currency(data.total_liabilities)])
        table_data.append(['', ''])
        
        table_data.append(['EQUITY', ''])
        for line in data.equity:
            indent = "    " * line.indent_level
            table_data.append([f'{indent}{line.label}', self._format_currency(line.current_period)])
        table_data.append(['TOTAL EQUITY', self._format_currency(data.total_equity)])
        table_data.append(['', ''])
        
        table_data.append(['TOTAL LIABILITIES & EQUITY', self._format_currency(data.total_liabilities_and_equity)])
        
        table = Table(table_data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generate_income_statement(self, data: IncomeStatementData) -> BytesIO:
        """Generate Income Statement PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
        
        elements = []
        
        elements.append(Paragraph(data.company_name, self.styles['ReportTitle']))
        elements.append(Paragraph(
            f"Income Statement: {data.period_start.strftime('%b %d, %Y')} - {data.period_end.strftime('%b %d, %Y')}",
            self.styles['Heading2']
        ))
        elements.append(Spacer(1, 0.3*inch))
        
        table_data = [['Account', 'Amount', '% of Revenue']]
        
        table_data.append(['REVENUE', '', ''])
        for line in data.revenue:
            table_data.append([f'    {line.label}', self._format_currency(line.current_period), ''])
        table_data.append(['Total Revenue', self._format_currency(data.total_revenue), '100.00%'])
        table_data.append(['', '', ''])
        
        table_data.append(['COST OF SALES', '', ''])
        for line in data.cost_of_sales:
            table_data.append([f'    {line.label}', self._format_currency(line.current_period), ''])
        table_data.append(['Total Cost of Sales', self._format_currency(data.total_cost_of_sales), ''])
        table_data.append(['', '', ''])
        
        margin_pct = f"{float(data.gross_margin_percent):.2f}%" if data.gross_margin_percent else ''
        table_data.append(['GROSS PROFIT', self._format_currency(data.gross_profit), margin_pct])
        table_data.append(['', '', ''])
        
        table_data.append(['OPERATING EXPENSES', '', ''])
        for line in data.operating_expenses:
            table_data.append([f'    {line.label}', self._format_currency(line.current_period), ''])
        table_data.append(['Total Operating Expenses', self._format_currency(data.total_operating_expenses), ''])
        table_data.append(['', '', ''])
        
        net_margin = f"{float(data.net_margin_percent):.2f}%" if data.net_margin_percent else ''
        table_data.append(['NET INCOME', self._format_currency(data.net_income), net_margin])
        
        table = Table(table_data, colWidths=[3.5*inch, 1.5*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def _format_currency(self, value: Decimal) -> str:
        """Format decimal as currency string."""
        if value is None:
            return ''
        return f"${float(value):,.2f}"
