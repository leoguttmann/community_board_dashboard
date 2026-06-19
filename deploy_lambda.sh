#!/bin/bash
# Usage: ./deploy_lambda.sh [--new]
#   Default: updates the existing Lambda function code.
#   --new: creates the Lambda function for the first time.

set -e

FUNCTION_NAME="CBFunction"
ZIP_FILE_PATH="cbpackage.zip"
HANDLER="lambda_app.lambda_handler"
NEW=false

for arg in "$@"; do
  case $arg in
    --new) NEW=true ;;
  esac
done

(cd ./app && zip -r $ZIP_FILE_PATH ./*)

if [ "$NEW" = true ]; then
  echo "Creating new Lambda function..."
  aws lambda create-function \
    --profile qcb2 \
    --region us-east-1 \
    --function-name $FUNCTION_NAME \
    --runtime python3.8 \
    --role arn:aws:iam::487037338725:role/qcb2-dashboard-lambda-role \
    --handler $HANDLER \
    --zip-file fileb://app/$ZIP_FILE_PATH
else
  echo "Updating Lambda function code..."
  aws lambda update-function-code \
    --profile qcb2 \
    --region us-east-1 \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://app/$ZIP_FILE_PATH
fi

rm ./app/$ZIP_FILE_PATH
