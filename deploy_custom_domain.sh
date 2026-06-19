#!/bin/bash
# Usage: ./deploy_custom_domain.sh
#   Sets up a custom domain for the API Gateway.
#   Requires the Route 53 hosted zone to be in the same AWS account.

set -e

PROFILE="qcb2"
REGION="us-east-1"
DOMAIN="internal.qcb2.example.com"
HOSTED_ZONE_DOMAIN="qcb2.example.com"
API_ID="7fklhw9ka7"
STAGE="default"

# Step 1: Request ACM certificate
echo "Requesting ACM certificate for $DOMAIN..."
CERT_ARN=$(aws acm request-certificate \
  --profile $PROFILE \
  --region $REGION \
  --domain-name $DOMAIN \
  --validation-method DNS \
  --query 'CertificateArn' \
  --output text)
echo "Certificate ARN: $CERT_ARN"

# Step 2: Wait for AWS to generate the validation record, then fetch it
echo "Fetching DNS validation record (may take a moment)..."
VALIDATION_NAME=""
VALIDATION_VALUE=""
for i in $(seq 1 12); do
  VALIDATION_NAME=$(aws acm describe-certificate \
    --profile $PROFILE \
    --region $REGION \
    --certificate-arn $CERT_ARN \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord.Name' \
    --output text 2>/dev/null || true)
  VALIDATION_VALUE=$(aws acm describe-certificate \
    --profile $PROFILE \
    --region $REGION \
    --certificate-arn $CERT_ARN \
    --query 'Certificate.DomainValidationOptions[0].ResourceRecord.Value' \
    --output text 2>/dev/null || true)
  if [ -n "$VALIDATION_NAME" ] && [ "$VALIDATION_NAME" != "None" ]; then
    break
  fi
  echo "  Not ready yet, retrying in 10s..."
  sleep 10
done

if [ -z "$VALIDATION_NAME" ] || [ "$VALIDATION_NAME" = "None" ]; then
  echo "ERROR: Could not retrieve certificate validation record. Try again in a minute."
  exit 1
fi
echo "Validation record: $VALIDATION_NAME -> $VALIDATION_VALUE"

# Step 3: Look up the hosted zone ID
echo "Looking up Route 53 hosted zone for $HOSTED_ZONE_DOMAIN..."
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --profile $PROFILE \
  --dns-name "${HOSTED_ZONE_DOMAIN}." \
  --query "HostedZones[?Name=='${HOSTED_ZONE_DOMAIN}.'].Id" \
  --output text | sed 's|/hostedzone/||')

if [ -z "$HOSTED_ZONE_ID" ]; then
  echo "ERROR: Could not find hosted zone for $HOSTED_ZONE_DOMAIN."
  exit 1
fi
echo "Hosted Zone ID: $HOSTED_ZONE_ID"

# Step 4: Add the validation CNAME to Route 53
echo "Adding DNS validation record to Route 53..."
aws route53 change-resource-record-sets \
  --profile $PROFILE \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"$VALIDATION_NAME\",
        \"Type\": \"CNAME\",
        \"TTL\": 300,
        \"ResourceRecords\": [{\"Value\": \"$VALIDATION_VALUE\"}]
      }
    }]
  }" > /dev/null

# Step 5: Wait for certificate to be validated (typically 1-5 minutes)
echo "Waiting for certificate validation (this usually takes 1-5 minutes)..."
aws acm wait certificate-validated \
  --profile $PROFILE \
  --region $REGION \
  --certificate-arn $CERT_ARN
echo "Certificate validated!"

# Step 6: Create the custom domain name in API Gateway
echo "Creating custom domain in API Gateway..."
APIGW_DOMAIN=$(aws apigatewayv2 create-domain-name \
  --profile $PROFILE \
  --region $REGION \
  --domain-name $DOMAIN \
  --domain-name-configurations CertificateArn=$CERT_ARN \
  --query 'DomainNameConfigurations[0].ApiGatewayDomainName' \
  --output text)

APIGW_HOSTED_ZONE_ID=$(aws apigatewayv2 get-domain-name \
  --profile $PROFILE \
  --region $REGION \
  --domain-name $DOMAIN \
  --query 'DomainNameConfigurations[0].HostedZoneId' \
  --output text)
echo "API Gateway domain: $APIGW_DOMAIN"

# Step 7: Create API mapping (empty key so /default/members paths pass through unchanged)
echo "Creating API mapping..."
aws apigatewayv2 create-api-mapping \
  --profile $PROFILE \
  --region $REGION \
  --domain-name $DOMAIN \
  --api-id $API_ID \
  --stage $STAGE > /dev/null

# Step 8: Create Route 53 ALIAS record pointing custom domain at API Gateway
echo "Creating Route 53 ALIAS record for $DOMAIN..."
aws route53 change-resource-record-sets \
  --profile $PROFILE \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"$DOMAIN\",
        \"Type\": \"A\",
        \"AliasTarget\": {
          \"HostedZoneId\": \"$APIGW_HOSTED_ZONE_ID\",
          \"DNSName\": \"$APIGW_DOMAIN\",
          \"EvaluateTargetHealth\": false
        }
      }
    }]
  }" > /dev/null

echo ""
echo "Done! Your API is now available at:"
echo "https://$DOMAIN/$STAGE/members"
echo "https://$DOMAIN/$STAGE/results"
echo "(all existing paths remain the same)"
