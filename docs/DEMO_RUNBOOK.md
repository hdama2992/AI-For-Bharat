# Prototype Demo Runbook

This runbook is for the current 2-day prototype build of VikasGPT.

It is written for a live demo with judges, using:

- local frontend
- backend running in GitHub Codespaces
- Twilio WhatsApp Sandbox
- optional Sarvam voice
- optional Bedrock health generation

## Prototype Scope

The prototype scope for the demo is:

1. onboarding
2. dashboard
3. mandi advisor
4. health triage
5. WhatsApp health entrypoint

Pest is intentionally not part of the judge flow.

## Demo Goal

Show that the product can:

- create or load a rural household profile
- give a practical mandi decision
- triage a health case quickly
- continue the same health support flow over WhatsApp
- expose message delivery lifecycle using Twilio status callbacks

## Demo Architecture

### Frontend

Runs locally on:

```text
http://localhost:3000
```

### Backend

Runs in Codespaces and is exposed publicly on:

```text
https://<your-codespace-name>-8000.app.github.dev
```

### WhatsApp

Twilio Sandbox sends incoming messages to:

```text
https://<your-public-base-url>/api/v1/whatsapp/webhook
```

Twilio delivery/read status callbacks go to:

```text
https://<your-public-base-url>/api/v1/whatsapp/status-callback
```

### Media Hosting

Voice replies, when available, are temporarily hosted at:

```text
https://<your-public-base-url>/api/v1/whatsapp/media/{media_id}
```

## Pre-Demo Checklist

### Backend

- backend virtualenv created
- dependencies installed
- `.env` filled
- `PUBLIC_BASE_URL` set to the current Codespaces public URL
- backend starts successfully

Start command:

```bash
cd backend
source .venv/bin/activate
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

- frontend dependencies installed
- `.env.local` configured
- frontend starts successfully

Start command:

```bash
cd frontend
npm install
npm run dev
```

### Codespaces

- port `8000` is public
- public URL returns `200` for `/health`

Test:

```bash
curl https://<your-public-base-url>/health
curl https://<your-public-base-url>/api/v1
```

### Twilio

- sandbox joined from your phone
- incoming webhook configured
- phone has network access
- phone is ready with one saved text and one short voice note

### Optional AI/Voice Integrations

If enabled:

- Sarvam credentials configured
- Bedrock credentials configured

If not enabled:

- fallback logic still works
- text-based WhatsApp demo still succeeds

## Suggested Judge Demo Flow

Target total time: 3 to 4 minutes.

### Scene 1: Household setup

Open the landing page and show:

- user can start from onboarding
- demo household shortcut exists

Preferred flow:

- use the demo shortcut if time is tight
- use onboarding only if you want to show personalization

### Scene 2: Dashboard

Show:

- household profile context
- mandi module
- health module
- WhatsApp CTA

Talk track:

- the system knows the user is a rural household
- services are personalized by context

### Scene 3: Mandi advisor

Open Mandi Advisor and select:

- crop
- district

Show:

- local mandi
- alternative mandis
- recommendation
- savings message

Talk track:

- the prototype makes a practical sell decision after accounting for transport cost

### Scene 4: Health triage on web

Open Health and enter a strong demo case.

Recommended RED case:

```text
My 8 year old daughter has 103 F fever and vomiting since morning
```

Expected result:

- clear triage card
- emergency guidance
- confidence and follow-up guidance

Talk track:

- the product can escalate quickly for high-risk rural health scenarios

### Scene 5: WhatsApp continuity

Switch to your phone and send:

```text
My child has fever and vomiting
```

Then show:

- WhatsApp reply arrives
- status callback events are recorded

Open:

```text
https://<your-public-base-url>/api/v1/whatsapp/status-callback/recent
```

Talk track:

- the assistant is available on WhatsApp, not just the web app
- delivery lifecycle is visible for operational tracking

### Scene 6: Voice note on WhatsApp

Send a short voice note from your phone.

Expected result:

- if Sarvam is configured: voice note is processed and a voice or text reply is returned
- if Sarvam is not configured: fallback prompt asks the user to retry or type

Talk track:

- even with partial integrations, the user still gets a safe fallback response

## Recommended Demo Inputs

### GREEN case

```text
I have mild headache since today
```

### YELLOW case

```text
My mother has fever and vomiting for 3 days
```

### RED case

```text
My 8 year old daughter has 103 F fever and vomiting since morning
```

## What To Show If Something Fails

### If Sarvam voice fails

Show:

- WhatsApp text still works
- web health triage still works
- fallback message for voice still guides the user

### If Bedrock is unavailable

Show:

- triage still works through local fallback logic
- the system remains safe and deterministic

### If Twilio status events do not appear immediately

Show:

- direct status callback test with curl
- `/status-callback/recent` records the event

Command:

```bash
curl -X POST https://<your-public-base-url>/api/v1/whatsapp/status-callback \
  -d "MessageSid=SM123456789" \
  -d "MessageStatus=delivered" \
  -d "To=whatsapp:+14155238886" \
  -d "From=whatsapp:+919999999999"
```

## Live Validation Checklist

Run these before the demo begins.

### Backend health

```bash
curl https://<your-public-base-url>/health
curl https://<your-public-base-url>/api/v1
```

### WhatsApp webhook

```bash
curl -X POST https://<your-public-base-url>/api/v1/whatsapp/webhook \
  -d "From=whatsapp:+919999999999" \
  -d "Body=My child has fever and vomiting"
```

### Status callback

```bash
curl -X POST https://<your-public-base-url>/api/v1/whatsapp/status-callback \
  -d "MessageSid=SM123456789" \
  -d "MessageStatus=delivered"
```

### Recent status events

```bash
curl https://<your-public-base-url>/api/v1/whatsapp/status-callback/recent
```

## Day-of-Demo Operational Checklist

- keep backend terminal open
- keep frontend terminal open
- keep Codespaces tab open
- keep Twilio Sandbox page ready
- keep your phone joined to the sandbox
- keep one RED-case text copied
- keep one short voice note prepared
- do not restart Codespaces right before the demo
- do not change port visibility right before the demo

## Known Limitations

- WhatsApp status history is stored in memory only
- restarting the backend clears status history
- voice-note quality depends on Sarvam being configured and responding
- Twilio Sandbox is not a production WhatsApp number
- current demo scope does not include Pest in the surfaced flow

## Recommended Next Steps After Demo

1. move WhatsApp session/status storage from memory to persistent storage
2. add Twilio signature validation for webhook security
3. add a small UI page to monitor status callbacks
4. persist household and health session state in DynamoDB or Postgres
5. move from Twilio Sandbox to approved WhatsApp Business configuration

## Relevant Files

- [docs/WHATSAPP_CODESPACES_SETUP.md](/Users/hdama/Documents/GitHub/AI-For-Bharat/docs/WHATSAPP_CODESPACES_SETUP.md)
- [backend/app/routers/whatsapp.py](/Users/hdama/Documents/GitHub/AI-For-Bharat/backend/app/routers/whatsapp.py)
- [backend/app/services/health_advisor.py](/Users/hdama/Documents/GitHub/AI-For-Bharat/backend/app/services/health_advisor.py)
- [frontend/app/dashboard/page.tsx](/Users/hdama/Documents/GitHub/AI-For-Bharat/frontend/app/dashboard/page.tsx)
- [frontend/app/health/page.tsx](/Users/hdama/Documents/GitHub/AI-For-Bharat/frontend/app/health/page.tsx)
- [frontend/app/mandi/page.tsx](/Users/hdama/Documents/GitHub/AI-For-Bharat/frontend/app/mandi/page.tsx)
