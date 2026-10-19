import os
from pathlib import Path
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools.skill_toolset import SkillToolset, load_skill_from_dir

from .prompts import (
    SMART_CLOSER_AGENT_INSTRUCTION,
    SALESFORCE_AGENT_INSTRUCTION,
    SAP_AGENT_INSTRUCTION,
)
from .tools import (
    ToolboxHttpTool,
    get_open_opportunities,
    execute_soql_query,
    create_salesforce_quote,
    create_salesforce_quote_line_item,
    update_salesforce_opportunity,
)

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")

MODEL_NAME = os.environ.get("AGENT_MODEL", "gemini-3-flash-preview")

# Load ADK Skills from app_skills/skills/
_SKILLS_ROOT = Path(__file__).parent / "skills"
skills_list = [
    load_skill_from_dir(_SKILLS_ROOT / "quote-approval"),
    load_skill_from_dir(_SKILLS_ROOT / "identity-resolution"),
]
skill_toolset = SkillToolset(skills=skills_list)

# 1. Salesforce Sub-Agent
salesforce_agent = Agent(
    name="SalesforceAgent",
    model=MODEL_NAME,
    instruction=SALESFORCE_AGENT_INSTRUCTION,
    tools=[
        get_open_opportunities,
        execute_soql_query,
        create_salesforce_quote,
        create_salesforce_quote_line_item,
        update_salesforce_opportunity,
        skill_toolset,
    ],
)

# 2. SAP Sub-Agent (backed by MCP Toolbox v2 SAP OData tools)
sap_agent = Agent(
    name="SapAgent",
    model=MODEL_NAME,
    instruction=SAP_AGENT_INSTRUCTION,
    tools=[
        ToolboxHttpTool("get_sap_credit_status", "Fetch credit limit and exposure for a Business Partner in SAP.", {}),
        ToolboxHttpTool("read_material_stock", "Read material stock levels from SAP.", {}),
        ToolboxHttpTool("create_sales_order_header", "Create a sales order header in SAP.", {}),
        ToolboxHttpTool("create_sales_order_item", "Create a sales order item in SAP.", {}),
        ToolboxHttpTool("read_sales_order_header", "Read sales order headers from SAP.", {}),
        ToolboxHttpTool("read_sales_order_item", "Read sales order line items from SAP.", {}),
        skill_toolset,
    ],
)

# 3. Root Orchestrator Agent
root_agent = Agent(
    name="SmartCloserAgent",
    model=MODEL_NAME,
    instruction=SMART_CLOSER_AGENT_INSTRUCTION,
    sub_agents=[salesforce_agent, sap_agent],
    tools=[skill_toolset],
)

app = App(name="app_skills", root_agent=root_agent)
