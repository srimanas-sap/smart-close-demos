# 🚀 Gemini SAP S/4HANA Enterprise Gateway (`sap-agent-app`)

A consolidated, production-grade **Unified Agent Gateway** connecting **Google Cloud Gemini Enterprise & ADK Agents** to **SAP S/4HANA** via **SAP BTP Integration Suite (APIM)** and **BTP Principal Propagation**.

---

## 🏗️ Unified Enterprise Architecture

```text
[Google Workspace / @google.com Users]
            │
            ▼ (Google IAP Authentication)
[Enterprise IAP Domain: https://demo-1850.1987984870407.demo.altostrat.com]
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Cloud Run Container: sap-agent-app (Unified Agent Gateway)               │
│                                                                         │
│  ├── GET  /         ──► Interactive Web Chat Playground UI               │
│  ├── POST /mcp      ──► Custom MCP Gateway for Gemini Enterprise        │
│  └── POST /api/chat ──► ADK Multi-Agent Engine (SAP + Salesforce)       │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ├──► [BTP Destination Service] (Exchanges user token for identity "MANAS")
            │
            ▼ (Bearer Token)
[SAP BTP Integration Suite (APIM)]
    ├── /MS_DEMOS_API_SALES_ORDER_SRV  (Sales Orders SD)
    ├── /API_MATERIAL_STOCK_SRV         (Material Stock MM)
    └── /API_CRDTMBUSINESSPARTNER       (Credit Management AR)
            │
            ▼ (Cloud Connector)
[SAP S/4HANA Backend System]
```

---

## 📦 Consolidated Codebase Structure

| File Name | Purpose & Role |
| :--- | :--- |
| **`sap_auth.py`** | 🔐 **Authentication Core**: Handles XSUAA SSO, exchanges BTP user tokens for S/4HANA Bearer tokens via Destination Service (`ms-smart-close-destination`), fetches CSRF tokens, and manages session cookies. |
| **`sap_api.py`** | ⚡ **Unified SAP Business APIs**: Single consolidated module containing all OData functions across Sales Orders (SD), Material Stock (MM), Credit Management (AR), and Invoices (AP). |
| **`sap_playground.py`** | 🚀 **Unified Gateway Server**: Multi-threaded Python server listening on `$PORT` serving Web UI (`GET /`), Web Chat API (`POST /api/chat`), and MCP JSON-RPC (`POST /mcp`). |
| **`agent.py`** | 🧠 **ADK Multi-Agent Definition**: Google Agent Development Kit (ADK) agent structure defining `SmartCloserAgent` (Root), `SalesforceAgent` (`sfdc`), `SapAgent` (`s4`), and Entity Mappings. |
| **`Dockerfile`** | 🐳 **Container Build Spec**: Production Docker specification for building `sap-agent-app`. |

---

## 🌐 Domain Modules & Capabilities

| Domain Module | APIM Proxy Base Path | Capabilities & Functions |
| :--- | :--- | :--- |
| **Sales Orders (SD)** <br>`sap_api.py` | `/MS_DEMOS_API_SALES_ORDER_SRV` | • View Header + Line Items & Plant (`get_sales_order`) <br>• Create Sales Orders via `$batch` POST (`create_sales_order`) <br>• Update PO Reference via `PATCH` (`update_sales_order`) |
| **Material Stock (MM)** <br>`sap_api.py` | `/API_MATERIAL_STOCK_SRV` | • Query live warehouse stock quantity & plant (`get_material_stock`) |
| **Credit Management (AR)** <br>`sap_api.py` | `/API_CRDTMBUSINESSPARTNER` | • Query FSCM credit limits & risk classes (`get_customer_credit_status`) |
| **Accounts Payable (AP)** <br>`sap_api.py` | `/MS_API_SUPPLIERINVOICE_PROCESS_SRV` | • Post Supplier Invoices (`create_supplier_invoice`) |

---

## 🚀 Running & Deploying

### 1. Run Locally:
```bash
python3 sap_playground.py
```
Open **`http://localhost:8501`** in Chrome.

### 2. Single Cloud Run Deployment Command:
```bash
gcloud run deploy sap-agent-app \
  --source . \
  --region us-central1 \
  --project smart-closer-agt-sap-slf-1850
```

---

## 🔒 Enterprise Security & Governance

- **Corporate SSO**: Protected by Google Identity-Aware Proxy (IAP) at `demo-1850.1987984870407.demo.altostrat.com`.
- **Identity Context**: Executes all SAP S/4HANA OData queries under principal propagation identity **`MANAS`**.
- **Error Classification**: Precise handling for `401 / 403 Authorization Failed` (EXTIDDN mapping missing), `404 Document Not Found`, and `500 API Exceptions`.
