"""
Chart of Accounts Templates
Predefined account structures for different standards and business types
"""

from typing import Dict, List, Any
from app.accounting.chart_of_accounts.schemas import AccountTypeEnum


# ============== US GAAP Standard Template ==============

US_GAAP_TEMPLATE = {
    "name": "US GAAP Standard",
    "description": "Standard chart of accounts following US GAAP principles",
    "accounts": [
        # ASSETS (1XXX)
        {"code": "1000", "name": "Assets", "type": AccountTypeEnum.ASSET, "is_header": True},

        # Current Assets (11XX)
        {"code": "1100", "name": "Current Assets", "type": AccountTypeEnum.ASSET, "parent_code": "1000", "is_header": True},
        {"code": "1110", "name": "Cash and Cash Equivalents", "type": AccountTypeEnum.ASSET, "parent_code": "1100", "is_header": True},
        {"code": "1111", "name": "Operating Cash Account", "type": AccountTypeEnum.ASSET, "parent_code": "1110"},
        {"code": "1112", "name": "Petty Cash", "type": AccountTypeEnum.ASSET, "parent_code": "1110"},
        {"code": "1113", "name": "Savings Account", "type": AccountTypeEnum.ASSET, "parent_code": "1110"},

        {"code": "1200", "name": "Accounts Receivable", "type": AccountTypeEnum.ASSET, "parent_code": "1100", "is_header": True},
        {"code": "1210", "name": "Trade Receivables", "type": AccountTypeEnum.ASSET, "parent_code": "1200"},
        {"code": "1220", "name": "Allowance for Doubtful Accounts", "type": AccountTypeEnum.ASSET, "parent_code": "1200"},
        {"code": "1230", "name": "Employee Receivables", "type": AccountTypeEnum.ASSET, "parent_code": "1200"},

        {"code": "1300", "name": "Inventory", "type": AccountTypeEnum.ASSET, "parent_code": "1100", "is_header": True},
        {"code": "1310", "name": "Raw Materials", "type": AccountTypeEnum.ASSET, "parent_code": "1300"},
        {"code": "1320", "name": "Work in Progress", "type": AccountTypeEnum.ASSET, "parent_code": "1300"},
        {"code": "1330", "name": "Finished Goods", "type": AccountTypeEnum.ASSET, "parent_code": "1300"},

        {"code": "1400", "name": "Prepaid Expenses", "type": AccountTypeEnum.ASSET, "parent_code": "1100", "is_header": True},
        {"code": "1410", "name": "Prepaid Insurance", "type": AccountTypeEnum.ASSET, "parent_code": "1400"},
        {"code": "1420", "name": "Prepaid Rent", "type": AccountTypeEnum.ASSET, "parent_code": "1400"},
        {"code": "1430", "name": "Other Prepaid Expenses", "type": AccountTypeEnum.ASSET, "parent_code": "1400"},

        # Non-Current Assets (15XX)
        {"code": "1500", "name": "Non-Current Assets", "type": AccountTypeEnum.ASSET, "parent_code": "1000", "is_header": True},
        {"code": "1510", "name": "Property, Plant & Equipment", "type": AccountTypeEnum.ASSET, "parent_code": "1500", "is_header": True},
        {"code": "1511", "name": "Land", "type": AccountTypeEnum.ASSET, "parent_code": "1510"},
        {"code": "1512", "name": "Buildings", "type": AccountTypeEnum.ASSET, "parent_code": "1510"},
        {"code": "1513", "name": "Machinery & Equipment", "type": AccountTypeEnum.ASSET, "parent_code": "1510"},
        {"code": "1514", "name": "Vehicles", "type": AccountTypeEnum.ASSET, "parent_code": "1510"},
        {"code": "1515", "name": "Furniture & Fixtures", "type": AccountTypeEnum.ASSET, "parent_code": "1510"},
        {"code": "1516", "name": "Computer Equipment", "type": AccountTypeEnum.ASSET, "parent_code": "1510"},

        {"code": "1590", "name": "Accumulated Depreciation", "type": AccountTypeEnum.ASSET, "parent_code": "1500", "is_header": True},
        {"code": "1591", "name": "Accum. Depr. - Buildings", "type": AccountTypeEnum.ASSET, "parent_code": "1590"},
        {"code": "1592", "name": "Accum. Depr. - Equipment", "type": AccountTypeEnum.ASSET, "parent_code": "1590"},
        {"code": "1593", "name": "Accum. Depr. - Vehicles", "type": AccountTypeEnum.ASSET, "parent_code": "1590"},

        # LIABILITIES (2XXX)
        {"code": "2000", "name": "Liabilities", "type": AccountTypeEnum.LIABILITY, "is_header": True},

        # Current Liabilities (21XX)
        {"code": "2100", "name": "Current Liabilities", "type": AccountTypeEnum.LIABILITY, "parent_code": "2000", "is_header": True},
        {"code": "2110", "name": "Accounts Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2100", "is_header": True},
        {"code": "2111", "name": "Trade Payables", "type": AccountTypeEnum.LIABILITY, "parent_code": "2110"},
        {"code": "2112", "name": "Accrued Expenses", "type": AccountTypeEnum.LIABILITY, "parent_code": "2110"},

        {"code": "2200", "name": "Taxes Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2100", "is_header": True},
        {"code": "2210", "name": "Sales Tax Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2200"},
        {"code": "2220", "name": "Income Tax Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2200"},
        {"code": "2230", "name": "Payroll Tax Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2200"},

        {"code": "2300", "name": "Payroll Liabilities", "type": AccountTypeEnum.LIABILITY, "parent_code": "2100", "is_header": True},
        {"code": "2310", "name": "Wages Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2300"},
        {"code": "2320", "name": "Benefits Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2300"},

        {"code": "2400", "name": "Short-Term Loans", "type": AccountTypeEnum.LIABILITY, "parent_code": "2100"},
        {"code": "2500", "name": "Unearned Revenue", "type": AccountTypeEnum.LIABILITY, "parent_code": "2100"},

        # Long-Term Liabilities (26XX)
        {"code": "2600", "name": "Long-Term Liabilities", "type": AccountTypeEnum.LIABILITY, "parent_code": "2000", "is_header": True},
        {"code": "2610", "name": "Long-Term Loans", "type": AccountTypeEnum.LIABILITY, "parent_code": "2600"},
        {"code": "2620", "name": "Bonds Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2600"},
        {"code": "2630", "name": "Lease Obligations", "type": AccountTypeEnum.LIABILITY, "parent_code": "2600"},

        # EQUITY (3XXX)
        {"code": "3000", "name": "Equity", "type": AccountTypeEnum.EQUITY, "is_header": True},
        {"code": "3100", "name": "Owner's Capital", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3200", "name": "Common Stock", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3300", "name": "Preferred Stock", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3400", "name": "Additional Paid-In Capital", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3500", "name": "Retained Earnings", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3600", "name": "Current Year Earnings", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3700", "name": "Dividends", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3800", "name": "Treasury Stock", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},

        # REVENUE (4XXX)
        {"code": "4000", "name": "Revenue", "type": AccountTypeEnum.REVENUE, "is_header": True},
        {"code": "4100", "name": "Sales Revenue", "type": AccountTypeEnum.REVENUE, "parent_code": "4000", "is_header": True},
        {"code": "4110", "name": "Product Sales", "type": AccountTypeEnum.REVENUE, "parent_code": "4100"},
        {"code": "4120", "name": "Service Revenue", "type": AccountTypeEnum.REVENUE, "parent_code": "4100"},
        {"code": "4130", "name": "Sales Returns & Allowances", "type": AccountTypeEnum.REVENUE, "parent_code": "4100"},
        {"code": "4140", "name": "Sales Discounts", "type": AccountTypeEnum.REVENUE, "parent_code": "4100"},

        {"code": "4200", "name": "Other Income", "type": AccountTypeEnum.REVENUE, "parent_code": "4000", "is_header": True},
        {"code": "4210", "name": "Interest Income", "type": AccountTypeEnum.REVENUE, "parent_code": "4200"},
        {"code": "4220", "name": "Dividend Income", "type": AccountTypeEnum.REVENUE, "parent_code": "4200"},
        {"code": "4230", "name": "Gain on Asset Sale", "type": AccountTypeEnum.REVENUE, "parent_code": "4200"},
        {"code": "4240", "name": "Other Miscellaneous Income", "type": AccountTypeEnum.REVENUE, "parent_code": "4200"},

        # EXPENSES (5XXX)
        {"code": "5000", "name": "Expenses", "type": AccountTypeEnum.EXPENSE, "is_header": True},

        # Cost of Goods Sold (51XX)
        {"code": "5100", "name": "Cost of Goods Sold", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5110", "name": "Direct Materials", "type": AccountTypeEnum.EXPENSE, "parent_code": "5100"},
        {"code": "5120", "name": "Direct Labor", "type": AccountTypeEnum.EXPENSE, "parent_code": "5100"},
        {"code": "5130", "name": "Manufacturing Overhead", "type": AccountTypeEnum.EXPENSE, "parent_code": "5100"},
        {"code": "5140", "name": "Purchase Discounts", "type": AccountTypeEnum.EXPENSE, "parent_code": "5100"},

        # Operating Expenses (52XX-59XX)
        {"code": "5200", "name": "Personnel Expenses", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5210", "name": "Salaries & Wages", "type": AccountTypeEnum.EXPENSE, "parent_code": "5200"},
        {"code": "5220", "name": "Employee Benefits", "type": AccountTypeEnum.EXPENSE, "parent_code": "5200"},
        {"code": "5230", "name": "Payroll Taxes", "type": AccountTypeEnum.EXPENSE, "parent_code": "5200"},
        {"code": "5240", "name": "Training & Development", "type": AccountTypeEnum.EXPENSE, "parent_code": "5200"},

        {"code": "5300", "name": "Facilities Expenses", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5310", "name": "Rent Expense", "type": AccountTypeEnum.EXPENSE, "parent_code": "5300"},
        {"code": "5320", "name": "Utilities", "type": AccountTypeEnum.EXPENSE, "parent_code": "5300"},
        {"code": "5330", "name": "Repairs & Maintenance", "type": AccountTypeEnum.EXPENSE, "parent_code": "5300"},
        {"code": "5340", "name": "Property Insurance", "type": AccountTypeEnum.EXPENSE, "parent_code": "5300"},

        {"code": "5400", "name": "Administrative Expenses", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5410", "name": "Office Supplies", "type": AccountTypeEnum.EXPENSE, "parent_code": "5400"},
        {"code": "5420", "name": "Telephone & Internet", "type": AccountTypeEnum.EXPENSE, "parent_code": "5400"},
        {"code": "5430", "name": "Professional Fees", "type": AccountTypeEnum.EXPENSE, "parent_code": "5400"},
        {"code": "5440", "name": "Bank Fees", "type": AccountTypeEnum.EXPENSE, "parent_code": "5400"},

        {"code": "5500", "name": "Sales & Marketing", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5510", "name": "Advertising", "type": AccountTypeEnum.EXPENSE, "parent_code": "5500"},
        {"code": "5520", "name": "Marketing", "type": AccountTypeEnum.EXPENSE, "parent_code": "5500"},
        {"code": "5530", "name": "Travel & Entertainment", "type": AccountTypeEnum.EXPENSE, "parent_code": "5500"},

        {"code": "5600", "name": "Depreciation & Amortization", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5610", "name": "Depreciation Expense", "type": AccountTypeEnum.EXPENSE, "parent_code": "5600"},
        {"code": "5620", "name": "Amortization Expense", "type": AccountTypeEnum.EXPENSE, "parent_code": "5600"},

        {"code": "5700", "name": "Interest Expense", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},

        {"code": "5800", "name": "Tax Expense", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5810", "name": "Income Tax Expense", "type": AccountTypeEnum.EXPENSE, "parent_code": "5800"},
        {"code": "5820", "name": "Other Taxes", "type": AccountTypeEnum.EXPENSE, "parent_code": "5800"},

        {"code": "5900", "name": "Other Expenses", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000", "is_header": True},
        {"code": "5910", "name": "Loss on Asset Sale", "type": AccountTypeEnum.EXPENSE, "parent_code": "5900"},
        {"code": "5920", "name": "Miscellaneous Expense", "type": AccountTypeEnum.EXPENSE, "parent_code": "5900"},
    ]
}


# ============== Small Business Simplified Template ==============

SMB_TEMPLATE = {
    "name": "Small Business Simplified",
    "description": "Simplified chart of accounts for small businesses",
    "accounts": [
        # ASSETS
        {"code": "1000", "name": "Assets", "type": AccountTypeEnum.ASSET, "is_header": True},
        {"code": "1100", "name": "Cash", "type": AccountTypeEnum.ASSET, "parent_code": "1000"},
        {"code": "1200", "name": "Accounts Receivable", "type": AccountTypeEnum.ASSET, "parent_code": "1000"},
        {"code": "1300", "name": "Inventory", "type": AccountTypeEnum.ASSET, "parent_code": "1000"},
        {"code": "1400", "name": "Prepaid Expenses", "type": AccountTypeEnum.ASSET, "parent_code": "1000"},
        {"code": "1500", "name": "Fixed Assets", "type": AccountTypeEnum.ASSET, "parent_code": "1000"},
        {"code": "1600", "name": "Accumulated Depreciation", "type": AccountTypeEnum.ASSET, "parent_code": "1000"},

        # LIABILITIES
        {"code": "2000", "name": "Liabilities", "type": AccountTypeEnum.LIABILITY, "is_header": True},
        {"code": "2100", "name": "Accounts Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2000"},
        {"code": "2200", "name": "Credit Cards", "type": AccountTypeEnum.LIABILITY, "parent_code": "2000"},
        {"code": "2300", "name": "Taxes Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2000"},
        {"code": "2400", "name": "Loans Payable", "type": AccountTypeEnum.LIABILITY, "parent_code": "2000"},

        # EQUITY
        {"code": "3000", "name": "Equity", "type": AccountTypeEnum.EQUITY, "is_header": True},
        {"code": "3100", "name": "Owner's Capital", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3200", "name": "Retained Earnings", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},
        {"code": "3300", "name": "Owner's Draw", "type": AccountTypeEnum.EQUITY, "parent_code": "3000"},

        # REVENUE
        {"code": "4000", "name": "Income", "type": AccountTypeEnum.REVENUE, "is_header": True},
        {"code": "4100", "name": "Sales", "type": AccountTypeEnum.REVENUE, "parent_code": "4000"},
        {"code": "4200", "name": "Service Income", "type": AccountTypeEnum.REVENUE, "parent_code": "4000"},
        {"code": "4300", "name": "Other Income", "type": AccountTypeEnum.REVENUE, "parent_code": "4000"},

        # EXPENSES
        {"code": "5000", "name": "Expenses", "type": AccountTypeEnum.EXPENSE, "is_header": True},
        {"code": "5100", "name": "Cost of Goods Sold", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5200", "name": "Payroll", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5300", "name": "Rent", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5400", "name": "Utilities", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5500", "name": "Insurance", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5600", "name": "Office Supplies", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5700", "name": "Advertising", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5800", "name": "Professional Fees", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
        {"code": "5900", "name": "Other Expenses", "type": AccountTypeEnum.EXPENSE, "parent_code": "5000"},
    ]
}


# ============== EU/IFRS Template ==============

IFRS_TEMPLATE = {
    "name": "IFRS International",
    "description": "International Financial Reporting Standards compliant chart of accounts",
    "accounts": [
        # Similar structure adapted for IFRS terminology
        # Non-current Assets first, then Current Assets
        {"code": "1000", "name": "Assets", "type": AccountTypeEnum.ASSET, "is_header": True},

        # Non-Current Assets
        {"code": "1100", "name": "Non-Current Assets", "type": AccountTypeEnum.ASSET, "parent_code": "1000", "is_header": True},
        {"code": "1110", "name": "Property, Plant and Equipment", "type": AccountTypeEnum.ASSET, "parent_code": "1100"},
        {"code": "1120", "name": "Intangible Assets", "type": AccountTypeEnum.ASSET, "parent_code": "1100"},
        {"code": "1130", "name": "Investment Property", "type": AccountTypeEnum.ASSET, "parent_code": "1100"},
        {"code": "1140", "name": "Financial Assets", "type": AccountTypeEnum.ASSET, "parent_code": "1100"},

        # Current Assets
        {"code": "1200", "name": "Current Assets", "type": AccountTypeEnum.ASSET, "parent_code": "1000", "is_header": True},
        {"code": "1210", "name": "Inventories", "type": AccountTypeEnum.ASSET, "parent_code": "1200"},
        {"code": "1220", "name": "Trade and Other Receivables", "type": AccountTypeEnum.ASSET, "parent_code": "1200"},
        {"code": "1230", "name": "Cash and Cash Equivalents", "type": AccountTypeEnum.ASSET, "parent_code": "1200"},

        # More accounts following IFRS structure...
    ]
}


# ============== Template Registry ==============

ACCOUNT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "us_gaap": US_GAAP_TEMPLATE,
    "smb": SMB_TEMPLATE,
    "ifrs": IFRS_TEMPLATE,
}


def get_template(name: str) -> Dict[str, Any]:
    """Get account template by name."""
    return ACCOUNT_TEMPLATES.get(name)


def get_available_templates() -> List[Dict[str, str]]:
    """Get list of available templates."""
    return [
        {
            "id": key,
            "name": template["name"],
            "description": template.get("description", ""),
            "account_count": len(template["accounts"]),
        }
        for key, template in ACCOUNT_TEMPLATES.items()
    ]
