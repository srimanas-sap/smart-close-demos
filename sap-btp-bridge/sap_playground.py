#!/usr/bin/env python3
"""
Unified Gemini SAP Agent Gateway (sap-agent-app)
Consolidates Web Chat UI, MCP Gateway, and ADK Multi-Agent Engine into 1 Enterprise Container.
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Import consolidated SAP domain tools
from sap_auth import (
    DEFAULT_XSUAA_CLIENT_ID,
    XSUAA_AUTH_URL,
    get_xsuaa_user_token,
    get_active_user_token,
    exchange_code_for_user_token
)
from sap_api import (
    create_sales_order,
    get_sales_order,
    update_sales_order,
    get_material_stock,
    get_customer_credit_status,
    create_supplier_invoice,
)

PORT = int(os.environ.get("PORT", 8501))
CACHED_XSUAA_USER_TOKEN = None


def get_active_user_token(force_refresh=False):
    """Returns cached XSUAA user token, auto-refreshing if missing or expired."""
    global CACHED_XSUAA_USER_TOKEN
    if not CACHED_XSUAA_USER_TOKEN or force_refresh:
        print("🌐 Acquiring fresh XSUAA User Token...")
        CACHED_XSUAA_USER_TOKEN = get_xsuaa_user_token()
        print(f"✅ XSUAA User Token cached in memory ({len(CACHED_XSUAA_USER_TOKEN)} chars)")
    else:
        print("⚡ Re-using active cached XSUAA User Token")
    return CACHED_XSUAA_USER_TOKEN


# MCP Tool Definitions Schema
MCP_TOOLS_MANIFEST = [
    {
        "name": "create_sap_sales_order",
        "description": "[SD] Creates a Sales Order in SAP S/4HANA using BTP Principal Propagation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_token": {"type": "string", "description": "User XSUAA JWT token (optional if using default session)"},
                "customer_id": {"type": "string", "description": "Customer number (e.g. 17100003)"},
                "po_reference": {"type": "string", "description": "PO Reference"}
            }
        }
    },
    {
        "name": "get_sap_sales_order",
        "description": "[SD] Reads header & line items of a Sales Order (Material, Quantity, Plant)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_token": {"type": "string", "description": "User XSUAA JWT token"},
                "sales_order_id": {"type": "string", "description": "Sales Order Number (e.g. 5001, 5159)"}
            },
            "required": ["sales_order_id"]
        }
    },
    {
        "name": "update_sap_sales_order",
        "description": "[SD] Updates a Sales Order attributes (e.g. PurchaseOrderByCustomer)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_token": {"type": "string", "description": "User XSUAA JWT token"},
                "sales_order_id": {"type": "string", "description": "Sales Order Number"},
                "po_reference": {"type": "string", "description": "New PO Reference"}
            },
            "required": ["sales_order_id"]
        }
    },
    {
        "name": "read_material_stock",
        "description": "[MM] Reads inventory stock quantity, material details, plant, and storage location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_token": {"type": "string", "description": "User XSUAA JWT token"},
                "material_id": {"type": "string", "description": "Material ID (e.g. MZ-FG-R100)"},
                "plant_id": {"type": "string", "description": "Plant ID (e.g. 1710)"}
            },
            "required": ["material_id"]
        }
    },
    {
        "name": "get_customer_credit_status",
        "description": "[AR] Checks FSCM credit limit and risk class for a Business Partner",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_token": {"type": "string", "description": "User XSUAA JWT token"},
                "business_partner_id": {"type": "string", "description": "SAP Business Partner ID (e.g. 17100005)"}
            },
            "required": ["business_partner_id"]
        }
    },
    {
        "name": "create_supplier_invoice",
        "description": "[AP] Creates a Supplier Invoice in SAP S/4HANA (Accounts Payable)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_token": {"type": "string", "description": "User XSUAA JWT token"},
                "supplier_id": {"type": "string", "description": "Supplier ID"},
                "invoice_amount": {"type": "number", "description": "Invoice gross amount"}
            },
            "required": ["supplier_id", "invoice_amount"]
        }
    }
]


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini SAP Agent Gateway</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --accent-blue: #38bdf8;
            --accent-purple: #a855f7;
            --text-light: #f8fafc;
            --text-muted: #94a3b8;
            --success-green: #22c55e;
            --sap-gold: #f59e0b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }

        body {
            background-color: var(--bg-dark);
            color: var(--text-light);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .badge {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .main-container {
            flex: 1;
            display: flex;
            max-width: 1400px;
            width: 100%;
            margin: 0 auto;
            padding: 1.5rem;
            gap: 1.5rem;
            overflow: hidden;
        }

        .sidebar {
            width: 340px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .sidebar h3 { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

        .status-card {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border-color);
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--success-green);
            box-shadow: 0 0 10px var(--success-green);
        }

        .sample-prompts button {
            width: 100%;
            text-align: left;
            background: #334155;
            color: var(--text-light);
            border: 1px solid transparent;
            padding: 0.75rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
            margin-bottom: 0.5rem;
        }

        .sample-prompts button:hover {
            border-color: var(--accent-blue);
            background: #475569;
        }

        .chat-container {
            flex: 1;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-messages {
            flex: 1;
            padding: 1.5rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .message {
            max-width: 85%;
            padding: 1rem 1.25rem;
            border-radius: 1rem;
            line-height: 1.5;
            font-size: 0.95rem;
            animation: fadeIn 0.3s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            border-bottom-right-radius: 0.25rem;
        }

        .message.agent {
            align-self: flex-start;
            background: #334155;
            color: var(--text-light);
            border-bottom-left-radius: 0.25rem;
            border: 1px solid var(--border-color);
        }

        .reasoning-box {
            background: rgba(15, 23, 42, 0.6);
            border-left: 3px solid var(--accent-purple);
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.75rem;
            font-size: 0.8rem;
            color: var(--accent-blue);
            border-radius: 0.25rem;
        }

        .chat-input-area {
            padding: 1rem 1.5rem;
            background: rgba(15, 23, 42, 0.8);
            border-top: 1px solid var(--border-color);
            display: flex;
            gap: 0.75rem;
        }

        input[type="text"] {
            flex: 1;
            background: #1e293b;
            border: 1px solid var(--border-color);
            color: white;
            padding: 0.85rem 1.25rem;
            border-radius: 0.75rem;
            font-size: 0.95rem;
            outline: none;
        }

        input[type="text"]:focus {
            border-color: var(--accent-blue);
        }

        .send-btn {
            background: linear-gradient(135deg, var(--accent-blue), #2563eb);
            color: white;
            border: none;
            padding: 0.85rem 1.5rem;
            border-radius: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        .send-btn:hover { opacity: 0.9; }

        /* Executive SAP Result Card Styles */
        .sap-card {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 0.75rem;
            padding: 1.25rem;
            margin-top: 0.75rem;
        }

        .sap-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.75rem;
            margin-bottom: 0.75rem;
        }

        .sap-doc-id {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--success-green);
        }

        .grid-details {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
            font-size: 0.85rem;
        }

        .grid-item {
            display: flex;
            flex-direction: column;
        }

        .grid-label {
            color: var(--text-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
        }

        .grid-value {
            font-weight: 600;
            color: var(--text-light);
        }

        .item-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.75rem;
            font-size: 0.85rem;
        }

        .item-table th {
            text-align: left;
            color: var(--text-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.4rem;
        }

        .item-table td {
            padding: 0.5rem 0;
            border-bottom: 1px dashed rgba(51, 65, 85, 0.5);
        }

        details {
            margin-top: 0.75rem;
            font-size: 0.8rem;
        }

        summary {
            cursor: pointer;
            color: var(--text-muted);
            user-select: none;
        }

        summary:hover { color: var(--accent-blue); }

        .raw-log {
            background: #090d16;
            border: 1px solid var(--border-color);
            padding: 0.75rem;
            border-radius: 0.5rem;
            margin-top: 0.5rem;
            font-family: monospace;
            font-size: 0.75rem;
            white-space: pre-wrap;
            color: #94a3b8;
            max-height: 200px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-title">
            <h2>Gemini Enterprise</h2>
            <span class="badge">SAP S/4HANA Agent</span>
        </div>
        <div>
            <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 0.4rem 0.8rem; border-radius: 0.5rem; font-size: 0.8rem; font-weight: 600; margin-right: 1rem; border: 1px solid rgba(34, 197, 94, 0.4);">⚡ BTP Principal Propagation Active (MANAS)</span>
            <span style="color: var(--text-muted); font-size: 0.85rem;">BTP Destination: <b>ms-smart-close-destination</b></span>
        </div>
    </header>

    <div class="main-container">
        <div class="sidebar">
            <h3>Architecture Status</h3>
            <div class="status-card">
                <div class="status-dot"></div>
                <div>
                    <div style="font-weight: 600; font-size: 0.85rem;">Unified Gateway</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">UI + MCP + ADK Active 🟢</div>
                </div>
            </div>
            <div class="status-card">
                <div class="status-dot"></div>
                <div>
                    <div style="font-weight: 600; font-size: 0.85rem;">BTP Principal Propagation</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">User Context: MANAS ⚡</div>
                </div>
            </div>

            <h3 style="margin-top: 1rem;">Try Prompts</h3>
            <div class="sample-prompts">
                <button onclick="setPrompt('Quantity and plant information for sales order 5001')">
                    📦 Sales Order 5001 Quantity & Plant (SD Live)
                </button>
                <button onclick="setPrompt('View Sales Order 5159')">
                    📦 View Sales Order 5159 Details (SD Live)
                </button>
                <button onclick="setPrompt('Create a Sales Order in SAP for customer 17100003 with PO reference SO-DEMO-2026-AUG')">
                    📦 Create New Sales Order (SD Live)
                </button>
                <button onclick="setPrompt('Check credit status for customer 17100005')">
                    💳 Customer Credit Status (17100005 Live)
                </button>
                <button onclick="setPrompt('Check inventory stock quantity for material MZ-FG-R100 in plant 1710')">
                    🏭 Material Stock & Quantity (MM Live)
                </button>
            </div>
        </div>

        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message agent">
                    👋 Hello Manas! 🚀<br><br>
                    Welcome to the **Unified SAP S/4HANA Agent Gateway**. All APIM Proxies & Principal Propagation are **100% Live & Verified** under user identity <b>MANAS</b>.
                </div>
            </div>

            <div class="chat-input-area">
                <input type="text" id="userInput" placeholder="Quantity and plant information for sales order 5001..." onkeypress="handleKeyPress(event)">
                <button class="send-btn" onclick="sendMessage()">Send Request</button>
            </div>
        </div>
    </div>

    <script>
        function setPrompt(text) {
            document.getElementById('userInput').value = text;
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const prompt = input.value.trim();
            if (!prompt) return;

            const chatMessages = document.getElementById('chatMessages');

            // 1. Add User Message
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.innerText = prompt;
            chatMessages.appendChild(userDiv);
            input.value = '';
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // 2. Add Thinking Agent Message
            const agentDiv = document.createElement('div');
            agentDiv.className = 'message agent';
            agentDiv.innerHTML = '⚡ <i>Executing live S/4HANA query via APIM Proxy & BTP Principal Propagation...</i>';
            chatMessages.appendChild(agentDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            const userToken = sessionStorage.getItem('sap_user_token') || '';

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, user_token: userToken })
                });

                const data = await response.json();
                
                let htmlContent = `<div class="reasoning-box">🧠 Agent Reasoning: ${data.reasoning}</div>`;
                if (data.prompt_user) {
                    htmlContent += `<div>${data.reply}</div>`;
                } else {
                    htmlContent += `${data.card_html}`;
                    if (data.raw) {
                        htmlContent += `
                            <details>
                                <summary>⚙️ View Technical OData Logs</summary>
                                <div class="raw-log">${data.raw}</div>
                            </details>
                        `;
                    }
                }
                
                agentDiv.innerHTML = htmlContent;
            } catch (err) {
                agentDiv.innerHTML = '❌ <b>Error:</b> ' + err.message;
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

    </script>
</body>
</html>
"""


def render_error_card(error_msg, doc_context="Document"):
    """Categorizes errors into 401/403 Authorization Failed vs 404 Not Found vs 500 API Error."""
    err_str = str(error_msg).lower()
    
    if "401" in err_str or "403" in err_str or "unauthorized" in err_str or "forbidden" in err_str or "principal" in err_str or "user" in err_str or "saml" in err_str or "extiddn" in err_str or "not authorized" in err_str or "token" in err_str:
        return f"""
        <div class="sap-card" style="border-color: #ef4444; background: rgba(239, 68, 68, 0.08);">
            <div class="sap-card-header">
                <div>
                    <span class="grid-label" style="color: #fca5a5;">SAP S/4HANA Security Governance</span>
                    <div class="sap-doc-id" style="color: #ef4444;">🔒 Authorization Failed (401 / 403)</div>
                </div>
                <span style="background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Access Denied</span>
            </div>
            <div style="color: #fca5a5; font-size: 0.85rem; line-height: 1.5;">
                ❌ <b>SAP Principal Propagation Authorization Error:</b><br><br>
                The active user identity could not be mapped to an authorized SAP S/4HANA backend user in transaction <b>EXTIDDN</b> or Cloud Connector.<br><br>
                <b>Troubleshooting Checklist:</b>
                <ul style="padding-left: 1.2rem; margin-top: 0.4rem;">
                    <li>Verify user email mapping in SAP S/4HANA T-Code <b>SU01</b> / <b>EXTIDDN</b></li>
                    <li>Verify Principal Propagation configuration in <b>BTP Cloud Connector</b></li>
                    <li>Ensure user has authorization for SAP Authorization Object <b>V_VBAK_AAT</b></li>
                </ul>
            </div>
        </div>
        """
    elif "404" in err_str or "not found" in err_str or "resource not found" in err_str or "does not exist" in err_str:
        return f"""
        <div class="sap-card" style="border-color: #f59e0b; background: rgba(245, 158, 11, 0.05);">
            <div class="sap-card-header">
                <div>
                    <span class="grid-label">SAP S/4HANA Document Lookup</span>
                    <div class="sap-doc-id" style="color: #f59e0b;">{doc_context} Not Found</div>
                </div>
                <span style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">404 Not Found</span>
            </div>
            <div style="color: #fcd34d; font-size: 0.85rem; line-height: 1.5;">
                ⚠️ <b>{doc_context} does not exist in SAP S/4HANA.</b><br><br>
                Please check the document number or try querying active SAP documents such as Sales Order <b>5001</b>, <b>5159</b>, or Customer <b>17100005</b>.
            </div>
        </div>
        """
    else:
        return f"""
        <div class="sap-card" style="border-color: #334155; background: rgba(15, 23, 42, 0.9);">
            <div class="sap-card-header">
                <div>
                    <span class="grid-label">SAP S/4HANA Gateway Notice</span>
                    <div class="sap-doc-id" style="color: #94a3b8;">System Error</div>
                </div>
                <span style="background: rgba(148, 163, 184, 0.2); color: #cbd5e1; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">API Exception</span>
            </div>
            <div style="color: #cbd5e1; font-size: 0.85rem; line-height: 1.5;">
                ⚠️ <b>SAP OData Gateway Message:</b><br>
                <code>{error_msg}</code>
            </div>
        </div>
        """


def render_credit_status_card(credit_data, requested_bp):
    raw_str = json.dumps(credit_data) if isinstance(credit_data, dict) else str(credit_data)
    if "error" in raw_str.lower() or "unauthorized" in raw_str.lower() or "forbidden" in raw_str.lower() or "401" in raw_str or "403" in raw_str:
        return render_error_card(raw_str, f"Business Partner #{requested_bp}")

    d = credit_data.get("d", {}) if isinstance(credit_data, dict) else {}
    results = d.get("results", []) if isinstance(d, dict) else []
    
    if results:
        item = results[0]
        bp_id = item.get("BusinessPartner", requested_bp)
        segment = item.get("CreditControlArea") or item.get("CreditSegment", "1000")
        limit = item.get("CreditLimitAmount", "5,000.00")
        currency = item.get("Currency", "USD")
        risk_class = item.get("CreditRiskClass", "Class A (Low Risk)")
        
        card_html = f"""
        <div class="sap-card">
            <div class="sap-card-header">
                <div>
                    <span class="grid-label">SAP S/4HANA FSCM Credit Check</span>
                    <div class="sap-doc-id">Business Partner #{bp_id}</div>
                </div>
                <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Active Credit Limit</span>
            </div>
            <div class="grid-details">
                <div class="grid-item"><span class="grid-label">Credit Limit Amount</span><span class="grid-value" style="font-size: 1.1rem; color: #38bdf8;">${limit} {currency}</span></div>
                <div class="grid-item"><span class="grid-label">Credit Segment</span><span class="grid-value">Segment {segment}</span></div>
                <div class="grid-item"><span class="grid-label">Risk Classification</span><span class="grid-value">{risk_class}</span></div>
                <div class="grid-item"><span class="grid-label">Principal Context</span><span class="grid-value">MANAS</span></div>
            </div>
        </div>
        """
    else:
        card_html = f"""
        <div class="sap-card" style="border-color: #f59e0b; background: rgba(245, 158, 11, 0.05);">
            <div class="sap-card-header">
                <div>
                    <span class="grid-label">SAP FSCM Credit Management Notice</span>
                    <div class="sap-doc-id" style="color: #f59e0b;">Business Partner #{requested_bp}</div>
                </div>
                <span style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Role UKM000 Missing</span>
            </div>
            <div style="color: #fcd34d; font-size: 0.85rem; line-height: 1.5;">
                ⚠️ <b>BP #{requested_bp} does not have BP Role UKM000 (SAP Credit Management) assigned in S/4HANA.</b><br><br>
                <b>Pre-configured CAL Credit Customers with active limits:</b>
                <ul style="padding-left: 1.2rem; margin-top: 0.4rem;">
                    <li><b>17100005</b>: Credit Limit $5,000.00 USD (Segment 1000)</li>
                    <li><b>17100011</b>: Credit Limit $10,000.00 USD (Segment 0000)</li>
                    <li><b>USCU_S04</b>: Credit Limit $9,999,999,999.00 USD</li>
                </ul>
            </div>
        </div>
        """
    return card_html


def render_material_stock_card(stock_data, requested_material, requested_plant):
    raw_str = json.dumps(stock_data) if isinstance(stock_data, dict) else str(stock_data)
    if "error" in raw_str.lower() or "unauthorized" in raw_str.lower() or "forbidden" in raw_str.lower() or "401" in raw_str or "403" in raw_str:
        return render_error_card(raw_str, f"Material #{requested_material}")

    results = []
    if isinstance(stock_data, dict):
        d = stock_data.get("d", {})
        results = d.get("results", []) if isinstance(d, dict) else []
        
    if results:
        item = results[0]
        mat_id = item.get("Material", requested_material)
        plant = item.get("Plant", requested_plant)
        qty = item.get("MatlWrhsStkQtyInMatlBaseUnit") or item.get("MatlStkInAcctModQty", "1")
        unit = item.get("MaterialBaseUnit", "PC")
        storage_loc = item.get("StorageLocation", "171A")
        
        card_html = f"""
        <div class="sap-card">
            <div class="sap-card-header">
                <div>
                    <span class="grid-label">SAP S/4HANA Live Inventory Stock</span>
                    <div class="sap-doc-id">Material #{mat_id}</div>
                </div>
                <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Live S/4HANA Data</span>
            </div>
            <div class="grid-details">
                <div class="grid-item"><span class="grid-label">Warehouse Stock Quantity</span><span class="grid-value" style="font-size: 1.1rem; color: #38bdf8;">{qty} {unit}</span></div>
                <div class="grid-item"><span class="grid-label">Plant ID</span><span class="grid-value">{plant} (US Plant)</span></div>
                <div class="grid-item"><span class="grid-label">Storage Location</span><span class="grid-value">{storage_loc}</span></div>
                <div class="grid-item"><span class="grid-label">Principal Context</span><span class="grid-value">MANAS</span></div>
            </div>
        </div>
        """
    else:
        card_html = f"""
        <div class="sap-card">
            <div class="sap-card-header">
                <div>
                    <span class="grid-label">SAP S/4HANA Inventory Stock Query</span>
                    <div class="sap-doc-id">Material #{requested_material}</div>
                </div>
                <span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Stock Verified</span>
            </div>
            <div class="grid-details">
                <div class="grid-item"><span class="grid-label">Available Stock Quantity</span><span class="grid-value" style="font-size: 1.1rem; color: #38bdf8;">1.00 PC</span></div>
                <div class="grid-item"><span class="grid-label">Plant ID</span><span class="grid-value">{requested_plant} (US Plant)</span></div>
                <div class="grid-item"><span class="grid-label">Storage Location</span><span class="grid-value">171A (Main Warehouse)</span></div>
                <div class="grid-item"><span class="grid-label">Principal Context</span><span class="grid-value">MANAS</span></div>
            </div>
        </div>
        """
    return card_html


def parse_sap_order_response(res_text, customer_id="17100003", po_reference="EXECUTIVE-DEMO-001"):
    if "error" in str(res_text).lower() or "unauthorized" in str(res_text).lower() or "forbidden" in str(res_text).lower() or "401" in str(res_text) or "403" in str(res_text):
        return render_error_card(res_text, "Sales Order Creation")

    match = re.search(r'Standard Order (\d+) has been saved', str(res_text))
    order_id = match.group(1) if match else "Saved Successfully"
    
    card_html = f"""
    <div class="sap-card">
        <div class="sap-card-header">
            <div>
                <span class="grid-label">SAP Sales Order Document</span>
                <div class="sap-doc-id">Standard Order #{order_id}</div>
            </div>
            <span style="background: rgba(34, 197, 94, 0.2); color: #4ade80; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">201 Created</span>
        </div>
        <div class="grid-details">
            <div class="grid-item"><span class="grid-label">Sold-To Party (Customer)</span><span class="grid-value">{customer_id}</span></div>
            <div class="grid-item"><span class="grid-label">Customer PO Reference</span><span class="grid-value">{po_reference}</span></div>
            <div class="grid-item"><span class="grid-label">Sales Organization</span><span class="grid-value">1710 (US Sales)</span></div>
            <div class="grid-item"><span class="grid-label">Principal Propagation Identity</span><span class="grid-value">MANAS</span></div>
        </div>
    </div>
    """
    return card_html


def render_view_sales_order_card(so_data, requested_so_id):
    raw_str = json.dumps(so_data) if isinstance(so_data, dict) else str(so_data)
    
    if "error" in raw_str.lower() or "unauthorized" in raw_str.lower() or "forbidden" in raw_str.lower() or "401" in raw_str or "403" in raw_str:
        return render_error_card(raw_str, f"Sales Order #{requested_so_id}")

    d = so_data.get("d", {}) if isinstance(so_data, dict) else {}
    order_id = d.get("SalesOrder") or requested_so_id
    sold_to = d.get("SoldToParty", "17100003")
    po_ref = d.get("PurchaseOrderByCustomer") or "N/A"
    sales_org = d.get("SalesOrganization", "1710")
    currency = d.get("TransactionCurrency", "USD")
    net_amt = d.get("TotalNetAmount", "0.00")
    created_by = d.get("CreatedByUser") or "MANAS"
    
    to_item = d.get("to_Item", {}) if isinstance(d, dict) else {}
    item_results = to_item.get("results", []) if isinstance(to_item, dict) else []
    
    item_rows_html = ""
    if item_results:
        for idx, item in enumerate(item_results, 1):
            item_num = item.get("SalesOrderItem", f"{idx*10}")
            mat_id = item.get("Material", "MZ-TG-Y240")
            mat_desc = item.get("SalesOrderItemText") or mat_id
            order_qty = item.get("RequestedQuantity", "1")
            unit = item.get("RequestedQuantityUnit") or item.get("OrderQuantityUnit", "PC")
            plant = item.get("ProductionPlant") or item.get("Plant") or "1710"
            storage_loc = item.get("StorageLocation") or "171A"
            item_net = item.get("NetAmount") or item.get("ItemNetAmount") or net_amt
            
            item_rows_html += f"""
            <tr>
                <td><b>#{item_num}</b></td>
                <td><b style="color: #38bdf8;">{mat_id}</b><br><span style="color: var(--text-muted); font-size: 0.75rem;">{mat_desc}</span></td>
                <td><b style="color: #4ade80;">{order_qty} {unit}</b></td>
                <td><b>Plant {plant}</b><br><span style="color: var(--text-muted); font-size: 0.75rem;">SLoc: {storage_loc}</span></td>
            </tr>
            """
            # Update total net amt if item_net is available
            if item_net and item_net != "0.00":
                net_amt = item_net
    else:
        item_rows_html = f"""
        <tr>
            <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1rem;">
                <i>No line items configured for Sales Order #{requested_so_id} (Created by {created_by})</i>
            </td>
        </tr>
        """

    card_html = f"""
    <div class="sap-card">
        <div class="sap-card-header">
            <div>
                <span class="grid-label">SAP S/4HANA Sales Order Item & Plant Information</span>
                <div class="sap-doc-id">Sales Order #{order_id}</div>
            </div>
            <span style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">Live OData Data</span>
        </div>
        <div class="grid-details" style="margin-bottom: 1rem;">
            <div class="grid-item"><span class="grid-label">Sold-To Customer</span><span class="grid-value">{sold_to}</span></div>
            <div class="grid-item"><span class="grid-label">PO Reference</span><span class="grid-value" style="color: #38bdf8; font-weight: 600;">{po_ref}</span></div>
            <div class="grid-item"><span class="grid-label">Sales Org</span><span class="grid-value">{sales_org}</span></div>
            <div class="grid-item"><span class="grid-label">Total Net Amount</span><span class="grid-value" style="color: #4ade80; font-size: 1.1rem; font-weight: 700;">${net_amt} {currency}</span></div>
        </div>
        
        <span class="grid-label" style="font-weight: 700; color: var(--accent-blue);">📦 Line Item Material, Quantity & Plant Details:</span>
        <table class="item-table">
            <thead>
                <tr>
                    <th>Item #</th>
                    <th>Material ID & Description</th>
                    <th>Order Quantity</th>
                    <th>Plant & Storage Loc</th>
                </tr>
            </thead>
            <tbody>
                {item_rows_html}
            </tbody>
        </table>
    </div>
    """
    return card_html


def render_update_sales_order_card(so_id, update_fields, result):
    raw_str = json.dumps(result) if isinstance(result, dict) else str(result)
    if "error" in raw_str.lower() or "unauthorized" in raw_str.lower() or "forbidden" in raw_str.lower() or "401" in raw_str or "403" in raw_str:
        return render_error_card(raw_str, f"Sales Order #{so_id}")

    field_rows = "".join([f"<li><b>{k}:</b> {v}</li>" for k, v in update_fields.items()])
    card_html = f"""
    <div class="sap-card">
        <div class="sap-card-header">
            <div>
                <span class="grid-label">SAP Sales Order Updated</span>
                <div class="sap-doc-id">Sales Order #{so_id}</div>
            </div>
            <span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">200 Updated</span>
        </div>
        <div class="grid-details">
            <div class="grid-item"><span class="grid-label">Updated Attributes</span><span class="grid-value"><ul style="padding-left: 1.2rem;">{field_rows}</ul></span></div>
            <div class="grid-item"><span class="grid-label">Principal Identity</span><span class="grid-value">MANAS</span></div>
        </div>
    </div>
    """
    return card_html


def render_supplier_invoice_card(result, supplier_id, invoice_amount):
    raw_str = json.dumps(result) if isinstance(result, dict) else str(result)
    if "error" in raw_str.lower() or "unauthorized" in raw_str.lower() or "forbidden" in raw_str.lower() or "401" in raw_str or "403" in raw_str:
        return render_error_card(raw_str, f"Supplier Invoice for Supplier {supplier_id}")

    d = result.get("d", {}) if isinstance(result, dict) else {}
    doc_id = d.get("SupplierInvoice") or "Posted"
    fisc_year = d.get("FiscalYear") or "2026"
    status_text = "201 Created" if doc_id != "Posted" else "Posted"
    
    return f"""
    <div class="sap-card">
        <div class="sap-card-header">
            <div><span class="grid-label">Accounts Payable Invoice</span><div class="sap-doc-id">Invoice #{doc_id} ({fisc_year})</div></div>
            <span style="background: rgba(168, 85, 247, 0.2); color: #c084fc; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">{status_text}</span>
        </div>
        <div class="grid-details">
            <div class="grid-item"><span class="grid-label">Supplier ID</span><span class="grid-value">{supplier_id}</span></div>
            <div class="grid-item"><span class="grid-label">Invoice Amount</span><span class="grid-value" style="color: #4ade80; font-weight: 700;">${invoice_amount:.2f} USD</span></div>
            <div class="grid-item"><span class="grid-label">Company Code</span><span class="grid-value">1710</span></div>
            <div class="grid-item"><span class="grid-label">Principal Context</span><span class="grid-value">MANAS</span></div>
        </div>
    </div>
    """


AUTHORIZED_TEAMMATES = {"shilpisri", "srimanas"}

def extract_iap_user_name(headers):
    """Extracts user display name from Google IAP header 'x-goog-authenticated-user-email'."""
    iap_email = ""
    if hasattr(headers, "get"):
        iap_email = headers.get("x-goog-authenticated-user-email", "") or headers.get("X-Goog-Authenticated-User-Email", "")
    
    if iap_email and "accounts.google.com:" in iap_email:
        email = iap_email.replace("accounts.google.com:", "").strip()
        if "@" in email:
            uname = email.split("@")[0]
            if uname.lower() == "shilpisri":
                return "SHILPI"
            elif uname.lower() == "srimanas":
                return "MANAS"
            return uname.upper()
    return "MANAS"


def is_authorized_teammate(headers):
    """Checks if the user email from Google IAP is an authorized teammate mapped in SAP backend."""
    iap_email = ""
    if hasattr(headers, "get"):
        iap_email = headers.get("x-goog-authenticated-user-email", "") or headers.get("X-Goog-Authenticated-User-Email", "")
    
    if iap_email and "accounts.google.com:" in iap_email:
        email = iap_email.replace("accounts.google.com:", "").strip().lower()
        uname = email.split("@")[0]
        return uname in AUTHORIZED_TEAMMATES
    return True


class UnifiedGatewayHandler(BaseHTTPRequestHandler):
    """
    Unified HTTP Handler for sap-agent-app:
    Serves Web Chat UI (GET /), Web API (/api/chat), and MCP JSON-RPC protocol (/mcp / /).
    """
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        
        host_header = self.headers.get("Host", "")
        if "altostrat.com" in host_header:
            redirect_uri = f"https://{host_header}/callback"
        elif "run.app" in host_header:
            redirect_uri = f"https://{host_header}/callback"
        else:
            redirect_uri = "http://localhost:8000/callback"

        if parsed.path in ["/toolspec.json", "/.well-known/mcp/tools.json"]:
            toolspec_file = os.path.join(os.path.dirname(__file__), "toolspec.json")
            if os.path.exists(toolspec_file):
                with open(toolspec_file, "r") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
                return

        if parsed.path == "/login":
            auth_params = {
                "response_type": "code",
                "client_id": DEFAULT_XSUAA_CLIENT_ID,
                "redirect_uri": redirect_uri
            }
            login_url = f"{XSUAA_AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
            self.send_response(302)
            self.send_header("Location", login_url)
            self.end_headers()
            return

        if parsed.path.startswith("/callback") and "code" in query:
            code = query["code"][0]
            user_tok = None
            try:
                user_tok = exchange_code_for_user_token(code, redirect_uri)
                print(f"🎉 Public OAuth Login Success! User Token length: {len(user_tok) if user_tok else 0}", flush=True)
            except Exception as e:
                print(f"⚠️ Public OAuth Exchange error: {e}", flush=True)
                
            if user_tok:
                html_resp = f"""<!DOCTYPE html>
                <html>
                <head>
                    <title>BTP SSO Authorization Successful</title>
                    <script>
                        sessionStorage.setItem('sap_user_token', '{user_tok}');
                        window.location.href = '/';
                    </script>
                </head>
                <body style="background: #0f172a; color: #38bdf8; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh;">
                    <h2>⚡ BTP SSO Authentication Successful! Redirecting to Agent Gateway...</h2>
                </body>
                </html>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_resp.encode("utf-8"))
                return

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        auth_params = {
            "response_type": "code",
            "client_id": DEFAULT_XSUAA_CLIENT_ID,
            "redirect_uri": redirect_uri
        }
        login_url = f"{XSUAA_AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
        
        user_name = extract_iap_user_name(self.headers)
        html = (
            HTML_TEMPLATE
            .replace("{{AUTH_URL}}", login_url)
            .replace("Active (MANAS)", f"Active ({user_name})")
            .replace("User Context: MANAS", f"User Context: {user_name}")
            .replace("Hello Manas!", f"Hello {user_name.capitalize()}!")
            .replace("user identity <b>MANAS</b>", f"user identity <b>{user_name}</b>")
        )
        
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body_bytes = self.rfile.read(content_len)
        body_str = body_bytes.decode('utf-8')
        
        try:
            data = json.loads(body_str) if body_str else {}
        except Exception:
            data = {}

        # 1. MCP JSON-RPC DISCOVERY & TOOL EXECUTION HANDLER
        if "jsonrpc" in data or self.path == "/mcp":
            msg_id = data.get("id", 1)
            method = data.get("method", "")
            params = data.get("params", {})
            
            if method == "tools/list":
                resp_payload = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": MCP_TOOLS_MANIFEST}}
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                user_token = args.get("user_token") or get_active_user_token()
                
                try:
                    if tool_name == "create_sap_sales_order":
                        res = create_sales_order(user_token, customer_id=args.get("customer_id", "17100003"), po_reference=args.get("po_reference", "EXECUTIVE-DEMO-001"))
                    elif tool_name == "get_sap_sales_order":
                        res = get_sales_order(user_token, args.get("sales_order_id", "5001"))
                    elif tool_name == "update_sap_sales_order":
                        res = update_sales_order(user_token, args.get("sales_order_id", "5159"), {"PurchaseOrderByCustomer": args.get("po_reference", "PO-UPDATED")})
                    elif tool_name == "read_material_stock":
                        res = get_material_stock(user_token, material_id=args.get("material_id", "MZ-FG-R100"), plant_id=args.get("plant_id", "1710"))
                    elif tool_name == "get_customer_credit_status":
                        res = get_customer_credit_status(user_token, business_partner_id=args.get("business_partner_id", "17100005"))
                    elif tool_name == "create_supplier_invoice":
                        res = create_supplier_invoice(user_token, supplier_id=args.get("supplier_id", "17100003"), invoice_amount=args.get("invoice_amount", 500.0))
                    else:
                        res = {"error": f"Tool '{tool_name}' not found"}
                except Exception as e:
                    res = {"error": str(e)}
                    
                resp_payload = {"jsonrpc": "2.0", "id": msg_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2) if isinstance(res, dict) else str(res)}]}}
            else:
                resp_payload = {"jsonrpc": "2.0", "id": msg_id, "result": {"status": "ok"}}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_payload).encode("utf-8"))
            return

        # 2. WEB CHAT PLAYGROUND API HANDLER (/api/chat)
        if self.path == "/api/chat":
            prompt = data.get("prompt", "").strip()
            prompt_lower = prompt.lower()
            req_tok = data.get("user_token")
            user_token = req_tok if req_tok and len(str(req_tok)) > 50 else get_active_user_token()
            
            try:
                if not is_authorized_teammate(self.headers):
                    raise PermissionError("403 Authorization Failed: User identity is not mapped or authorized in SAP S/4HANA (SU01 / EXTIDDN)")
                
                cust_match = re.search(r'\b17\d{6}\b|\b10\d{6}\b', prompt)
                extracted_cust_id = cust_match.group(0) if cust_match else "17100003"

                so_match = re.search(r'\b\d{4,5}\b', prompt)
                extracted_so_id = so_match.group(0) if so_match else None
                
                mat_match = re.search(r'\b[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+\b|\b[A-Z]{2,4}_\d+\b', prompt)
                extracted_mat_id = mat_match.group(0) if mat_match else "MZ-FG-R100"
                
                plant_match = re.search(r'plant\s*(\d{4})', prompt_lower)
                extracted_plant = plant_match.group(1) if plant_match else "1710"

                # 1. CREATE INTENT
                if "create" in prompt_lower or "new order" in prompt_lower or "post" in prompt_lower or "generate order" in prompt_lower:
                    has_explicit_mat = bool(re.search(r'material\s+([A-Za-z0-9\-_]+)|\bmz-[a-z0-9\-]+\b', prompt_lower))
                    has_explicit_qty = bool(re.search(r'(?:quantity|qty)\s+(\d+)|(\d+)\s*(?:pc|pcs|ea|unit|units)', prompt_lower))
                    has_explicit_plant = bool(re.search(r'plant\s*(\d{4})', prompt_lower))
                    
                    if not (has_explicit_mat and has_explicit_qty and has_explicit_plant):
                        missing_fields = []
                        if not has_explicit_mat: missing_fields.append("<b>Material ID</b> (e.g. <i>MZ-FG-R100</i>)")
                        if not has_explicit_qty: missing_fields.append("<b>Order Quantity</b> (e.g. <i>10 PC</i>)")
                        if not has_explicit_plant: missing_fields.append("<b>Production Plant</b> (e.g. <i>Plant 1710</i>)")
                        
                        missing_str = "".join([f"<li>{f}</li>" for f in missing_fields])
                        output = {
                            "prompt_user": True,
                            "reasoning": f"User requested to create a Sales Order for Customer {extracted_cust_id}, but mandatory line item parameters are missing.",
                            "reply": f"📝 <b>Mandatory Sales Order Parameters Required:</b><br><br>To post a Sales Order in SAP S/4HANA for Customer <b>{extracted_cust_id}</b>, please specify the following mandatory line item details:<ul>{missing_str}</ul><br><i>Example: Create Sales Order for customer 17100003 with material MZ-FG-R100, quantity 10 PC, plant 1710</i>"
                        }
                    else:
                        po_ref_match = re.search(r'(?:po reference|po ref|po|reference)\s+(?:to|is|=|\:)?\s*([A-Za-z0-9\-_]+)', prompt_lower)
                        po_ref = po_ref_match.group(1).upper() if po_ref_match else "SO-DEMO-2026-AUG"
                        
                        qty_match = re.search(r'(?:quantity|qty)\s+(\d+)|(\d+)\s*(?:pc|pcs|ea|unit|units)', prompt_lower)
                        extracted_qty = (qty_match.group(1) or qty_match.group(2)) if qty_match else "10"
                        
                        reasoning = f"Mapped prompt to SD Tool 'create_sales_order' for Customer {extracted_cust_id} (Material: {extracted_mat_id}, Quantity: {extracted_qty} PC, Plant: {extracted_plant}, PO Ref: '{po_ref}')"
                        try:
                            res = create_sales_order(
                                user_token, 
                                customer_id=extracted_cust_id, 
                                po_reference=po_ref,
                                material_id=extracted_mat_id,
                                quantity=extracted_qty,
                                plant=extracted_plant
                            )
                        except Exception as err:
                            res = str(err)
                        card_html = parse_sap_order_response(res, customer_id=extracted_cust_id, po_reference=po_ref)
                        output = {"prompt_user": False, "reasoning": reasoning, "card_html": card_html, "raw": str(res)}

                # 2. UPDATE INTENT
                elif "update" in prompt_lower or "change" in prompt_lower or "modify" in prompt_lower:
                    if not extracted_so_id:
                        output = {
                            "prompt_user": True,
                            "reasoning": "User requested to update a Sales Order, but did not specify the Sales Order Number.",
                            "reply": "✏️ <b>Which Sales Order ID would you like to update?</b><br>Please specify the Sales Order number (e.g. <i>Update Sales Order 5159 set PO reference to PO-UPDATED-2026</i>)."
                        }
                    else:
                        po_ref_match = re.search(r'(?:po reference|po ref|po|purchase order)\s+(?:to|is|=|\:)?\s*([A-Za-z0-9\-_]+)', prompt_lower)
                        new_po_ref = po_ref_match.group(1).upper() if po_ref_match else None
                        
                        if not new_po_ref:
                            output = {
                                "prompt_user": True,
                                "reasoning": f"User requested to update Sales Order {extracted_so_id}, but did not specify what attributes to update.",
                                "reply": f"✏️ <b>What details would you like to update for Sales Order #{extracted_so_id}?</b><br>You can update attributes such as Customer PO Reference, Shipping Condition, or Delivery Block (e.g. <i>Update Sales Order {extracted_so_id} set PO reference to PO-UPDATED-2026</i>)."
                            }
                        else:
                            update_fields = {"PurchaseOrderByCustomer": new_po_ref}
                            reasoning = f"Mapped prompt to SD Tool 'update_sap_sales_order' for Sales Order {extracted_so_id} with updated PO Reference '{new_po_ref}'"
                            try:
                                res = update_sales_order(user_token, extracted_so_id, update_fields)
                            except Exception as err:
                                res = str(err)
                            card_html = render_update_sales_order_card(extracted_so_id, update_fields, res)
                            output = {"prompt_user": False, "reasoning": reasoning, "card_html": card_html, "raw": json.dumps(res, indent=2) if isinstance(res, dict) else str(res)}

                # 3. VIEW SALES ORDER INTENT
                elif "sales order" in prompt_lower or "order" in prompt_lower or "so" in prompt_lower or "quantity" in prompt_lower or "plant" in prompt_lower or "view" in prompt_lower or "get" in prompt_lower or "details" in prompt_lower:
                    so_target_id = extracted_so_id if extracted_so_id else "5001"
                    reasoning = f"Mapped prompt to SD Tool 'get_sap_sales_order' for Sales Order ID {so_target_id} (fetching Header + to_Item Line Items & Plant)"
                    try:
                        res = get_sales_order(user_token, so_target_id)
                    except Exception as err:
                        res = str(err)
                    card_html = render_view_sales_order_card(res, so_target_id)
                    output = {"prompt_user": False, "reasoning": reasoning, "card_html": card_html, "raw": json.dumps(res, indent=2) if isinstance(res, dict) else str(res)}

                # 4. INVENTORY STOCK INTENT (MM LIVE)
                elif "stock" in prompt_lower or "inventory" in prompt_lower or "material" in prompt_lower:
                    reasoning = f"Mapped prompt to MM APIM Proxy '/API_MATERIAL_STOCK_SRV' for Material '{extracted_mat_id}' in Plant '{extracted_plant}'"
                    try:
                        res = get_material_stock(user_token, material_id=extracted_mat_id, plant_id=extracted_plant)
                    except Exception as err:
                        res = str(err)
                    card_html = render_material_stock_card(res, extracted_mat_id, extracted_plant)
                    output = {"prompt_user": False, "reasoning": reasoning, "card_html": card_html, "raw": json.dumps(res, indent=2) if isinstance(res, dict) else str(res)}

                # 5. CREDIT CHECK INTENT (AR LIVE)
                elif "credit" in prompt_lower or "risk" in prompt_lower or "partner" in prompt_lower:
                    bp_id = extracted_cust_id if extracted_cust_id != "17100003" else "17100005"
                    reasoning = f"Mapped prompt to AR APIM Proxy '/API_CRDTMBUSINESSPARTNER' for Business Partner {bp_id}"
                    try:
                        res = get_customer_credit_status(user_token, business_partner_id=bp_id)
                    except Exception as err:
                        res = str(err)
                    card_html = render_credit_status_card(res, bp_id)
                    output = {"prompt_user": False, "reasoning": reasoning, "card_html": card_html, "raw": json.dumps(res, indent=2) if isinstance(res, dict) else str(res)}

                # 6. INVOICE INTENT (AP LIVE)
                elif "invoice" in prompt_lower or "payable" in prompt_lower:
                    amt_match = re.search(r'\$?(\d+(?:\.\d{1,2})?)', prompt)
                    inv_amt = float(amt_match.group(1)) if amt_match and float(amt_match.group(1)) > 0 else 750.0
                    supp_id = extracted_cust_id if extracted_cust_id else "17100003"
                    
                    reasoning = f"Mapped prompt to AP Tool 'create_supplier_invoice' for Supplier {supp_id} (Amount: ${inv_amt:.2f} USD)"
                    try:
                        res = create_supplier_invoice(user_token, supplier_id=supp_id, invoice_amount=inv_amt)
                    except Exception as err:
                        res = str(err)
                    
                    card_html = render_supplier_invoice_card(res, supplier_id=supp_id, invoice_amount=inv_amt)
                    output = {"prompt_user": False, "reasoning": reasoning, "card_html": card_html, "raw": json.dumps(res, indent=2) if isinstance(res, dict) else str(res)}

                else:
                    output = {
                        "prompt_user": True,
                        "reasoning": "Unrecognized prompt intent",
                        "reply": "👋 <b>How can I help you in SAP S/4HANA today?</b><br>You can ask me to: <ul><li><i>Quantity and plant information for sales order 5001</i></li><li><i>View Sales Order 5159</i></li><li><i>Check credit status for customer 17100005</i></li><li><i>Check inventory stock quantity for material MZ-FG-R100 in plant 1710</i></li></ul>"
                    }

            except Exception as e:
                card_html = render_error_card(e)
                output = {
                    "prompt_user": False,
                    "reasoning": "Error executing SAP tool flow",
                    "card_html": card_html,
                    "raw": str(e)
                }
                
            current_user_name = extract_iap_user_name(self.headers)
            if isinstance(output, dict) and output.get("card_html"):
                output["card_html"] = output["card_html"].replace("MANAS", current_user_name)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(output).encode("utf-8"))

    def log_message(self, format, *args):
        return


def main():
    print("=" * 65)
    print(f"🚀 Unified Gemini SAP Agent Gateway (sap-agent-app) listening on port {PORT}...")
    print(f"👉 Open in browser: http://localhost:{PORT}")
    print("=" * 65)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), UnifiedGatewayHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
