"""
Customers Module
Customer management for sales
"""

from app.sales.customers.models import (
    CustomerMaster,
    CustomerContact,
    CustomerShippingAddress,
    CustomerPriceList,
    CustomerTypeEnum,
    CustomerSegmentEnum,
)

from app.sales.customers.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerFilter,
    CustomerSummary,
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ShippingAddressCreate,
    ShippingAddressUpdate,
    ShippingAddressResponse,
    PriceListCreate,
    PriceListUpdate,
    PriceListResponse,
    AddressSchema,
    CreditHoldRequest,
    CreditLimitUpdate,
)

from app.sales.customers.service import (
    CustomerService,
    get_customer_service,
)


__all__ = [
    'CustomerMaster',
    'CustomerContact',
    'CustomerShippingAddress',
    'CustomerPriceList',
    'CustomerTypeEnum',
    'CustomerSegmentEnum',
    'CustomerCreate',
    'CustomerUpdate',
    'CustomerResponse',
    'CustomerFilter',
    'CustomerSummary',
    'ContactCreate',
    'ContactUpdate',
    'ContactResponse',
    'ShippingAddressCreate',
    'ShippingAddressUpdate',
    'ShippingAddressResponse',
    'PriceListCreate',
    'PriceListUpdate',
    'PriceListResponse',
    'AddressSchema',
    'CreditHoldRequest',
    'CreditLimitUpdate',
    'CustomerService',
    'get_customer_service',
]
