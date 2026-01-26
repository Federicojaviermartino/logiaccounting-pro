"""
Sales Module
Sales Orders & Customer Management

This module provides comprehensive sales management functionality including:
- Customer master data management
- Sales order processing
- Order fulfillment (picking and shipping)
- Customer invoicing and payments
- Accounts receivable aging
"""

from app.sales.customers import (
    CustomerMaster,
    CustomerContact,
    CustomerShippingAddress,
    CustomerPriceList,
    CustomerTypeEnum,
    CustomerSegmentEnum,
    CustomerService,
)

from app.sales.orders import (
    SalesOrder,
    SalesOrderLine,
    StockAllocation,
    SOStatusEnum,
    SOLineStatusEnum,
    PriorityEnum,
    SalesOrderService,
)

from app.sales.fulfillment import (
    PickList,
    PickListLine,
    Shipment,
    ShipmentLine,
    PickListStatusEnum,
    PickLineStatusEnum,
    ShipmentStatusEnum,
    PickListService,
    ShipmentService,
)

from app.sales.invoices import (
    CustomerInvoice,
    CustomerInvoiceLine,
    InvoicePayment,
    CustomerPayment,
    InvoiceStatusEnum,
    PaymentMethodEnum,
    InvoiceService,
    PaymentService,
)

from app.sales.routes import router


__all__ = [
    # Customer
    'CustomerMaster',
    'CustomerContact',
    'CustomerShippingAddress',
    'CustomerPriceList',
    'CustomerTypeEnum',
    'CustomerSegmentEnum',
    'CustomerService',
    # Orders
    'SalesOrder',
    'SalesOrderLine',
    'StockAllocation',
    'SOStatusEnum',
    'SOLineStatusEnum',
    'PriorityEnum',
    'SalesOrderService',
    # Fulfillment
    'PickList',
    'PickListLine',
    'Shipment',
    'ShipmentLine',
    'PickListStatusEnum',
    'PickLineStatusEnum',
    'ShipmentStatusEnum',
    'PickListService',
    'ShipmentService',
    # Invoices
    'CustomerInvoice',
    'CustomerInvoiceLine',
    'InvoicePayment',
    'CustomerPayment',
    'InvoiceStatusEnum',
    'PaymentMethodEnum',
    'InvoiceService',
    'PaymentService',
    # Router
    'router',
]
