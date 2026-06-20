# Community Board Dashboard

## Run locally

```bash
export FLASK_APP=flask_app.py
export API_KEY=<your-api-key>
cd app
flask run --reload
```

Then open http://127.0.0.1:5000/webresults

---

## AWS Infrastructure

### Overview

- **Lambda**: `CBFunction` — Python 3.12, handles all API routes
- **Lambda layer**: `cb-dashboard-dependencies` — third-party packages (twilio, flask, etc.)
- **API Gateway**: HTTP API (v2), catch-all `$default` route → Lambda, stage named `default`
- **API Gateway URL**: `https://7fklhw9ka7.execute-api.us-east-1.amazonaws.com/default`
- **Custom domain** (not yet configured): `deploy_custom_domain.sh` sets up a custom domain with ACM cert and Route 53 DNS

### Lambda environment variables

| Variable | Description |
|---|---|
| `API_KEY` | Shared secret checked via `x-api-key` header on all authenticated endpoints |
| `TWILIO_API_KEY` | Shared secret embedded in the Twilio webhook URL (`auth=` param) |

### Deployment scripts

| Script | Purpose |
|---|---|
| `./deploy_lambda.sh` | Update Lambda function code (default) |
| `./deploy_lambda.sh --new` | Create Lambda function for the first time |
| `./deploy_layer.sh` | Build and publish the dependency layer, attach it to CBFunction |
| `./deploy_api_gateway.sh` | Create the HTTP API Gateway (first-time setup) |
| `./deploy_custom_domain.sh` | Request ACM cert, create custom domain, wire up Route 53 (first-time setup) |

### First-time setup order

1. `./deploy_lambda.sh --new`
2. `./deploy_layer.sh`
3. `./deploy_api_gateway.sh`
4. `./deploy_custom_domain.sh`
5. Set environment variables on the Lambda:
   ```bash
   aws lambda update-function-configuration \
     --profile qcb2 \
     --region us-east-1 \
     --function-name CBFunction \
     --environment "Variables={API_KEY=<value>,TWILIO_API_KEY=<value>}"
   ```
6. Retrieve environment variables (e.g., to get the dashboard password):
   ```bash
   aws lambda get-function-configuration \
     --profile qcb2 \
     --region us-east-1 \
     --function-name CBFunction \
     --query 'Environment.Variables'
   ```

---

## API endpoints

All endpoints are available at `https://7fklhw9ka7.execute-api.us-east-1.amazonaws.com/default/`.

Authenticated endpoints require headers:
- `x-api-key: <API_KEY>`
- `x-community-board: <board_number>`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | No | Serve the dashboard HTML page |
| GET | `/members` | Yes | Get member list |
| POST | `/members` | Yes | Set member list |
| POST | `/startvoting` | Yes | Start a vote |
| POST | `/stopvoting` | Yes | Stop a vote |
| GET | `/results` | Yes | Get current vote results |
| GET | `/isvotingstarted` | Yes | Check if voting is active |
| POST | `/exportvotes` | Yes | Export votes for a date |
| POST | `/manualentry` | Yes | Manually submit a vote |
| POST | `/incomingtext` | URL param | Twilio SMS webhook |

---

## Twilio

Webhook URL to configure in the Twilio console:

```
https://7fklhw9ka7.execute-api.us-east-1.amazonaws.com/default/incomingtext?auth=<TWILIO_API_KEY>&cb=<community_board_number>
```

The `auth` param must match the `TWILIO_API_KEY` environment variable on the Lambda.

---

## Upload members

```bash
python3 uploadmembers.py
```

---

## Testing concurrent votes

`test_concurrent_votes.sh` sends votes from multiple phone numbers simultaneously to exercise the `/incomingtext` endpoint under load.

Phone numbers are read from a local `test_numbers.txt` file (one number per line) that is gitignored to keep member data out of the repo.

```
+12125551234
+12125555678
...
```

Run the test:

```bash
./test_concurrent_votes.sh
```

Or pass a custom numbers file:

```bash
./test_concurrent_votes.sh path/to/other_numbers.txt
```

---

## Before going to production

- **Upgrade Twilio to a paid account** — the free trial only allows SMS to/from verified numbers
- **Increase Lambda concurrency** — new AWS accounts default to 10 concurrent executions, which will throttle votes when 50+ members text at once. Request an increase to 100 via AWS Console → Service Quotas → AWS Lambda → Concurrent executions
- **Set up a custom domain** — update `DOMAIN` and `HOSTED_ZONE_DOMAIN` in `deploy_custom_domain.sh`, then run it
- **Upload the full member list** — via the Edit Members button in the dashboard
