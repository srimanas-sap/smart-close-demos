import os

_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def _read_prompt(filename: str) -> str:
    path = os.path.join(_PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if "</system_instruction>" in content:
        return content.split("</system_instruction>")[0].replace("<system_instruction>", "").strip()
    return content.strip()

SMART_CLOSER_AGENT_INSTRUCTION = _read_prompt("SmartCloserAgent.md")
SALESFORCE_AGENT_INSTRUCTION = _read_prompt("SalesforceAgent.md")
SAP_AGENT_INSTRUCTION = _read_prompt("SapAgent.md")
