#!/bin/bash

set -e

PROFILE="mcb7"
REGION="us-east-1"
ACCOUNT_ID="239460480281"
FUNCTION_NAME="CBFunction"
API_NAME="cb-dashboard-api"
STAGE_NAME="default"

echo "Creating HTTP API..."
API_ID=$(aws apigatewayv2 create-api \
  --profile $PROFILE \
  --region $REGION \
  --name $API_NAME \
  --protocol-type HTTP \
  --cors-configuration AllowOrigins="*",AllowMethods="GET,POST,OPTIONS",AllowHeaders="Content-Type,X-Api-Key,X-Community-Board" \
  --query 'ApiId' \
  --output text)
echo "API ID: $API_ID"

echo "Creating Lambda integration..."
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
  --profile $PROFILE \
  --region $REGION \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:lambda:$REGION:$ACCOUNT_ID:function:$FUNCTION_NAME \
  --payload-format-version 2.0 \
  --query 'IntegrationId' \
  --output text)
echo "Integration ID: $INTEGRATION_ID"

echo "Creating catch-all route..."
aws apigatewayv2 create-route \
  --profile $PROFILE \
  --region $REGION \
  --api-id $API_ID \
  --route-key '$default' \
  --target "integrations/$INTEGRATION_ID" > /dev/null

echo "Creating stage '$STAGE_NAME' with auto-deploy..."
aws apigatewayv2 create-stage \
  --profile $PROFILE \
  --region $REGION \
  --api-id $API_ID \
  --stage-name $STAGE_NAME \
  --auto-deploy > /dev/null

echo "Granting API Gateway permission to invoke Lambda..."
aws lambda add-permission \
  --profile $PROFILE \
  --region $REGION \
  --function-name $FUNCTION_NAME \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:$REGION:$ACCOUNT_ID:$API_ID/*" > /dev/null

echo ""
echo "Done! API base URL:"
echo "https://$API_ID.execute-api.$REGION.amazonaws.com/$STAGE_NAME"
