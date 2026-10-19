---
name: identity-resolution
description: Translates Salesforce Account and Product identifiers to SAP Business Partner and Material IDs.
---
# Identity Resolution Skill

This skill translates identifiers between Salesforce and SAP.

## Operational Guide

1. **Multi-Item Identity Resolution (MANDATORY)**:
   - When resolving identifiers for multiple deals or products, NEVER invoke `identity_resolver.py` item-by-item in separate calls.
   - You MUST call `run_skill_script` ONCE to run `scripts/identity_resolver.py` passing all Account IDs via `--accounts <id1,id2>` and all Product Codes via `--products <code1,code2>`.
   - Example: `scripts/identity_resolver.py --accounts 001Ws000053hK4jIAE,001Ws000053hK4YIAU --products A-1000,A-5000`
   - Retrieve the `accounts` and `products` dictionaries from the JSON output.
   - Do NOT pass raw Salesforce Account IDs (e.g. starting with `001`) or raw Product codes to SAP tools.

3. **Product Name Lookup Matrix**:
   If the user queries about availability or quotes using a text description rather than a code, first resolve it to the Salesforce Product Code using this matrix:
   * `Battery, High Capacity` ➡️ `B-1000`
   * `Small Turbine` ➡️ `A-100`
   * `Large Turbine` ➡️ `A-1000`
   * `Energy Meter` ➡️ `E-1000`
   * `Starter Kit` ➡️ `A-5000`
   * `Power Inverter` ➡️ `H-36378`
   * `Connector Cables` ➡️ `C-300`
   * `Battery, Low Capacity` ➡️ `C-45678`
   * `Maintenance Contract` ➡️ `M-1000`
   * `Remote Monitoring Subscription` ➡️ `R-100`
   * `Labor` ➡️ `L-1000`
   * `Installation Services` ➡️ `INST-100`
   * `Performance Optimization` ➡️ `L-100`
   * `Solar Panel` ➡️ `S-100`
   * `Wind Generator` ➡️ `WT-GEN`
   * `Solar EV Charging Station` ➡️ `V-1000`
