#!/bin/bash
# ==============================================================================
# Isolated Deployment Script for MCP Toolbox v2
# This script ensures that building and deploying this version has ZERO impact
# on the primary running "mcp-toolbox" Cloud Run service.
# ==============================================================================
set -e

PROJECT_ID="${PROJECT_ID:-smart-closer-agt-sap-slf-1850}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-mcp-toolbox-v2}"
IMAGE_TAG="us-central1-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/mcp-toolbox:v2"
SECRET_NAME="${SECRET_NAME:-tools_config_mcp_odata_v2}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-bpa-toolbox-identity@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "=== 1. Checking Secret Manager for Isolated Config (${SECRET_NAME}) ==="
if ! gcloud secrets describe "${SECRET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "Creating dedicated secret ${SECRET_NAME}..."
    gcloud secrets create "${SECRET_NAME}" \
        --project="${PROJECT_ID}" \
        --replication-policy="automatic" \
        --data-file="tools.yaml"
else
    echo "Secret ${SECRET_NAME} already exists. Updating version..."
    gcloud secrets versions add "${SECRET_NAME}" \
        --project="${PROJECT_ID}" \
        --data-file="tools.yaml"
fi

echo "=== 2. Building Isolated Container Image (${IMAGE_TAG}) ==="
gcloud builds submit \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_TAG}"

echo "=== 3. Deploying Isolated Cloud Run Service (${SERVICE_NAME}) ==="
gcloud run deploy "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_TAG}" \
    --service-account="${SERVICE_ACCOUNT}" \
    --set-secrets="/app/tools.yaml=${SECRET_NAME}:latest" \
    --args="--tools-file=/app/tools.yaml","--address=0.0.0.0","--port=8080" \
    --no-allow-unauthenticated

echo "=== Deployment Complete ==="
gcloud run services describe "${SERVICE_NAME}" --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)"
