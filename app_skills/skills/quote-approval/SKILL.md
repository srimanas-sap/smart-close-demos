---
name: quote-approval
description: Rules and tools to submit quote approvals to managers and poll for responses.
metadata:
  adk_additional_tools:
    - get_user_identity
    - get_manager_email
    - send_approval_email
    - check_approval_status
---
# Quote Approval Skill

This skill manages the manager quote approval flow.

## Operational Guide

1. **In-Chat Manager Approval Card Rendering (DEMO SIMULATION)**:
   - When a user asks to proceed with an opportunity, create a quote, or create a sales order, you MUST render an In-Chat **Manager Approval Card** matching the exact email template layout below.
   - **STRICT RULE**: Do NOT invoke `get_user_identity`, `get_manager_email`, or `send_approval_email` tools. Do NOT send external emails or output bullet points. Render ONLY the card below:
   
   ```markdown
   ### ✉️ Approval Required: New Quote
   
   **Dear Manager,**
   
   A new quote requires your approval before creation. Please review the details below:
   
   #### Opportunity Details
   | Field | Value |
   | :--- | :--- |
   | **Opportunity Name** | <Opportunity_Name> |
   | **Account Name** | <Account_Name> |
   | **Opportunity ID** | `<Opportunity_ID>` |
   | **Total Amount** | **$<Total_Amount>** |
   
   #### Requested Quote Items
   | Product | Qty | Price |
   | :--- | :---: | :---: |
   | <Product_Name_1> | <Qty_1> | $<Price_1> |
   | <Product_Name_2> | <Qty_2> | $<Price_2> |
   
   > ⚠️ **ACTION REQUIRED**: Please reply in this chat with **"APPROVED"** to proceed with Salesforce Quote & SAP Sales Order creation, or **"REJECTED"** with a reason if not approved.
   ```

2. **Approval Confirmation Handling**:
   - If the user's prompt explicitly contains **"APPROVED"** or **"Approve"**, treat the request as **APPROVED**. Immediately proceed to:
     1. Create Salesforce Quote (`create_salesforce_quote`) & Line Items (`create_salesforce_quote_line_item`).
     2. Create SAP Sales Order (`create_sales_order_header`).
     3. Update Salesforce Opportunity stage to `Closed Won` (`update_salesforce_opportunity`).
     4. Render the final Order Confirmation Summary.
