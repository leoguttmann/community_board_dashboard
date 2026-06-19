#!/bin/bash
# Usage: ./deploy_layer.sh
#   Builds a Lambda layer from app/requirements.txt, publishes it, and attaches it to CBFunction.
#   boto3 and pyngrok are excluded (boto3 is built into the Lambda runtime; pyngrok is local dev only).

set -e

PROFILE="qcb2"
REGION="us-east-1"
FUNCTION_NAME="CBFunction"
LAYER_NAME="cb-dashboard-dependencies"
BUILD_DIR="layer_build"
ZIP_FILE="layer.zip"

echo "Installing dependencies into $BUILD_DIR/python/..."
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR/python

grep -v -E '^(boto3|pyngrok)' app/requirements.txt > /tmp/layer-requirements.txt
pip3 install -r /tmp/layer-requirements.txt --target $BUILD_DIR/python --quiet

echo "Zipping layer..."
(cd $BUILD_DIR && zip -r ../$ZIP_FILE python) > /dev/null

echo "Publishing layer..."
LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
  --profile $PROFILE \
  --region $REGION \
  --layer-name $LAYER_NAME \
  --zip-file fileb://$ZIP_FILE \
  --compatible-runtimes python3.8 \
  --query 'LayerVersionArn' \
  --output text)
echo "Layer ARN: $LAYER_VERSION_ARN"

echo "Attaching layer to $FUNCTION_NAME..."
aws lambda update-function-configuration \
  --profile $PROFILE \
  --region $REGION \
  --function-name $FUNCTION_NAME \
  --layers $LAYER_VERSION_ARN > /dev/null

echo "Cleaning up..."
rm -rf $BUILD_DIR $ZIP_FILE

echo "Done!"
