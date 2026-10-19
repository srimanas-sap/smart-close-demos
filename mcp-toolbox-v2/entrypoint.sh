#!/bin/sh

if [ -n "$BTP_DL_ID" ] && [ -n "$BTP_DL_SECRET" ] && [ -n "$BTP_TOKEN_URL" ]; then
    echo "Fetching fresh BTP bootstrap token for startup schema initialization..."
    TOKEN=$(curl -s -X POST "$BTP_TOKEN_URL" \
        -u "$BTP_DL_ID:$BTP_DL_SECRET" \
        -d "grant_type=client_credentials" | jq -r '.access_token' 2>/dev/null || true)
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        export SAP_BOOTSTRAP_TOKEN="$TOKEN"
        echo "Successfully acquired BTP bootstrap token."
    fi
fi

# Fallback default so mcp-toolbox config parser never fails on missing env var
export SAP_BOOTSTRAP_TOKEN="${SAP_BOOTSTRAP_TOKEN:-none}"

exec /toolbox "$@"
