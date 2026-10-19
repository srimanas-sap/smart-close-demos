import os
import json
import urllib.parse
import requests
import google.auth.transport.requests
import google.oauth2.id_token
from typing import Any, Dict, Optional
from google.adk.tools import BaseTool, FunctionTool, ToolContext

TOOLBOX_URL = os.environ.get("TOOLBOX_URL", "https://mcp-toolbox-483251484488.us-central1.run.app").rstrip("/")
SFDC_BASE_URL = os.environ.get("SFDC_BASE_URL", "https://salesforce-mock-483251484488.us-central1.run.app").rstrip("/")
SAP_BTP_TOKEN_URL = os.environ.get("SAP_BTP_TOKEN_URL", "")
SAP_BTP_EXCHANGE_URL = os.environ.get("SAP_BTP_EXCHANGE_URL", "")
SAP_BTP_CLIENT_ID = os.environ.get("SAP_BTP_CLIENT_ID", "")
SAP_BTP_CLIENT_SECRET = os.environ.get("SAP_BTP_CLIENT_SECRET", "")
GEMINI_ENTERPRISE_SAP_AUTH_ID = os.environ.get("GEMINI_ENTERPRISE_SAP_AUTH_ID", "sap_sso")


def _get_cloud_run_id_token(service_url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(service_url)
        audience = f"{parsed.scheme}://{parsed.netloc}"
        req = google.auth.transport.requests.Request()
        return google.oauth2.id_token.fetch_id_token(req, audience)
    except Exception:
        return ""


def _exchange_btp_destination_token(user_xsuaa_token: str) -> str:
    """Exchanges the Gemini Enterprise user XSUAA token for an S/4HANA Destination token."""
    if not (SAP_BTP_TOKEN_URL and SAP_BTP_EXCHANGE_URL and SAP_BTP_CLIENT_ID and SAP_BTP_CLIENT_SECRET):
        return user_xsuaa_token

    # 1. Fetch BTP Destination Service client_credentials token
    resp = requests.post(
        SAP_BTP_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": SAP_BTP_CLIENT_ID,
            "client_secret": SAP_BTP_CLIENT_SECRET,
        },
        timeout=10,
    )
    resp.raise_for_status()
    dest_service_token = resp.json().get("access_token", "")

    # 2. Exchange user token via BTP Destination Service
    headers = {"Authorization": f"Bearer {dest_service_token}"}
    if user_xsuaa_token:
        headers["X-user-token"] = user_xsuaa_token
    ex_resp = requests.get(SAP_BTP_EXCHANGE_URL, headers=headers, timeout=10)
    ex_resp.raise_for_status()
    auth_tokens = ex_resp.json().get("authTokens", [])
    if auth_tokens and auth_tokens[0].get("value"):
        print("ToolboxHttpTool: Destination exchange succeeded!", flush=True)
        return auth_tokens[0]["value"]
    return user_xsuaa_token


class ToolboxHttpTool(BaseTool):
    """Invokes MCP Toolbox v2 HTTP endpoints with SAP BTP Destination token exchange."""

    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        super().__init__(name=name, description=description)
        self._parameters_schema = parameters_schema

    async def run_async(self, *, args: Dict[str, Any], tool_context: ToolContext) -> Any:
        state_dict = tool_context.state.to_dict() if hasattr(tool_context.state, "to_dict") else dict(tool_context.state or {})
        user_token = ""
        for k, v in state_dict.items():
            if GEMINI_ENTERPRISE_SAP_AUTH_ID in k or "sap" in k.lower() or "token" in k.lower():
                if isinstance(v, str) and len(v) > 50:
                    user_token = v
                    print(f"ToolboxHttpTool.run_async: Successfully extracted token from tool_context.state (len={len(user_token)})", flush=True)
                    break

        print("ToolboxHttpTool.run_async: Exchanging user token for backend BTP destination token...", flush=True)
        s4_token = _exchange_btp_destination_token(user_token)

        invoke_url = f"{TOOLBOX_URL}/api/tool/{self.name}/invoke"
        print(f"ToolboxHttpTool.run_async: Invoking '{self.name}' via POST {invoke_url}", flush=True)

        headers = {"Content-Type": "application/json"}
        cr_token = _get_cloud_run_id_token(TOOLBOX_URL)
        if cr_token:
            headers["Authorization"] = f"Bearer {cr_token}"
        if s4_token:
            headers["X-SAP-Auth_token"] = f"Bearer {s4_token}"

        resp = requests.post(invoke_url, headers=headers, json=args or {}, timeout=30)
        return resp.json()


# Salesforce Tools
def get_open_opportunities() -> Dict[str, Any]:
    """Fetches open Salesforce opportunities with pre-mapped SAP Business Partner & Material IDs."""
    resp = requests.get(f"{SFDC_BASE_URL}/opportunities/open", timeout=15)
    return resp.json()

def execute_soql_query(q: str) -> Dict[str, Any]:
    """Execute a SOQL query in Salesforce."""
    resp = requests.get(f"{SFDC_BASE_URL}/services/data/v58.0/query", params={"q": q}, timeout=15)
    return resp.json()

def create_salesforce_quote(Name: str, OpportunityId: str, Pricebook2Id: str = "01s000000000000AAA") -> Dict[str, Any]:
    """Create a quote in Salesforce."""
    resp = requests.post(
        f"{SFDC_BASE_URL}/services/data/v58.0/sobjects/Quote",
        json={"Name": Name, "OpportunityId": OpportunityId, "Pricebook2Id": Pricebook2Id},
        timeout=15,
    )
    return resp.json()

def create_salesforce_quote_line_item(QuoteId: str, Product2Id: str, Quantity: float, UnitPrice: float, PricebookEntryId: str = "01u000000000000AAA") -> Dict[str, Any]:
    """Create a quote line item in Salesforce."""
    resp = requests.post(
        f"{SFDC_BASE_URL}/services/data/v58.0/sobjects/QuoteLineItem",
        json={
            "QuoteId": QuoteId,
            "Product2Id": Product2Id,
            "Quantity": Quantity,
            "UnitPrice": UnitPrice,
            "PricebookEntryId": PricebookEntryId,
        },
        timeout=15,
    )
    return resp.json()

def update_salesforce_opportunity(Id: str, StageName: str) -> Dict[str, Any]:
    """Update an opportunity stage in Salesforce."""
    resp = requests.patch(
        f"{SFDC_BASE_URL}/services/data/v58.0/sobjects/Opportunity",
        json={"Id": Id, "StageName": StageName},
        timeout=15,
    )
    return resp.json()
