#!/bin/bash

TWILIO_API_KEY="${TWILIO_API_KEY:?Set TWILIO_API_KEY env var before running}"
URL="https://7fklhw9ka7.execute-api.us-east-1.amazonaws.com/default/incomingtext?auth=${TWILIO_API_KEY}&cb=2"

NUMBERS_FILE="${1:-test_numbers.txt}"

if [[ ! -f "$NUMBERS_FILE" ]]; then
  echo "Error: numbers file '$NUMBERS_FILE' not found."
  echo "Create it with one phone number per line (e.g. +12125551234)"
  exit 1
fi

NUMBERS=()
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -n "$line" ]] && NUMBERS+=("$line")
done < "$NUMBERS_FILE"

VOTES=("yes" "yes" "yes" "no" "yes" "abstain" "yes" "no" "yes" "yes" "yes" "cause" "yes" "no" "yes" "yes" "abstain" "yes" "no" "yes")

echo "Sending ${#NUMBERS[@]} votes concurrently..."

for i in "${!NUMBERS[@]}"; do
  NUMBER="${NUMBERS[$i]}"
  VOTE="${VOTES[$((i % ${#VOTES[@]}))]}"

  # Twilio webhook body: URL-encoded, then base64-encoded (as API Gateway delivers it to Lambda)
  ENCODED_NUMBER=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${NUMBER}'))")
  FORM_BODY="Body=${VOTE}&From=${ENCODED_NUMBER}"
  B64_BODY=$(echo -n "$FORM_BODY" | base64)

  curl -s -o /dev/null -w "${NUMBER} (${VOTE}): %{http_code}\n" \
    -X POST "$URL" \
    --data-raw "$B64_BODY" &
done

wait
echo "Done."
