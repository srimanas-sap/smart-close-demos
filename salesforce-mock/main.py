import copy
import re
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Salesforce Lightning Mock Service", version="1.0.0")

# Initial Authoritative 10 Opportunities Dataset
INITIAL_OPPORTUNITIES: List[Dict[str, Any]] = [
    {
        "Id": "006Ws000003hK01IAE",
        "Name": "Permadyne - Add-On Business",
        "Amount": 187000.0,
        "StageName": "Proposal/Quote",
        "CloseDate": "2026-04-29",
        "AccountId": "001Ws000053hK4YIAU",
        "AccountNumber": "A83223763",
        "Account": {"Name": "Permadyne GmbH, LTD", "AccountNumber": "A83223763"},
        "OwnerAlias": "sancha",
        "Products__c": "Battery, High Capacity",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem01",
                    "Product2Id": "01tWs000003HighCapBattery",
                    "Product2": {"Name": "Battery, High Capacity", "ProductCode": "B-1000"},
                    "Quantity": 20,
                    "UnitPrice": 9350.0,
                    "TotalPrice": 187000.0,
                    "sap_material_id": "TG10"
                }
            ]
        },
        "sap_business_partner_id": "1000330"
    },
    {
        "Id": "006Ws000003hK02IAE",
        "Name": "Advanced Communications - New Business",
        "Amount": 130000.0,
        "StageName": "Negotiation",
        "CloseDate": "2026-03-21",
        "AccountId": "001Ws000053hK4mIAE",
        "AccountNumber": "A37942334",
        "Account": {"Name": "Advanced Communications", "AccountNumber": "A37942334"},
        "OwnerAlias": "sancha",
        "Products__c": "Large Turbine, Starter Kit",
        "OpportunityLineItems": {
            "totalSize": 2,
            "records": [
                {
                    "Id": "00kWs000001LineItem02",
                    "Product2Id": "01tWs000001LargeTurbine",
                    "Product2": {"Name": "Large Turbine", "ProductCode": "A-1000"},
                    "Quantity": 1,
                    "UnitPrice": 100000.0,
                    "TotalPrice": 100000.0,
                    "sap_material_id": "TG12"
                },
                {
                    "Id": "00kWs000001LineItem03",
                    "Product2Id": "01tWs000002StarterKit",
                    "Product2": {"Name": "Starter Kit", "ProductCode": "A-5000"},
                    "Quantity": 3,
                    "UnitPrice": 10000.0,
                    "TotalPrice": 30000.0,
                    "sap_material_id": "TG14"
                }
            ]
        },
        "sap_business_partner_id": "1000338"
    },
    {
        "Id": "006Ws000003hK03IAE",
        "Name": "Towson Inc. - Services",
        "Amount": 110000.0,
        "StageName": "Proposal/Quote",
        "CloseDate": "2026-03-17",
        "AccountId": "001Ws000053hK4VIAU",
        "AccountNumber": "A35771791",
        "Account": {"Name": "Towson Inc.", "AccountNumber": "A35771791"},
        "OwnerAlias": "sancha",
        "Products__c": "Installation Services",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem04",
                    "Product2Id": "01tWs000004Installation",
                    "Product2": {"Name": "Installation Services", "ProductCode": "INST-100"},
                    "Quantity": 10,
                    "UnitPrice": 11000.0,
                    "TotalPrice": 110000.0,
                    "sap_material_id": "TG21"
                }
            ]
        },
        "sap_business_partner_id": "1000333"
    },
    {
        "Id": "006Ws000003hK04IAE",
        "Name": "Southern Solutions - New Business",
        "Amount": 100000.0,
        "StageName": "Qualification",
        "CloseDate": "2026-05-21",
        "AccountId": "001Ws000053hK4HIAU",
        "AccountNumber": "A32381498",
        "Account": {"Name": "Southern Solutions", "AccountNumber": "A32381498"},
        "OwnerAlias": "sancha",
        "Products__c": "Wind Generator",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem05",
                    "Product2Id": "01tWs000005WindGen",
                    "Product2": {"Name": "Wind Generator", "ProductCode": "WT-GEN"},
                    "Quantity": 5,
                    "UnitPrice": 20000.0,
                    "TotalPrice": 100000.0,
                    "sap_material_id": "TG0012"
                }
            ]
        },
        "sap_business_partner_id": "1000331"
    },
    {
        "Id": "006Ws000003hK05IAE",
        "Name": "Advanced Communications - Add-On",
        "Amount": 97000.0,
        "StageName": "Negotiation",
        "CloseDate": "2026-03-21",
        "AccountId": "001Ws000053hK4mIAE",
        "AccountNumber": "A37942334",
        "Account": {"Name": "Advanced Communications", "AccountNumber": "A37942334"},
        "OwnerAlias": "sancha",
        "Products__c": "Battery, High Capacity",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem06",
                    "Product2Id": "01tWs000003HighCapBattery",
                    "Product2": {"Name": "Battery, High Capacity", "ProductCode": "B-1000"},
                    "Quantity": 10,
                    "UnitPrice": 9700.0,
                    "TotalPrice": 97000.0,
                    "sap_material_id": "TG10"
                }
            ]
        },
        "sap_business_partner_id": "1000338"
    },
    {
        "Id": "006Ws000003hK06IAE",
        "Name": "Universal Containers - Add-On",
        "Amount": 75000.0,
        "StageName": "Negotiation",
        "CloseDate": "2026-03-21",
        "AccountId": "001Ws000053hK4jIAE",
        "AccountNumber": "A87586863",
        "Account": {"Name": "Universal Containers", "AccountNumber": "A87586863"},
        "OwnerAlias": "sancha",
        "Products__c": "Solar EV Charging Station",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem07",
                    "Product2Id": "01tWs000006SolarEV",
                    "Product2": {"Name": "Solar EV Charging Station", "ProductCode": "V-1000"},
                    "Quantity": 5,
                    "UnitPrice": 15000.0,
                    "TotalPrice": 75000.0,
                    "sap_material_id": "TG0013"
                }
            ]
        },
        "sap_business_partner_id": "1000329"
    },
    {
        "Id": "006Ws000003hK07IAE",
        "Name": "Opportunity Resources Inc - New Business",
        "Amount": 60000.0,
        "StageName": "Discovery",
        "CloseDate": "2026-04-13",
        "AccountId": "001Ws000053hK4OIAU",
        "AccountNumber": "A32501049",
        "Account": {"Name": "Opportunity Resources Inc", "AccountNumber": "A32501049"},
        "OwnerAlias": "sancha",
        "Products__c": "Solar Panel",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem08",
                    "Product2Id": "01tWs000007SolarPanel",
                    "Product2": {"Name": "Solar Panel", "ProductCode": "S-100"},
                    "Quantity": 20,
                    "UnitPrice": 3000.0,
                    "TotalPrice": 60000.0,
                    "sap_material_id": "TG0011"
                }
            ]
        },
        "sap_business_partner_id": "1000332"
    },
    {
        "Id": "006Ws000003hK08IAE",
        "Name": "Employnet - New Business",
        "Amount": 55500.0,
        "StageName": "Qualification",
        "CloseDate": "2026-07-02",
        "AccountId": "001Ws000053hK4QIAU",
        "AccountNumber": "A89739749",
        "Account": {"Name": "Employnet", "AccountNumber": "A89739749"},
        "OwnerAlias": "sancha",
        "Products__c": "Starter Kit",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem09",
                    "Product2Id": "01tWs000002StarterKit",
                    "Product2": {"Name": "Starter Kit", "ProductCode": "A-5000"},
                    "Quantity": 5,
                    "UnitPrice": 11100.0,
                    "TotalPrice": 55500.0,
                    "sap_material_id": "TG14"
                }
            ]
        },
        "sap_business_partner_id": "1000334"
    },
    {
        "Id": "006Ws000003hK09IAE",
        "Name": "Vand Enterprises, Inc. - Add-On",
        "Amount": 35000.0,
        "StageName": "Negotiation",
        "CloseDate": "2026-06-27",
        "AccountId": "001Ws000053hK4LIAU",
        "AccountNumber": "A86372801",
        "Account": {"Name": "Vand Enterprises, Inc.", "AccountNumber": "A86372801"},
        "OwnerAlias": "sancha",
        "Products__c": "Starter Kit",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem10",
                    "Product2Id": "01tWs000002StarterKit",
                    "Product2": {"Name": "Starter Kit", "ProductCode": "A-5000"},
                    "Quantity": 3,
                    "UnitPrice": 11666.67,
                    "TotalPrice": 35000.0,
                    "sap_material_id": "TG14"
                }
            ]
        },
        "sap_business_partner_id": "1000336"
    },
    {
        "Id": "006Ws000003hK10IAE",
        "Name": "Green Fields Media - New Business",
        "Amount": 7000.0,
        "StageName": "Proposal/Quote",
        "CloseDate": "2026-11-10",
        "AccountId": "001Ws000053hK4dIAE",
        "AccountNumber": "A73896892",
        "Account": {"Name": "Green Fields Media", "AccountNumber": "A73896892"},
        "OwnerAlias": "sancha",
        "Products__c": "Starter Kit",
        "OpportunityLineItems": {
            "totalSize": 1,
            "records": [
                {
                    "Id": "00kWs000001LineItem11",
                    "Product2Id": "01tWs000002StarterKit",
                    "Product2": {"Name": "Starter Kit", "ProductCode": "A-5000"},
                    "Quantity": 1,
                    "UnitPrice": 7000.0,
                    "TotalPrice": 7000.0,
                    "sap_material_id": "TG14"
                }
            ]
        },
        "sap_business_partner_id": "1000335"
    }
]

# Multi-Session In-Memory Store
sessions: Dict[str, Dict[str, Any]] = {}

def get_session_id(request: Request) -> str:
    user_hdr = request.headers.get("x-user-id") or request.headers.get("x-session-id")
    if user_hdr:
        return user_hdr.strip()
    user_param = request.query_params.get("user") or request.query_params.get("session")
    if user_param:
        return user_param.strip()
    user_cookie = request.cookies.get("sfdc_session")
    if user_cookie:
        return user_cookie.strip()
    return "default"

def get_session_state(session_id: str) -> Dict[str, Any]:
    if session_id not in sessions:
        sessions[session_id] = {
            "opportunities": copy.deepcopy(INITIAL_OPPORTUNITIES),
            "quotes": [],
            "quote_line_items": []
        }
    return sessions[session_id]

# Schemas
class QuotePayload(BaseModel):
    OpportunityId: str
    Name: str
    Pricebook2Id: Optional[str] = None

class QuoteLineItemPayload(BaseModel):
    QuoteId: str
    PricebookEntryId: str
    Quantity: int
    UnitPrice: float

# UI Endpoint
@app.get("/", response_class=HTMLResponse)
@app.get("/lightning", response_class=HTMLResponse)
def get_lightning_ui():
    return HTML_CONTENT

# Salesforce SOQL API
@app.get("/services/data/v60.0/query/")
def query_salesforce(q: str, request: Request):
    q_upper = q.upper()
    state = get_session_state(get_session_id(request))
    
    if "FROM OPPORTUNITY" in q_upper:
        records = copy.deepcopy(state["opportunities"])
        stage_match = re.search(r"STAGENAME\s*=\s*'([^']+)'", q, re.IGNORECASE)
        if stage_match:
            target_stage = stage_match.group(1)
            records = [r for r in records if r.get("StageName", "").lower() == target_stage.lower()]
        
        limit_match = re.search(r"LIMIT\s+(\d+)", q, re.IGNORECASE)
        if limit_match:
            lim = int(limit_match.group(1))
            records = records[:lim]

        return {
            "totalSize": len(records),
            "done": True,
            "records": records
        }

    if "FROM QUOTE" in q_upper:
        records = copy.deepcopy(state["quotes"])
        opp_match = re.search(r"OPPORTUNITYID\s*=\s*'([^']+)'", q, re.IGNORECASE)
        if opp_match:
            target_opp = opp_match.group(1)
            records = [r for r in records if r.get("OpportunityId") == target_opp]
        return {
            "totalSize": len(records),
            "done": True,
            "records": records
        }

    return {
        "totalSize": len(state["opportunities"]),
        "done": True,
        "records": state["opportunities"]
    }

# Create Quote SObject
@app.post("/services/data/v60.0/sobjects/Quote", status_code=status.HTTP_201_CREATED)
def create_quote(payload: QuotePayload, request: Request):
    state = get_session_state(get_session_id(request))
    new_id = f"0Q0Ws{len(state['quotes'])+1:010d}"
    quote_record = {
        "Id": new_id,
        "Name": payload.Name,
        "OpportunityId": payload.OpportunityId,
        "Pricebook2Id": payload.Pricebook2Id or "01s000000000000AAA",
        "Status": "Draft",
        "TotalPrice": 0.0,
        "LineItems": []
    }
    
    opp = next((o for o in state["opportunities"] if o["Id"] == payload.OpportunityId), None)
    if opp:
        quote_record["TotalPrice"] = opp.get("Amount", 0.0)

    state["quotes"].append(quote_record)
    return {"id": new_id, "success": True, "errors": []}

# Create Quote Line Item
@app.post("/services/data/v60.0/sobjects/QuoteLineItem", status_code=status.HTTP_201_CREATED)
def create_quote_line_item(payload: QuoteLineItemPayload, request: Request):
    state = get_session_state(get_session_id(request))
    new_id = f"0QLWs{len(state['quote_line_items'])+1:010d}"
    line_item = {
        "Id": new_id,
        "QuoteId": payload.QuoteId,
        "PricebookEntryId": payload.PricebookEntryId,
        "Quantity": payload.Quantity,
        "UnitPrice": payload.UnitPrice,
        "TotalPrice": payload.Quantity * payload.UnitPrice
    }
    state["quote_line_items"].append(line_item)
    
    quote = next((q for q in state["quotes"] if q["Id"] == payload.QuoteId), None)
    if quote:
        quote["LineItems"].append(line_item)
        quote["TotalPrice"] = sum(i["TotalPrice"] for i in quote["LineItems"])

    return {"id": new_id, "success": True, "errors": []}

# Update Opportunity Stage
@app.patch("/services/data/v60.0/sobjects/Opportunity/{opportunity_id}")
async def update_opportunity(opportunity_id: str, request: Request):
    state = get_session_state(get_session_id(request))
    body = await request.json()
    opp = next((o for o in state["opportunities"] if o["Id"] == opportunity_id), None)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    if "StageName" in body:
        opp["StageName"] = body["StageName"]
    for k, v in body.items():
        opp[k] = v
        
    return {"id": opportunity_id, "success": True, "errors": []}

# Frontend API helpers
@app.get("/api/opportunities")
def get_opportunities(request: Request):
    state = get_session_state(get_session_id(request))
    return state["opportunities"]

@app.get("/api/quotes")
def get_quotes(request: Request):
    state = get_session_state(get_session_id(request))
    return state["quotes"]

@app.post("/api/reset")
def reset_data(request: Request):
    sid = get_session_id(request)
    sessions[sid] = {
        "opportunities": copy.deepcopy(INITIAL_OPPORTUNITIES),
        "quotes": [],
        "quote_line_items": []
    }
    return {"message": f"Data reset for session '{sid}' to default 10 opportunities"}


HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>All Opportunities | Salesforce</title>
  <link rel="icon" type="image/png" href="https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: #f3f3f3;
      color: #181818;
      height: 100vh;
      display: flex;
      overflow: hidden;
    }

    /* LEFT VERTICAL DOCK */
    .sfdc-left-dock {
      width: 68px;
      background-color: #0b1a30;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 10px 0;
      flex-shrink: 0;
      user-select: none;
      z-index: 10;
    }
    .sfdc-dock-logo {
      width: 42px;
      height: 42px;
      background: #0176D3;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 16px;
      cursor: pointer;
    }
    .sfdc-dock-logo svg {
      width: 26px;
      height: 26px;
      fill: white;
    }
    .sfdc-dock-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 58px;
      height: 52px;
      margin-bottom: 6px;
      border-radius: 6px;
      cursor: pointer;
      color: #93a1b5;
      font-size: 0.65rem;
      font-weight: 500;
      text-align: center;
      transition: all 0.15s ease;
    }
    .sfdc-dock-item:hover {
      background-color: rgba(255,255,255,0.1);
      color: white;
    }
    .sfdc-dock-item.active {
      background-color: #0176D3;
      color: white;
    }
    .sfdc-dock-icon {
      font-size: 1.15rem;
      margin-bottom: 3px;
    }

    /* RIGHT CONTAINER */
    .sfdc-main-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      background-color: #ffffff;
    }

    /* TOP NAVBAR */
    .sfdc-top-bar {
      height: 50px;
      background: #ffffff;
      border-bottom: 1px solid #d8dde6;
      display: flex;
      align-items: center;
      padding: 0 16px;
      gap: 14px;
      flex-shrink: 0;
    }
    .sfdc-brand-cloud {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
    }
    .sfdc-brand-cloud svg {
      width: 32px;
      height: 22px;
      fill: #0176D3;
    }
    .sfdc-app-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #181818;
      display: flex;
      align-items: center;
      gap: 4px;
    }

    /* HORIZONTAL TABS */
    .sfdc-tabs-bar {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-left: 8px;
    }
    .sfdc-nav-tab {
      font-size: 0.82rem;
      font-weight: 500;
      color: #444;
      padding: 14px 10px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 4px;
      border-bottom: 3px solid transparent;
      white-space: nowrap;
    }
    .sfdc-nav-tab:hover {
      color: #0176D3;
    }
    .sfdc-nav-tab.active {
      color: #0176D3;
      font-weight: 700;
      border-bottom: 3px solid #0176D3;
    }

    /* SEARCH BAR */
    .sfdc-center-search {
      flex: 1;
      max-width: 440px;
      margin: 0 auto;
      position: relative;
    }
    .sfdc-search-pill {
      width: 100%;
      height: 32px;
      border-radius: 16px;
      border: 1px solid #c9c7c5;
      background-color: #f3f3f3;
      padding: 0 14px 0 34px;
      font-size: 0.8rem;
      outline: none;
      transition: all 0.2s;
    }
    .sfdc-search-pill:focus {
      background-color: #ffffff;
      border-color: #0176D3;
      box-shadow: 0 0 0 1px #0176D3;
    }
    .sfdc-search-lens {
      position: absolute;
      left: 12px;
      top: 8px;
      font-size: 0.85rem;
      color: #706e6b;
    }

    /* UTILITY ICONS */
    .sfdc-utility-bar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-left: auto;
    }
    .sfdc-util-btn {
      width: 28px;
      height: 28px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: #706e6b;
      font-size: 0.95rem;
    }
    .sfdc-util-btn:hover {
      background: #f4f6f9;
      color: #0176D3;
    }
    .sfdc-avatar {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      background: #0176D3;
      color: white;
      font-size: 0.75rem;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    /* OPPORTUNITIES PAGE WORKSPACE */
    .sfdc-workspace {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      background: #f3f3f3;
      padding: 12px 16px 24px 16px;
    }

    /* HEADER CARD */
    .sfdc-header-card {
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-radius: 4px 4px 0 0;
      padding: 12px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .sfdc-title-area {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .sfdc-opp-icon {
      width: 36px;
      height: 36px;
      background: #fc8f32;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: white;
      box-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }
    .sfdc-title-text {
      display: flex;
      flex-direction: column;
    }
    .sfdc-sub-title {
      font-size: 0.72rem;
      color: #555;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.5px;
    }
    .sfdc-main-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: #181818;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
    }
    .sfdc-pin {
      font-size: 0.85rem;
      color: #706e6b;
    }

    /* HEADER ACTIONS */
    .sfdc-btn-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .sfdc-btn {
      padding: 6px 14px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid #c9c7c5;
      background: #ffffff;
      color: #0176D3;
      transition: all 0.1s;
    }
    .sfdc-btn:hover {
      background: #f4f6f9;
    }
    .sfdc-btn-brand {
      background: #0176D3;
      color: white;
      border-color: #0176D3;
    }
    .sfdc-btn-brand:hover {
      background: #014486;
      border-color: #014486;
    }

    /* LIST CONTROLS TOOLBAR */
    .sfdc-list-toolbar {
      background: #ffffff;
      border-left: 1px solid #d8dde6;
      border-right: 1px solid #d8dde6;
      padding: 8px 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.78rem;
      color: #555;
    }
    .sfdc-search-list-box {
      position: relative;
      width: 220px;
    }
    .sfdc-search-list-input {
      width: 100%;
      height: 28px;
      border: 1px solid #c9c7c5;
      border-radius: 4px;
      padding: 0 10px 0 28px;
      font-size: 0.78rem;
      outline: none;
    }
    .sfdc-search-list-input:focus {
      border-color: #0176D3;
    }
    .sfdc-list-tools {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .sfdc-tool-icon {
      width: 28px;
      height: 28px;
      border: 1px solid #d8dde6;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      background: #ffffff;
      font-size: 0.85rem;
      color: #706e6b;
    }
    .sfdc-tool-icon:hover {
      background: #f4f6f9;
      color: #0176D3;
    }

    /* DATA TABLE */
    .sfdc-table-wrapper {
      background: #ffffff;
      border: 1px solid #d8dde6;
      border-top: none;
      border-radius: 0 0 4px 4px;
      overflow-x: auto;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    table.sfdc-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
    }
    table.sfdc-table thead tr {
      background-color: #fafaf9;
      border-bottom: 1px solid #d8dde6;
    }
    table.sfdc-table th {
      padding: 8px 12px;
      font-weight: 600;
      color: #514f4d;
      text-align: left;
      border-right: 1px solid #f3f3f3;
      white-space: nowrap;
      user-select: none;
    }
    table.sfdc-table th.num-col { width: 36px; text-align: center; }
    table.sfdc-table th.check-col { width: 36px; text-align: center; }
    table.sfdc-table th.right-col { text-align: right; }
    table.sfdc-table tbody tr {
      border-bottom: 1px solid #eef1f6;
      transition: background 0.1s;
    }
    table.sfdc-table tbody tr:hover {
      background-color: #f4f6f9;
    }
    table.sfdc-table td {
      padding: 9px 12px;
      color: #181818;
      vertical-align: middle;
      white-space: nowrap;
    }
    table.sfdc-table td.num-col {
      color: #706e6b;
      text-align: center;
      font-size: 0.75rem;
    }
    table.sfdc-table td.check-col {
      text-align: center;
    }
    table.sfdc-table td.right-col {
      text-align: right;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
      font-weight: 500;
    }
    .opp-link {
      color: #0176D3;
      text-decoration: none;
      font-weight: 600;
      cursor: pointer;
    }
    .opp-link:hover {
      text-decoration: underline;
    }
    .acct-link {
      color: #0176D3;
      text-decoration: none;
      cursor: pointer;
    }
    .acct-link:hover {
      text-decoration: underline;
    }

    /* CHEVRON STAGE PROGRESSION BAR */
    .chevron-bar {
      display: flex;
      margin: 18px 0;
      background: #eef4f9;
      border-radius: 4px;
      overflow: hidden;
    }
    .chevron-step {
      flex: 1;
      padding: 10px 14px;
      font-size: 0.78rem;
      text-align: center;
      font-weight: 600;
      background: #e5eef7;
      color: #555;
      position: relative;
      clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%, 12px 50%);
      margin-right: -4px;
      cursor: default;
    }
    .chevron-step:first-child {
      clip-path: polygon(0 0, calc(100% - 12px) 0, 100% 50%, calc(100% - 12px) 100%, 0 100%);
    }
    .chevron-step.current {
      background: #0176D3;
      color: #ffffff;
    }
    .chevron-step.complete {
      background: #2e844a;
      color: #ffffff;
    }

    /* DETAIL MODAL */
    .sfdc-modal-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.5);
      z-index: 9999;
      justify-content: center;
      align-items: center;
    }
    .sfdc-modal-dialog {
      background: #ffffff;
      border-radius: 8px;
      width: 92%;
      max-width: 960px;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 12px 40px rgba(0,0,0,0.25);
      display: flex;
      flex-direction: column;
    }
    .sfdc-modal-header {
      background: #f8f9fa;
      border-bottom: 1px solid #d8dde6;
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .sfdc-modal-body {
      padding: 20px;
      overflow-y: auto;
    }
    .sfdc-highlights-panel {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      background: #fafaf9;
      border: 1px solid #e5e5e5;
      border-radius: 4px;
      padding: 14px 18px;
      gap: 16px;
      margin-bottom: 16px;
    }
    .sfdc-highlight-item {
      display: flex;
      flex-direction: column;
    }
    .sfdc-highlight-label {
      font-size: 0.72rem;
      color: #706e6b;
      text-transform: uppercase;
      font-weight: 600;
      margin-bottom: 4px;
    }
    .sfdc-highlight-val {
      font-size: 1.05rem;
      font-weight: 700;
      color: #181818;
    }
  </style>
</head>
<body>

  <!-- LEFT VERTICAL APP NAVIGATION DOCK -->
  <div class="sfdc-left-dock">
    <div class="sfdc-dock-logo" title="Salesforce">
      <svg viewBox="0 0 40 28">
        <path d="M16.5 4C18.2 1.6 21 0 24.2 0C29.6 0 34 4.4 34 9.8C34 10.3 33.9 10.9 33.8 11.4C37.3 12.4 40 15.6 40 19.5C40 24.2 36.2 28 31.5 28C30.9 28 30.2 27.9 29.6 27.8C28.2 29.2 26.2 30 24 30C20.7 30 18 28.2 16.5 25.5C15 27 12.8 28 10.5 28C5.8 28 2 24.2 2 19.5C2 17.5 2.7 15.7 3.8 14.2C1.5 12.8 0 10.3 0 7.5C0 3.4 3.4 0 7.5 0C11.3 0 14.5 2.8 15.1 6.5C15.5 5.6 16 4.7 16.5 4Z"/>
      </svg>
    </div>
    <div class="sfdc-dock-item"><div class="sfdc-dock-icon">👥</div>Contacts</div>
    <div class="sfdc-dock-item"><div class="sfdc-dock-icon">🏢</div>Accounts</div>
    <div class="sfdc-dock-item active"><div class="sfdc-dock-icon">💼</div>Deals</div>
    <div class="sfdc-dock-item"><div class="sfdc-dock-icon">🎧</div>Service</div>
    <div class="sfdc-dock-item"><div class="sfdc-dock-icon">📢</div>Outreach</div>
    <div class="sfdc-dock-item"><div class="sfdc-dock-icon">🎯</div>Marketing</div>
    <div class="sfdc-dock-item"><div class="sfdc-dock-icon">🛒</div>Commerce</div>
    <div class="sfdc-dock-item" style="margin-top: auto;"><div class="sfdc-dock-icon">⚙️</div>More</div>
  </div>

  <!-- MAIN CONTENT CONTAINER -->
  <div class="sfdc-main-container">
    
    <!-- TOP NAVBAR -->
    <div class="sfdc-top-bar">
      <div class="sfdc-brand-cloud">
        <svg viewBox="0 0 40 28">
          <path d="M16.5 4C18.2 1.6 21 0 24.2 0C29.6 0 34 4.4 34 9.8C34 10.3 33.9 10.9 33.8 11.4C37.3 12.4 40 15.6 40 19.5C40 24.2 36.2 28 31.5 28C30.9 28 30.2 27.9 29.6 27.8C28.2 29.2 26.2 30 24 30C20.7 30 18 28.2 16.5 25.5C15 27 12.8 28 10.5 28C5.8 28 2 24.2 2 19.5C2 17.5 2.7 15.7 3.8 14.2C1.5 12.8 0 10.3 0 7.5C0 3.4 3.4 0 7.5 0C11.3 0 14.5 2.8 15.1 6.5C15.5 5.6 16 4.7 16.5 4Z"/>
        </svg>
        <div class="sfdc-app-title">Sales <span style="font-size: 0.75rem; color: #706e6b;">▾</span></div>
      </div>

      <div class="sfdc-tabs-bar">
        <div class="sfdc-nav-tab">Leads ▾</div>
        <div class="sfdc-nav-tab">Contacts ▾</div>
        <div class="sfdc-nav-tab">Accounts ▾</div>
        <div class="sfdc-nav-tab active">Opportunities ▾</div>
        <div class="sfdc-nav-tab">Forecasts</div>
        <div class="sfdc-nav-tab">Quotes ▾</div>
        <div class="sfdc-nav-tab">Products ▾</div>
        <div class="sfdc-nav-tab">Price Books ▾</div>
        <div class="sfdc-nav-tab">Calendar ▾</div>
        <div class="sfdc-nav-tab">Analytics</div>
      </div>

      <div class="sfdc-center-search">
        <span class="sfdc-search-lens">🔍</span>
        <input type="text" class="sfdc-search-pill" id="globalSearch" placeholder="Search..." onkeyup="filterOpportunities()">
      </div>

      <div class="sfdc-utility-bar">
        <div class="sfdc-util-btn" title="Quick Create">➕</div>
        <div class="sfdc-util-btn" title="Help">❔</div>
        <div class="sfdc-util-btn" title="Setup">⚙️</div>
        <div class="sfdc-util-btn" title="Notifications">🔔</div>
        <div class="sfdc-avatar" title="Sanchita Mohta">SM</div>
      </div>
    </div>

    <!-- WORKSPACE AREA -->
    <div class="sfdc-workspace">
      
      <!-- PAGE HEADER CARD -->
      <div class="sfdc-header-card">
        <div class="sfdc-title-area">
          <div class="sfdc-opp-icon">🏆</div>
          <div class="sfdc-title-text">
            <span class="sfdc-sub-title">Opportunities</span>
            <div class="sfdc-main-title">
              All Opportunities <span style="font-size: 0.85rem; color: #706e6b;">▾</span>
              <span class="sfdc-pin" title="Pinned List">📌</span>
            </div>
          </div>
        </div>

        <div class="sfdc-btn-group">
          <button class="sfdc-btn" onclick="loadOpportunities()">🔄 Refresh</button>
          <button class="sfdc-btn sfdc-btn-brand">New</button>
          <button class="sfdc-btn">Assign Label</button>
        </div>
      </div>

      <!-- LIST CONTROLS TOOLBAR -->
      <div class="sfdc-list-toolbar">
        <div>
          <span id="oppItemCount">10</span> items • Sorted by Amount • Filtered by All opportunities • <span style="color: #2e844a; font-weight: 600;">Live Sync Connected</span>
        </div>

        <div class="sfdc-list-tools">
          <div class="sfdc-search-list-box">
            <span style="position: absolute; left: 8px; top: 6px; font-size: 0.75rem; color: #706e6b;">🔍</span>
            <input type="text" class="sfdc-search-list-input" id="listSearch" placeholder="Search this list..." onkeyup="filterOpportunities()">
          </div>
          <div class="sfdc-tool-icon" title="Display as Table">▦</div>
          <div class="sfdc-tool-icon" title="Display as Kanban">🗂</div>
          <div class="sfdc-tool-icon" title="Refresh List" onclick="loadOpportunities()">🔄</div>
          <div class="sfdc-tool-icon" title="Inline Edit">✏️</div>
          <div class="sfdc-tool-icon" title="Show Charts">📊</div>
          <div class="sfdc-tool-icon" title="Filter List">🔽</div>
        </div>
      </div>

      <!-- DATA TABLE WRAPPER -->
      <div class="sfdc-table-wrapper">
        <table class="sfdc-table">
          <thead>
            <tr>
              <th class="num-col">#</th>
              <th class="check-col"><input type="checkbox"></th>
              <th>Opportunity Name ↑</th>
              <th>Account Name</th>
              <th>Account Number</th>
              <th class="right-col">Amount</th>
              <th>Close Date</th>
              <th>Stage</th>
              <th>Owner</th>
              <th>SAP BP</th>
              <th style="width: 32px;"></th>
            </tr>
          </thead>
          <tbody id="oppTableBody">
            <!-- Dynamically populated -->
          </tbody>
        </table>
      </div>

    </div>
  </div>

  <!-- OPPORTUNITY RECORD DETAIL MODAL -->
  <div class="sfdc-modal-overlay" id="detailModal">
    <div class="sfdc-modal-dialog">
      <div class="sfdc-modal-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <div class="sfdc-opp-icon" style="width: 30px; height: 30px; font-size: 16px;">🏆</div>
          <div>
            <div style="font-size: 0.7rem; color: #706e6b; text-transform: uppercase;">Opportunity</div>
            <h2 id="modalOppTitle" style="font-size: 1.15rem; font-weight: 700; margin: 0;"></h2>
          </div>
        </div>
        <button onclick="closeModal()" style="border: none; background: none; font-size: 22px; cursor: pointer; color: #706e6b;">&times;</button>
      </div>

      <div class="sfdc-modal-body">
        
        <!-- Highlights Panel -->
        <div class="sfdc-highlights-panel">
          <div class="sfdc-highlight-item">
            <span class="sfdc-highlight-label">Amount</span>
            <span class="sfdc-highlight-val" id="modalAmount" style="color: #0176D3;"></span>
          </div>
          <div class="sfdc-highlight-item">
            <span class="sfdc-highlight-label">Stage</span>
            <span class="sfdc-highlight-val" id="modalStage"></span>
          </div>
          <div class="sfdc-highlight-item">
            <span class="sfdc-highlight-label">Close Date</span>
            <span class="sfdc-highlight-val" id="modalCloseDate"></span>
          </div>
          <div class="sfdc-highlight-item">
            <span class="sfdc-highlight-label">Account</span>
            <span class="sfdc-highlight-val" id="modalAccount"></span>
          </div>
        </div>

        <!-- Chevron Progression Bar -->
        <div style="font-size: 0.75rem; font-weight: 700; color: #514f4d; text-transform: uppercase; margin-bottom: 4px;">Stage Progression Path</div>
        <div class="chevron-bar">
          <div class="chevron-step" id="step-Discovery">Discovery</div>
          <div class="chevron-step" id="step-Qualification">Qualification</div>
          <div class="chevron-step" id="step-Proposal/Quote">Proposal/Quote</div>
          <div class="chevron-step" id="step-Negotiation">Negotiation</div>
          <div class="chevron-step" id="step-Closed Won">Closed Won</div>
        </div>

        <!-- Line Items Table -->
        <div style="margin-top: 24px;">
          <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 10px;">Products (Opportunity Line Items)</h3>
          <table class="sfdc-table" style="border: 1px solid #d8dde6; border-radius: 4px;">
            <thead>
              <tr style="background: #fafaf9;">
                <th>Product Name</th>
                <th>Product Code</th>
                <th>SAP Material ID</th>
                <th>Quantity</th>
                <th class="right-col">Total Price</th>
              </tr>
            </thead>
            <tbody id="modalLineItems"></tbody>
          </table>
        </div>

        <!-- Related Quotes List -->
        <div style="margin-top: 24px;">
          <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 10px;">Quotes (Quote-to-Cash)</h3>
          <div id="modalQuotes"></div>
        </div>

      </div>

      <div style="background: #f8f9fa; border-top: 1px solid #d8dde6; padding: 12px 20px; text-align: right;">
        <button class="sfdc-btn" onclick="closeModal()">Close</button>
      </div>
    </div>
  </div>

  <script>
    let opportunities = [];
    let quotes = [];
    let selectedOpp = null;

    // Session Isolation
    const urlParams = new URLSearchParams(window.location.search);
    let sessionId = urlParams.get('user') || urlParams.get('session') || sessionStorage.getItem('sfdc_session_id');
    if (!sessionId) {
      sessionId = 'user_' + Math.random().toString(36).substring(2, 9);
      sessionStorage.setItem('sfdc_session_id', sessionId);
    }
    document.cookie = "sfdc_session=" + encodeURIComponent(sessionId) + "; path=/; max-age=86400";

    async function loadOpportunities() {
      try {
        const queryParam = '?session=' + encodeURIComponent(sessionId);
        const [oppRes, quoteRes] = await Promise.all([
          fetch('/api/opportunities' + queryParam),
          fetch('/api/quotes' + queryParam)
        ]);
        opportunities = await oppRes.json();
        quotes = await quoteRes.json();
        renderTable();
        if (selectedOpp) {
          const updated = opportunities.find(o => o.Id === selectedOpp.Id);
          if (updated) showDetail(updated.Id);
        }
      } catch (e) {
        console.error("Error loading opportunities:", e);
      }
    }

    function renderTable() {
      const tbody = document.getElementById('oppTableBody');
      const search = (document.getElementById('listSearch').value || document.getElementById('globalSearch').value).toLowerCase();

      const filtered = opportunities.filter(o => 
        o.Name.toLowerCase().includes(search) ||
        o.Account.Name.toLowerCase().includes(search) ||
        o.AccountNumber.toLowerCase().includes(search) ||
        o.StageName.toLowerCase().includes(search)
      );

      document.getElementById('oppItemCount').innerText = filtered.length;

      tbody.innerHTML = filtered.map((opp, idx) => `
        <tr>
          <td class="num-col">${idx + 1}</td>
          <td class="check-col"><input type="checkbox"></td>
          <td>
            <a class="opp-link" href="javascript:void(0)" onclick="showDetail('${opp.Id}')">${opp.Name}</a>
          </td>
          <td>
            <a class="acct-link" href="javascript:void(0)">${opp.Account.Name}</a>
          </td>
          <td><span style="font-family: monospace; background: #f3f3f3; padding: 2px 6px; border-radius: 4px;">${opp.AccountNumber}</span></td>
          <td class="right-col">$${Number(opp.Amount).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
          <td>${opp.CloseDate}</td>
          <td><strong>${opp.StageName}</strong></td>
          <td>${opp.OwnerAlias || 'sancha'}</td>
          <td><span style="font-family: monospace; color: #0176D3; font-weight: bold;">${opp.sap_business_partner_id}</span></td>
          <td style="text-align: center; color: #706e6b; cursor: pointer;">▾</td>
        </tr>
      `).join('');
    }

    function filterOpportunities() {
      renderTable();
    }

    function showDetail(oppId) {
      selectedOpp = opportunities.find(o => o.Id === oppId);
      if (!selectedOpp) return;

      document.getElementById('modalOppTitle').innerText = selectedOpp.Name;
      document.getElementById('modalAmount').innerText = '$' + Number(selectedOpp.Amount).toLocaleString('en-US', {minimumFractionDigits: 2});
      document.getElementById('modalStage').innerText = selectedOpp.StageName;
      document.getElementById('modalCloseDate').innerText = selectedOpp.CloseDate;
      document.getElementById('modalAccount').innerText = `${selectedOpp.Account.Name} (${selectedOpp.AccountNumber})`;

      // Update Chevron
      const stages = ['Discovery', 'Qualification', 'Proposal/Quote', 'Negotiation', 'Closed Won'];
      const currentIndex = stages.indexOf(selectedOpp.StageName);

      stages.forEach((stage, idx) => {
        const el = document.getElementById(`step-${stage}`);
        if (!el) return;
        el.className = 'chevron-step';
        if (selectedOpp.StageName === 'Closed Won') {
          el.classList.add('complete');
        } else if (idx < currentIndex) {
          el.classList.add('complete');
        } else if (idx === currentIndex) {
          el.classList.add('current');
        }
      });

      // Products
      const lineItemsTbody = document.getElementById('modalLineItems');
      const items = selectedOpp.OpportunityLineItems?.records || [];
      if (items.length === 0) {
        lineItemsTbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #888;">No product line items.</td></tr>';
      } else {
        lineItemsTbody.innerHTML = items.map(item => `
          <tr>
            <td style="font-weight: 500;">${item.Product2?.Name || selectedOpp.Products__c}</td>
            <td style="font-family: monospace;">${item.Product2?.ProductCode || 'GEN-01'}</td>
            <td><span style="font-weight: bold; color: #0176D3;">${item.sap_material_id || 'TG12'}</span></td>
            <td>${item.Quantity}</td>
            <td class="right-col">$${Number(item.TotalPrice).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
          </tr>
        `).join('');
      }

      // Quotes
      const oppQuotes = quotes.filter(q => q.OpportunityId === selectedOpp.Id);
      const quotesBox = document.getElementById('modalQuotes');
      if (oppQuotes.length === 0) {
        quotesBox.innerHTML = '<div style="padding: 14px; border: 1px dashed #d8dde6; border-radius: 4px; text-align: center; color: #706e6b; font-size: 0.8rem;">No Quotes created yet for this opportunity. Quotes created by SmartCloser will appear here in real time.</div>';
      } else {
        quotesBox.innerHTML = `
          <table class="sfdc-table" style="border: 1px solid #d8dde6; border-radius: 4px;">
            <thead>
              <tr style="background: #fafaf9;">
                <th>Quote Number</th>
                <th>Quote Name</th>
                <th>Status</th>
                <th class="right-col">Total Price</th>
              </tr>
            </thead>
            <tbody>
              ${oppQuotes.map(q => `
                <tr>
                  <td style="font-family: monospace; font-weight: bold; color: #0176D3;">${q.Id}</td>
                  <td>${q.Name}</td>
                  <td><span style="background: #e0eafd; color: #004487; padding: 2px 8px; border-radius: 10px; font-weight: bold; font-size: 0.72rem;">${q.Status || 'Draft'}</span></td>
                  <td class="right-col">$${Number(q.TotalPrice).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }

      document.getElementById('detailModal').style.display = 'flex';
    }

    function closeModal() {
      document.getElementById('detailModal').style.display = 'none';
      selectedOpp = null;
    }

    async function resetDemoData() {
      if (confirm('Reset all opportunity stages and quotes back to initial state?')) {
        await fetch('/api/reset', { method: 'POST' });
        await loadOpportunities();
      }
    }

    loadOpportunities();
    setInterval(loadOpportunities, 3000);
  </script>
</body>
</html>
"""
