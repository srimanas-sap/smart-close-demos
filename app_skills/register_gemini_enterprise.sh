#!/bin/bash
# ==============================================================================
# Register Smart Closer Agent & SAP BTP OAuth SSO into Gemini Enterprise
# Matches the live Gemini Enterprise App:
#   Engine: gemini-enterprise-17842875_1784287591601
#   Agent:  Smart Closer Agent (reasoningEngines/3520413581034127360)
# ==============================================================================
set -e

PROJECT_ID="${PROJECT_ID:-smart-closer-agt-sap-slf-1850}"
PROJECT_NUMBER="${PROJECT_NUMBER:-483251484488}"
ENGINE_ID="${ENGINE_ID:-gemini-enterprise-17842875_1784287591601}"
REASONING_ENGINE_ID="${REASONING_ENGINE_ID:-3520413581034127360}"
AUTH_ID="${AUTH_ID:-sap_sso}"

TOKEN=$(gcloud auth print-access-token)

echo "=== 1. Registering SAP BTP OAuth 2.0 Authorization (${AUTH_ID}) in Gemini Enterprise ==="
curl -s -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/authorizations?authorizationId=${AUTH_ID}" \
  -d '{
    "displayName": "sap_sso",
    "serverSideOauth2": {
      "clientId": "sb-ms-demos-smartclose!t4152",
      "clientSecret": "<YOUR_SAP_BTP_XSUAA_CLIENT_SECRET>",
      "authorizationUri": "https://google-connectors-wlgpgm7r.authentication.us30.hana.ondemand.com/oauth/authorize?response_type=code",
      "tokenUri": "https://google-connectors-wlgpgm7r.authentication.us30.hana.ondemand.com/oauth/token"
    }
  }'

echo ""
echo "=== 2. Registering Smart Closer Agent in Gemini Enterprise Assistant ==="
curl -s -X POST \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_NUMBER}/locations/global/collections/default_collection/engines/${ENGINE_ID}/assistants/default_assistant/agents" \
  -d "{
    \"displayName\": \"Smart Closer Agent\",
    \"description\": \"An AI assistant for managing Quote-to-Cash (Q2C) workflows across Salesforce and SAP.\",
    \"adkAgentDefinition\": {
      \"provisionedReasoningEngine\": {
        \"reasoningEngine\": \"projects/${PROJECT_NUMBER}/locations/us-central1/reasoningEngines/${REASONING_ENGINE_ID}\"
      }
    },
    \"authorizationConfig\": {
      \"toolAuthorizations\": [
        \"projects/${PROJECT_NUMBER}/locations/global/authorizations/${AUTH_ID}\"
      ]
    },
    \"sharingConfig\": {
      \"scope\": \"ALL_USERS\"
    }
  }"
echo ""
