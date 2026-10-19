#!/bin/bash
# Deploy Smart Closer Agent (app_skills) to Vertex AI Agent Engine
uv run -m app_skills.utils.deploy \
  --source-packages=./app_skills \
  --entrypoint-module=app_skills.agent_engine_app \
  --entrypoint-object=agent_engine \
  --requirements-file=app_skills/utils/.requirements.txt \
  --set-env-vars="GOOGLE_CLOUD_LOCATION=global,GOOGLE_CLOUD_REGION=us-central1,NUM_WORKERS=1,GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true,OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true" \
  --set-secrets="TOOLBOX_URL=sap-toolbox-url:latest,SFDC_BASE_URL=salesforce-mock-url:latest,SAP_BTP_TOKEN_URL=mcp-token-url:latest,SAP_BTP_EXCHANGE_URL=mcp-exchange-url:latest,SAP_BTP_CLIENT_ID=mcp-dl-id:latest,SAP_BTP_CLIENT_SECRET=mcp-dl-secret:latest,GEMINI_ENTERPRISE_SAP_AUTH_ID=ge-sap-auth-id-combined-ge-agent-template:latest,GEMINI_ENTERPRISE_SFDC_AUTH_ID=ge-sfdc-auth-id-combined-ge-agent-template:latest,AGENTMAIL_API_KEY=agentmail-api-key-ge-agent-template:latest"
