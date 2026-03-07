# WhatsApp Setup on GitHub Codespaces

This document describes the current prototype setup for running the VikasGPT backend from GitHub Codespaces and connecting it to the Twilio WhatsApp Sandbox.

It reflects the code that is currently implemented in the repository, not the original broader plan.

## What Is Already Implemented

The backend currently supports these WhatsApp-related endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/whatsapp/webhook` | Incoming Twilio WhatsApp webhook |
| `POST` | `/api/v1/whatsapp/status-callback` | Twilio delivery/read status callback |
| `GET` | `/api/v1/whatsapp/status-callback/recent` | Inspect recent status events |
| `GET` | `/api/v1/whatsapp/media/{media_id}` | Temporary hosted media for voice replies |

The current WhatsApp behavior is:

1. Twilio sends an incoming text or voice note to `/api/v1/whatsapp/webhook`.
2. If the message is a voice note, the backend tries to transcribe it using Bhashini.
3. The backend generates a health response using the shared health advisor service.
4. If TTS is available, the backend generates a temporary hosted audio reply.
5. If TTS is not available, the backend falls back to a text reply.
6. Twilio lifecycle events are sent to `/api/v1/whatsapp/status-callback`.

## Deployment Model

For this prototype, the backend runs inside GitHub Codespaces and is exposed using a **public forwarded port**.

Twilio cannot call:

- `localhost`
- a private Codespaces port
- a Codespaces URL that redirects to `github.dev/pf-signin`

Twilio can only call a **publicly reachable HTTPS URL**.

## Required Environment Variables

Create `backend/.env` from `backend/.env.example`.

Minimum required for WhatsApp Sandbox:

```env
PUBLIC_BASE_URL=https://<your-codespace-name>-8000.app.github.dev
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Optional for real voice transcription and voice reply:

```env
BHASHINI_USER_ID=...
BHASHINI_API_KEY=...
```

Optional for Bedrock-backed health generation instead of fallback-only logic:

```env
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
```

## Running the Backend in Codespaces

From the repo root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Important:

- use `--host 0.0.0.0`
- keep the process running while testing Twilio
- restart the backend any time you change `PUBLIC_BASE_URL`

## Making Port 8000 Public in Codespaces

1. Open the `Ports` tab in Codespaces.
2. Find port `8000`.
3. Set its visibility to `Public`.
4. Copy the public HTTPS URL.

Example:

```text
https://effective-couscous-7vq4qpj5q4x4cjr-8000.app.github.dev
```

Set `PUBLIC_BASE_URL` to that exact value.

## Verifying the Public Backend URL

Before configuring Twilio, verify the backend is reachable without authentication.

Run:

```bash
curl https://<your-public-base-url>/health
curl https://<your-public-base-url>/api/v1
```

Expected result:

- `200 OK`
- JSON response
- no redirect to `github.dev/pf-signin`

If you see a `302` redirect to `github.dev/pf-signin`, the port is still not public.

## Twilio WhatsApp Sandbox Configuration

Open the Twilio Console WhatsApp Sandbox page.

The incoming message webhook must be:

```text
https://<your-public-base-url>/api/v1/whatsapp/webhook
```

Method:

```text
POST
```

For this implementation, the status callback URL is already attached to outgoing replies from the backend. It points to:

```text
https://<your-public-base-url>/api/v1/whatsapp/status-callback
```

The backend adds this URL to the generated TwiML reply so Twilio can report lifecycle events such as:

- `queued`
- `sending`
- `sent`
- `delivered`
- `undelivered`
- WhatsApp read-related channel events when available

## Joining the Twilio Sandbox

From your phone, send the sandbox join command shown in Twilio Console to:

```text
+1 415 523 8886
```

Example:

```text
join example-sandbox-code
```

Only numbers that have joined the sandbox can participate in the demo.

## Testing the Endpoints

### 1. Test the incoming WhatsApp webhook directly

```bash
curl -X POST https://<your-public-base-url>/api/v1/whatsapp/webhook \
  -d "From=whatsapp:+919999999999" \
  -d "Body=My 8 year old daughter has 103 F fever and vomiting since morning"
```

Expected result:

- XML response
- contains `<Response>` and `<Message>`

### 2. Test the status callback directly

```bash
curl -X POST https://<your-public-base-url>/api/v1/whatsapp/status-callback \
  -d "MessageSid=SM123456789" \
  -d "MessageStatus=delivered" \
  -d "To=whatsapp:+14155238886" \
  -d "From=whatsapp:+919999999999"
```

Expected result:

```json
{"received":true,"message_sid":"SM123456789","status":"delivered"}
```

### 3. Inspect recorded status events

```bash
curl https://<your-public-base-url>/api/v1/whatsapp/status-callback/recent
```

Expected result:

- JSON with a list of recent callback events

## End-to-End WhatsApp Test Sequence

Once Twilio is configured:

1. send a WhatsApp text message first
2. verify the bot replies
3. check `/api/v1/whatsapp/status-callback/recent`
4. then send a short voice note
5. if Bhashini is configured, verify voice or text reply
6. check `/api/v1/whatsapp/status-callback/recent` again

Recommended first text:

```text
My child has fever and vomiting
```

Recommended RED-case demo text:

```text
My 8 year old daughter has 103 F fever and vomiting since morning
```

## Current Fallback Behavior

The prototype is intentionally resilient to missing external services.

### If Bedrock is unavailable

The backend uses the local fallback triage engine implemented in:

`backend/app/services/health_advisor.py`

This still returns structured triage levels:

- `GREEN`
- `YELLOW`
- `RED`

### If Bhashini is unavailable

Text messages still work.

Voice-note behavior becomes:

- transcription fails
- user receives a retry/text-fallback prompt

### If TTS fails

The WhatsApp reply is sent as text only.

## Troubleshooting

### Problem: Twilio cannot hit the webhook

Check:

- `PUBLIC_BASE_URL` is correct
- Codespaces port `8000` is public
- backend is running on `0.0.0.0:8000`
- webhook path is `/api/v1/whatsapp/webhook`

### Problem: backend URL redirects to login

Cause:

- Codespaces port is not public

Fix:

- change port `8000` visibility to `Public`

### Problem: voice notes do not work

Check:

- `BHASHINI_USER_ID`
- `BHASHINI_API_KEY`
- Twilio media download credentials
- whether the incoming message is actually `audio/*`

### Problem: no status events appear

Check:

- Twilio is successfully sending replies
- backend response includes TwiML `<Message ... statusCallback="...">`
- `PUBLIC_BASE_URL` matches the currently active public Codespaces URL

## Files Relevant to This Setup

- [backend/app/routers/whatsapp.py](/Users/hdama/Documents/GitHub/AI-For-Bharat/backend/app/routers/whatsapp.py)
- [backend/app/db/memory.py](/Users/hdama/Documents/GitHub/AI-For-Bharat/backend/app/db/memory.py)
- [backend/app/services/health_advisor.py](/Users/hdama/Documents/GitHub/AI-For-Bharat/backend/app/services/health_advisor.py)
- [backend/app/services/onboarding.py](/Users/hdama/Documents/GitHub/AI-For-Bharat/backend/app/services/onboarding.py)
- [backend/.env.example](/Users/hdama/Documents/GitHub/AI-For-Bharat/backend/.env.example)

## Next Steps

1. finalize `backend/.env` with real Twilio values
2. keep the Codespaces public URL stable through the demo
3. test text message flow first
4. test status callback flow second
5. test voice-note flow third
6. add Bhashini credentials if you want real voice transcription and voice replies
7. optionally add Bedrock credentials if you want live LLM responses instead of fallback-only behavior
