#!/usr/bin/env python3
"""
Consolidated SAP S/4HANA OData API Manager (SD, MM, AR, AP)
Contains all business domain functions:
- Sales Orders (SD): create_sales_order, get_sales_order, update_sales_order
- Material Stock (MM): get_material_stock
- Customer Credit (AR): get_customer_credit_status
- Accounts Payable (AP): create_supplier_invoice
"""

import json
import urllib.parse
from sap_auth import execute_sap_request, execute_sap_batch_request

# APIM Base Paths
APIM_SALES_ORDER_BASE = "/MS_DEMOS_API_SALES_ORDER_SRV"
APIM_MATERIAL_STOCK_BASE = "/API_MATERIAL_STOCK_SRV"
APIM_CREDIT_MANAGEMENT_BASE = "/API_CRDTMBUSINESSPARTNER"
APIM_INVOICE_BASE = "/MS_API_SUPPLIERINVOICE_PROCESS_SRV"


# ============================================================================
# 1. SALES ORDERS (SD MODULE)
# ============================================================================

def create_sales_order(
    user_token: str, 
    customer_id: str = "17100003", 
    po_reference: str = "EXECUTIVE-DEMO-001",
    material_id: str = "MZ-FG-R100",
    quantity: str = "10",
    plant: str = "1710"
) -> str:
    """
    Creates a Sales Order in SAP S/4HANA using OData $batch POST with dynamic line items.
    """
    qty_clean = str(quantity).upper().replace("PCS", "").replace("PC", "").strip()
    if not qty_clean or not qty_clean.isdigit():
        qty_clean = "10"

    batch_payload = (
        "--batch_req\r\n"
        "Content-Type: multipart/mixed; boundary=changeset_create\r\n\r\n"
        "--changeset_create\r\n"
        "Content-Type: application/http\r\n"
        "Content-Transfer-Encoding: binary\r\n\r\n"
        "POST A_SalesOrder HTTP/1.1\r\n"
        "Content-Type: application/json\r\n"
        "Accept: application/json\r\n\r\n"
        "{\r\n"
        '  "SalesOrderType": "OR",\r\n'
        '  "SalesOrganization": "1710",\r\n'
        '  "DistributionChannel": "10",\r\n'
        '  "OrganizationDivision": "00",\r\n'
        f'  "SoldToParty": "{customer_id}",\r\n'
        f'  "PurchaseOrderByCustomer": "{po_reference}",\r\n'
        '  "to_Item": [\r\n'
        "    {\r\n"
        '      "SalesOrderItem": "10",\r\n'
        f'      "Material": "{material_id}",\r\n'
        f'      "RequestedQuantity": "{qty_clean}",\r\n'
        '      "RequestedQuantityUnit": "PC",\r\n'
        f'      "ProductionPlant": "{plant}"\r\n'
        "    }\r\n"
        "  ]\r\n"
        "}\r\n\r\n"
        "--changeset_create--\r\n"
        "--batch_req--"
    )
    
    res = execute_sap_batch_request(
        user_token=user_token,
        apim_base_path=APIM_SALES_ORDER_BASE,
        batch_body=batch_payload
    )
    return res


def get_sales_order(user_token: str, sales_order_id: str) -> dict:
    """
    Reads Header + to_Item Line Items & Plant for a Sales Order.
    Zero-pads order ID to 10 digits (e.g. 5159 -> 0000005159).
    """
    formatted_id = sales_order_id.zfill(10)
    endpoint = f"/A_SalesOrder('{formatted_id}')?$expand=to_Item"
    
    return execute_sap_request(
        user_token=user_token,
        apim_base_path=APIM_SALES_ORDER_BASE,
        endpoint_path=endpoint,
        method="GET"
    )


def update_sales_order(user_token: str, sales_order_id: str, update_fields: dict) -> dict:
    """
    Updates Sales Order attributes (e.g. PurchaseOrderByCustomer) using PATCH / MERGE.
    """
    formatted_id = sales_order_id.zfill(10)
    endpoint = f"/A_SalesOrder('{formatted_id}')"
    
    return execute_sap_request(
        user_token=user_token,
        apim_base_path=APIM_SALES_ORDER_BASE,
        endpoint_path=endpoint,
        method="PATCH",
        payload=update_fields
    )


# ============================================================================
# 2. MATERIAL STOCK (MM MODULE)
# ============================================================================

def get_material_stock(user_token: str, material_id: str = "MZ-FG-R100", plant_id: str = "1710") -> dict:
    """
    Queries live warehouse inventory stock quantity, plant, and storage location.
    """
    encoded_material = urllib.parse.quote(material_id)
    encoded_plant = urllib.parse.quote(plant_id)
    endpoint = f"/A_MatlStkInAcctModif?%24filter=Material%20eq%20'{encoded_material}'%20and%20Plant%20eq%20'{encoded_plant}'"
    
    return execute_sap_request(
        user_token=user_token,
        apim_base_path=APIM_MATERIAL_STOCK_BASE,
        endpoint_path=endpoint,
        method="GET"
    )


# ============================================================================
# 3. CREDIT MANAGEMENT (AR MODULE)
# ============================================================================

def get_customer_credit_status(user_token: str, business_partner_id: str = "17100005") -> dict:
    """
    Queries FSCM Credit Limit and Risk Class for a Business Partner.
    """
    encoded_bp = urllib.parse.quote(business_partner_id)
    endpoint = f"/A_BusinessPartner('{encoded_bp}')/to_CreditAccountDetails"
    
    return execute_sap_request(
        user_token=user_token,
        apim_base_path=APIM_CREDIT_MANAGEMENT_BASE,
        endpoint_path=endpoint,
        method="GET"
    )


# ============================================================================
# 4. ACCOUNTS PAYABLE (AP MODULE)
# ============================================================================

def create_supplier_invoice(
    user_token: str, 
    supplier_id: str = "17100003", 
    invoice_amount: float = 500.0,
    company_code: str = "1710",
    currency: str = "USD"
) -> dict:
    """
    Posts a Supplier Invoice in Accounts Payable with dynamic posting date.
    """
    import time
    epoch_ms = int(time.time() * 1000)
    
    payload = {
        "CompanyCode": company_code,
        "DocumentCurrency": currency,
        "InvoiceGrossAmount": str(invoice_amount),
        "InvoicingParty": supplier_id,
        "DocumentDate": f"/Date({epoch_ms})/",
        "PostingDate": f"/Date({epoch_ms})/"
    }
    
    return execute_sap_request(
        user_token=user_token,
        apim_base_path=APIM_INVOICE_BASE,
        endpoint_path="/A_SupplierInvoice",
        method="POST",
        payload=payload
    )
