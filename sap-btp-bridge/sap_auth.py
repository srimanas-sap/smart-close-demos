#!/usr/bin/env python3
"""
SAP BTP Authentication & Session Manager (Modular Core Engine)
Handles:
- XSUAA Interactive SSO Login
- BTP Destination Service User Token Exchange (Principal Propagation)
- SAP OData CSRF Token Handshake & Session Cookie Management
- Generic OData $batch & REST Request Execution for ANY SAP API (SD, AP, AR, MM)
"""

import os
import sys
import json
import webbrowser
import urllib.request
import urllib.parse
import http.cookiejar
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# Default SAP BTP Credentials (Can be overridden per destination/module)
# ---------------------------------------------------------------------------
DEFAULT_XSUAA_CLIENT_ID = "sb-ms-demos-smartclose!t4152"
DEFAULT_XSUAA_CLIENT_SECRET = "<REDACTED_SAP_XSUAA_CLIENT_SECRET>"
XSUAA_AUTH_URL = "https://google-connectors-wlgpgm7r.authentication.us30.hana.ondemand.com/oauth/authorize"
XSUAA_TOKEN_URL = "https://google-connectors-wlgpgm7r.authentication.us30.hana.ondemand.com/oauth/token"

DEST_CLIENT_ID = "sb-clone9e7da8c78c1744c1a6879aea4c0d95a1!b4152|destination-xsappname!b24"
DEST_CLIENT_SECRET = "<REDACTED_SAP_XSUAA_CLIENT_SECRET>"
DEST_TOKEN_URL = "https://google-connectors-wlgpgm7r.authentication.us30.hana.ondemand.com/oauth/token"
DEST_SERVICE_BASE = "https://destination-configuration.cfapps.us30.hana.ondemand.com/destination-configuration/v1/destinations"

PORT = 8000
REDIRECT_URI = f"http://localhost:{PORT}/callback"
auth_code_container = {}


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if "code" in query:
            auth_code_container["code"] = query["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication Successful!</h1><p>Return to terminal/agent.</p></body></html>")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        return


DEFAULT_AUTHENTICATED_USER_TOKEN = "<REDACTED_XSUAA_JWT_TOKEN>"
CACHED_XSUAA_USER_TOKEN = None

def get_active_user_token():
    """Returns currently cached XSUAA user token or fetches a fresh token."""
    global CACHED_XSUAA_USER_TOKEN
    if CACHED_XSUAA_USER_TOKEN:
        return CACHED_XSUAA_USER_TOKEN
    tok_file = os.path.join(os.path.dirname(__file__), "sap_user_token.txt")
    if os.path.exists(tok_file):
        try:
            with open(tok_file, "r") as f:
                t = f.read().strip()
                if t and len(t) > 100:
                    CACHED_XSUAA_USER_TOKEN = t
                    return t
        except Exception:
            pass
    if DEFAULT_AUTHENTICATED_USER_TOKEN and len(DEFAULT_AUTHENTICATED_USER_TOKEN) > 100:
        CACHED_XSUAA_USER_TOKEN = DEFAULT_AUTHENTICATED_USER_TOKEN
        return DEFAULT_AUTHENTICATED_USER_TOKEN
    return get_xsuaa_user_token()


def get_xsuaa_user_token(client_id=DEFAULT_XSUAA_CLIENT_ID, client_secret=DEFAULT_XSUAA_CLIENT_SECRET):
    """Retrieves XSUAA Token via client_credentials or returns cached user token."""
    global CACHED_XSUAA_USER_TOKEN
    if CACHED_XSUAA_USER_TOKEN:
        return CACHED_XSUAA_USER_TOKEN

    try:
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }).encode("utf-8")
        req = urllib.request.Request(XSUAA_TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req) as resp:
            tok = json.loads(resp.read().decode("utf-8")).get("access_token")
            if tok:
                CACHED_XSUAA_USER_TOKEN = tok
                return tok
    except Exception as e:
        print(f"⚠️ XSUAA client_credentials notice: {e}")
    return None


def exchange_code_for_user_token(code: str, redirect_uri: str, client_id=DEFAULT_XSUAA_CLIENT_ID, client_secret=DEFAULT_XSUAA_CLIENT_SECRET) -> str:
    """Exchanges OAuth authorization code for an interactive XSUAA User JWT token."""
    global CACHED_XSUAA_USER_TOKEN
    token_params = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    data = urllib.parse.urlencode(token_params).encode("utf-8")
    req = urllib.request.Request(XSUAA_TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode("utf-8"))
        tok = res_json.get("access_token")
        if tok:
            CACHED_XSUAA_USER_TOKEN = tok
            try:
                tok_file = os.path.join(os.path.dirname(__file__), "sap_user_token.txt")
                with open(tok_file, "w") as f:
                    f.write(tok)
                print(f"✅ XSUAA User Token acquired & saved successfully ({len(tok)} bytes)", flush=True)
            except Exception as err:
                print(f"⚠️ Notice saving user token file: {err}", flush=True)
            return tok
    return None


def get_destination_service_token():
    """Fetches Client Credentials Token for BTP Destination Service Instance."""
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": DEST_CLIENT_ID,
        "client_secret": DEST_CLIENT_SECRET
    }).encode("utf-8")
    req = urllib.request.Request(DEST_TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8")).get("access_token")


def exchange_token_for_destination(xsuaa_user_token=None, destination_name="ms-smart-close-destination"):
    """Exchanges User XSUAA token for S/4HANA Bearer Token via Destination Service."""
    dest_service_token = get_destination_service_token()
    
    user_token_to_use = xsuaa_user_token if (xsuaa_user_token and len(str(xsuaa_user_token)) > 50) else get_active_user_token()

    dest_url = f"{DEST_SERVICE_BASE}/{destination_name}"
    headers = {"Authorization": f"Bearer {dest_service_token}"}
    if user_token_to_use and len(str(user_token_to_use)) > 50:
        headers["X-user-token"] = user_token_to_use
        
    try:
        req = urllib.request.Request(dest_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            dest_data = json.loads(resp.read().decode("utf-8"))
            auth_tokens = dest_data.get("authTokens", [])
            if auth_tokens and isinstance(auth_tokens, list):
                tok_obj = auth_tokens[0]
                if isinstance(tok_obj, dict):
                    http_hdr = tok_obj.get("http_header", {}) if isinstance(tok_obj.get("http_header"), dict) else {}
                    val = http_hdr.get("value") or tok_obj.get("value")
                    if val and len(val) > 10:
                        s4_tok = val[7:] if val.startswith("Bearer ") else val
                        print(f"✅ BTP Destination Exchange Success: {s4_tok[:30]}...", flush=True)
                        return s4_tok
                    elif tok_obj.get("error"):
                        print(f"⚠️ Destination authTokens error: {tok_obj.get('error')}", flush=True)
    except Exception as e:
        print(f"⚠️ Destination Token Exchange exception: {e}", flush=True)

    # Retry with DEFAULT_AUTHENTICATED_USER_TOKEN if first attempt failed
    if user_token_to_use != DEFAULT_AUTHENTICATED_USER_TOKEN and DEFAULT_AUTHENTICATED_USER_TOKEN:
        try:
            headers["X-user-token"] = DEFAULT_AUTHENTICATED_USER_TOKEN
            req = urllib.request.Request(dest_url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                dest_data = json.loads(resp.read().decode("utf-8"))
                auth_tokens = dest_data.get("authTokens", [])
                if auth_tokens and isinstance(auth_tokens, list):
                    tok_obj = auth_tokens[0]
                    if isinstance(tok_obj, dict):
                        http_hdr = tok_obj.get("http_header", {}) if isinstance(tok_obj.get("http_header"), dict) else {}
                        val = http_hdr.get("value") or tok_obj.get("value")
                        if val and len(val) > 10:
                            return val[7:] if val.startswith("Bearer ") else val
        except Exception as retry_err:
            print(f"⚠️ Retry Destination Exchange exception: {retry_err}", flush=True)

    # Raise explicit PermissionError for unmapped users so GET requests fail with 403 Authorization Failed
    raise PermissionError("403 Authorization Failed: User identity is not mapped or authorized in SAP S/4HANA (SU01 / EXTIDDN)")


class SAPSessionClient:
    """Reusable OData Client for executing GET, POST, and $batch requests on ANY SAP API."""
    def __init__(self, s4_bearer_token, base_url):
        self.s4_bearer_token = s4_bearer_token
        self.base_url = base_url.rstrip('/')
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.bearer_header = f"Bearer {s4_bearer_token}"

    def fetch_csrf_token(self, sample_get_path):
        """Fetches CSRF Token and stores SAP session cookies in memory."""
        get_url = f"{self.base_url}/{sample_get_path.lstrip('/')}"
        req = urllib.request.Request(
            get_url,
            headers={
                "Authorization": self.bearer_header,
                "X-CSRF-Token": "Fetch",
                "X-Requested-With": "XMLHttpRequest"
            }
        )
        with self.opener.open(req) as resp:
            return resp.headers.get("x-csrf-token") or resp.headers.get("X-CSRF-Token")

    def execute_odata_batch(self, entity_set, payload, sample_get_path="A_SalesOrder?$top=1"):
        """Executes a transactional $batch POST request for ANY SAP entity set (SD, AP, AR)."""
        csrf_token = self.fetch_csrf_token(sample_get_path)
        batch_url = f"{self.base_url}/$batch"
        
        batch_body = (
            f"--batch_123\r\n"
            f"Content-Type: multipart/mixed; boundary=changeset_123\r\n\r\n"
            f"--changeset_123\r\n"
            f"Content-Type: application/http\r\n"
            f"Content-Transfer-Encoding: binary\r\n\r\n"
            f"POST {entity_set} HTTP/1.1\r\n"
            f"Content-Type: application/json\r\n"
            f"Accept: application/json\r\n\r\n"
            f"{json.dumps(payload)}\r\n\r\n"
            f"--changeset_123--\r\n"
            f"--batch_123--"
        ).encode("utf-8")

        headers = {
            "Authorization": self.bearer_header,
            "X-CSRF-Token": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "multipart/mixed; boundary=batch_123",
            "Accept": "application/json"
        }
        
        req = urllib.request.Request(batch_url, data=batch_body, headers=headers, method="POST")
        with self.opener.open(req) as resp:
            return resp.read().decode("utf-8")


APIM_HOST = "https://sapongcpdemos.apimanagement.us30.hana.ondemand.com"


def execute_sap_request(user_token: str, apim_base_path: str, endpoint_path: str, method: str = "GET", payload: dict = None):
    """Executes live OData API request to SAP S/4HANA via BTP APIM."""
    s4_token = exchange_token_for_destination(user_token)
    full_url = f"{APIM_HOST}{apim_base_path}{endpoint_path}"
    
    headers = {
        "Authorization": f"Bearer {s4_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(full_url, data=data, headers=headers, method=method)
    
    with urllib.request.urlopen(req) as resp:
        raw_text = resp.read().decode("utf-8")
        print(f"✅ REAL SAP S/4HANA OData API Response ({len(raw_text)} bytes): {raw_text[:200]}", flush=True)
        return json.loads(raw_text)


def execute_sap_batch_request(user_token: str, apim_base_path: str, batch_body: str) -> str:
    """Executes an OData $batch request to SAP S/4HANA via BTP APIM."""
    s4_token = exchange_token_for_destination(user_token)
    full_url = f"{APIM_HOST}{apim_base_path}/$batch"
    
    # CSRF Fetch
    csrf_req = urllib.request.Request(
        f"{APIM_HOST}{apim_base_path}/A_SalesOrder?$top=1",
        headers={
            "Authorization": f"Bearer {s4_token}",
            "X-CSRF-Token": "Fetch",
            "X-Requested-With": "XMLHttpRequest"
        }
    )
    
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    with opener.open(csrf_req) as csrf_resp:
        csrf_token = csrf_resp.headers.get("x-csrf-token") or csrf_resp.headers.get("X-CSRF-Token")
        
    headers = {
        "Authorization": f"Bearer {s4_token}",
        "X-CSRF-Token": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "multipart/mixed; boundary=batch_req",
        "Accept": "application/json"
    }
    
    req = urllib.request.Request(full_url, data=batch_body.encode("utf-8"), headers=headers, method="POST")
    with opener.open(req) as resp:
        return resp.read().decode("utf-8")

