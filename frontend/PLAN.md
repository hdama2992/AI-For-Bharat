# Asha-GPT: 3-Day Sprint Implementation Plan

**Deadline: March 4, 2026 | Today: March 1, 2026 | Remaining: ~72 hours**

---

## Scope: Cut to Win

With 72 hours, ruthless scope cuts are mandatory. Goal: one polished, demo-ready product.

**Keep (non-negotiable):**
1. Mandi Price Advisor (mock data, compelling UI)
2. Pest-Vision (image upload → Claude multimodal analysis)
3. Health Triage (symptom chat → Green/Yellow/Red card)
4. Household Context (cross-module insight panel — the WOW moment)

**Cut:**
- WhatsApp integration (replaced by web chat UI)
- Bhashini voice ASR/TTS (replaced by browser Web Speech API)
- ABHA integration, Scheme Matcher, Weather module
- Real eNAM API (use rich mock data)
- AWS KMS dual-vault (use SQLite with logical separation)
- Lambda/serverless (use single FastAPI server on EC2)

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 + Tailwind CSS | PWA-capable, mobile-first, fast |
| Backend | Python 3.11 + FastAPI | Team preference, async-friendly |
| AI | Amazon Bedrock (Claude 3.5 Sonnet) | Matches proposal, uses AWS credits |
| Database | SQLite (local) → DynamoDB (AWS) | Single config flag to switch |
| Deployment | Vercel (frontend) + EC2 t3.micro (backend) | Fast setup, live URL |

---

## Project Folder Structure

```
asha-gpt/
├── README.md
├── .gitignore
│
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── core/
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── database.py            # SQLite init + DynamoDB adapter
│   │   └── bedrock_client.py      # Boto3 Bedrock runtime wrapper
│   │
│   ├── models/
│   │   ├── household.py           # HouseholdProfile pydantic model
│   │   ├── health.py              # TriageResult, SymptomLog models
│   │   └── krishi.py              # MandiPrice, PestAnalysis models
│   │
│   ├── routers/
│   │   ├── household.py           # POST/GET /household
│   │   ├── mandi.py               # GET /mandi/prices, /mandi/compare
│   │   ├── pest.py                # POST /pest/analyze (multipart image)
│   │   └── health.py              # POST /health/triage, /health/chat
│   │
│   ├── services/
│   │   ├── household_context.py   # Cross-domain context builder ← KEY FILE
│   │   ├── mandi_service.py       # Mock data loader + price comparison
│   │   ├── pest_service.py        # Image → base64 → Bedrock multimodal
│   │   └── health_service.py      # Symptom → Bedrock triage chain
│   │
│   ├── prompts/
│   │   ├── pest_system.txt        # Pest-Vision system prompt
│   │   ├── health_system.txt      # Health Triage system prompt
│   │   └── context_system.txt     # Household context synthesis prompt
│   │
│   └── data/
│       ├── mandi_mock.json        # Rich mock Mandi price dataset
│       └── crops.json             # Crop reference data
│
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── .env.local
    │
    ├── public/
    │   ├── manifest.json          # PWA manifest
    │   └── favicon.ico
    │
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx           # Landing/onboarding
        │   ├── setup/page.tsx     # Household profile wizard
        │   ├── dashboard/page.tsx # Main hub (3 module cards)
        │   ├── mandi/page.tsx     # Price comparison
        │   ├── pest/page.tsx      # Photo upload + result
        │   └── health/page.tsx    # Chat-based triage
        │
        ├── components/
        │   ├── ui/
        │   │   ├── ChatBubble.tsx
        │   │   ├── VoiceButton.tsx
        │   │   ├── TriageCard.tsx
        │   │   ├── MandiTable.tsx
        │   │   ├── PestResultCard.tsx
        │   │   └── HouseholdContextBanner.tsx  ← KEY COMPONENT
        │   └── layout/
        │       ├── Header.tsx
        │       └── BottomNav.tsx
        │
        ├── hooks/
        │   ├── useVoice.ts
        │   ├── useHousehold.ts
        │   └── useChat.ts
        │
        └── lib/
            ├── api.ts
            └── i18n.ts            # Hindi/English string map
```

---

## Day-by-Day Schedule

### Day 1 — March 1 (Today): Foundation + Mandi + Pest-Vision

**Hours 1-4: Backend foundation**
- Initialize backend: `uv init` or `python -m venv`
- `core/bedrock_client.py` — boto3 wrapper for standard + streaming invokes + base64 images
- `core/database.py` — SQLite with 3 logical tables: `households`, `krishi_activity`, `health_activity`
- Pydantic models for all entities
- `data/mandi_mock.json` — 5 districts × 5 mandis × 5 crops with realistic prices
- Verify Bedrock access: test invoke with Claude 3.5 Sonnet

**Hours 5-8: Mandi + Pest-Vision backend**
- `POST /household` and `GET /household/{id}`
- `GET /mandi/prices` and `GET /mandi/compare`
- `POST /pest/analyze` (multipart image → base64 → Bedrock multimodal)
- Write Pest-Vision system prompt (see prompts section below)
- Test Pest-Vision with a real leaf photo

**Hours 9-12: Frontend foundation + Mandi + Pest pages**
- `npx create-next-app@14 frontend --typescript --tailwind`
- Color palette, layout components (Header, BottomNav, ModuleCard)
- Landing page + Household Setup wizard (3 steps)
- `/mandi` page with MandiTable + savings callout
- `/pest` page with image upload + PestResultCard
- Wire both to backend, test full flow

**Target by end of Day 1:** Pest-Vision and Mandi working end-to-end

---

### Day 2 — March 2: Health Triage + Household Context + Voice

**Hours 1-4: Health Triage backend**
- `POST /health/chat` with streaming (SSE) response
- `POST /health/triage` for final triage output
- Write Health Triage system prompt (see below)
- Test symptom conversation → Green/Yellow/Red output

**Hours 5-8: Health frontend + Household Context**
- `/health` page — WhatsApp-style streaming chat interface
- `TriageCard` component (Green/Yellow/Red with animation)
- `VoiceButton` — Web Speech API, `lang="hi-IN"` or `"en-IN"`
- `household_context.py` service:
  - Rule 1: Pest treatment + pregnant member → flag safer pesticide
  - Rule 2: Red/Yellow triage + upcoming Mandi trip → flag rest first
  - Bedrock synthesis for complex multi-factor cases
- `GET /household/context/{id}` endpoint
- `HouseholdContextBanner` component on Dashboard

**Hours 9-12: Integration + polish**
- Full household journey test (setup → mandi → pest → health → context banner)
- Mobile responsiveness pass on all pages
- Loading states, error states, empty states
- Hindi/English toggle for key strings

**Target by end of Day 2:** All 3 modules + household context working end-to-end

---

### Day 3 — March 3: Polish + Demo Data + Deployment

**Hours 1-4: Demo preparation**
- Pre-seed demo household "Rajesh Kumar" (Harda MP, soybean farmer, wife Priya 28wk pregnant)
- Verify WOW moment flow works:
  1. Upload soybean leaf with Fall Armyworm damage
  2. Bedrock identifies pest + recommends pesticide
  3. Context banner fires: "Priya (28wk pregnant) — use Neem-based Azadirachtin instead. Available at Ramu Agri Store, 2.3km."
- Final UI polish: animations, loading skeletons

**Hours 5-8: AWS deployment**
- Launch EC2 t3.micro, attach IAM Role (Bedrock + DynamoDB access)
- Deploy FastAPI with uvicorn (or Elastic Beanstalk for speed)
- Create 3 DynamoDB tables
- Switch `DATABASE_BACKEND=dynamodb` env var
- Push frontend to GitHub → connect to Vercel → set `NEXT_PUBLIC_API_URL`
- Test live URL from real mobile phone

**Hours 9-12: Submission**
- Record 2-3 min demo video (screen recording on phone browser)
- Update README with live URL, architecture diagram, video link
- Submit GitHub repo + live URL + video

---

## API Endpoints

### Base URL: `http://localhost:8000/api/v1`

```
# Household
POST   /household                          Create household profile
GET    /household/{id}                     Get profile
GET    /household/context/{id}             Get active cross-domain insights

# Mandi
GET    /mandi/prices?crop=&district=       Get prices for crop/district
GET    /mandi/compare?crop=&district=      Get best mandi recommendation
GET    /mandi/crops                        List available crops

# Pest-Vision
POST   /pest/analyze                       Upload image → pest analysis

# Health
POST   /health/chat                        Streaming symptom chat (SSE)
POST   /health/triage                      Get final triage result

# Utility
GET    /health                             API health check
```

---

## Key Bedrock Prompts

### Pest-Vision System Prompt
```
You are Asha-GPT's Pest-Vision module — expert agricultural pathologist
trained on ICAR databases, specialized in Indian crop diseases and pests.

RULES:
1. Only recommend pesticides registered under India's CIB&RC.
2. NEVER recommend banned pesticides (Endosulfan, Monocrotophos).
3. Always provide a neem-based/organic alternative.
4. Dosage in Indian units: ml per 15L pump, or grams per acre.
5. If household has pregnant members, flag organophosphates as UNSAFE
   and prioritize neem/biological alternative.

OUTPUT: JSON only (no markdown):
{
  "disease_identified": "string",
  "confidence_pct": number,
  "severity": "Low|Medium|High",
  "primary_cause": "Pest|Fungal|Bacterial|Viral|Nutritional",
  "treatment": {
    "recommended_pesticide": "string",
    "active_ingredient": "string",
    "dosage": "string",
    "cost_estimate_inr": number
  },
  "household_safety_alert": "string or null",
  "alternative_treatment": { "name": "string", "dosage": "string" },
  "prevention_tips": ["string"]
}
```
Config: Claude 3.5 Sonnet, temperature=0.1, max_tokens=1024

---

### Health Triage System Prompt
```
You are Asha-GPT's health advisor following eSanjeevani clinical triage
guidelines and ICMR protocols for rural primary healthcare.

STRICT SAFETY RULES — NEVER VIOLATE:
1. NEVER prescribe specific medications or dosages.
2. NEVER diagnose a specific disease — triage only.
3. ALWAYS recommend calling 108 for: chest pain, breathing difficulty,
   loss of consciousness, stroke symptoms, severe bleeding.
4. If uncertain, escalate to YELLOW, never downgrade to GREEN.
5. Include disclaimer in every triage result.

TRIAGE LEVELS:
- GREEN: Manage at home. Follow up if no improvement in 3 days.
- YELLOW: Visit PHC within 24 hours.
- RED: EMERGENCY — Call 108 immediately.

STYLE: Speak like an ASHA worker — empathetic, simple language.
Ask one clarifying question at a time. After 3-5 messages, triage.

When ready, output:
<TRIAGE>
{
  "triage_level": "GREEN|YELLOW|RED",
  "confidence_pct": number,
  "assessment_summary": "string",
  "immediate_actions": ["string"],
  "emergency_number": "108 or null",
  "disclaimer": "This is not a medical diagnosis. Please consult a doctor."
}
</TRIAGE>
```
Config: Claude 3.5 Sonnet, temperature=0.2, max_tokens=2048, streaming=true

---

## Mandi Mock Data Strategy

Since eNAM API requires registration, use a rich realistic mock:
- 5 districts: Harda (MP), Bhopal (MP), Jaipur (Rajasthan), Lucknow (UP), Nagpur (Maharashtra)
- 3 mandis per district (local + 2 regional)
- 5 crops: Soybean, Wheat, Mustard, Cotton, Maize
- Realistic price variance: local ≈ MSP, regional mandis 3-8% above MSP
- Transport cost formula: `distance_km × 1.15` rupees per quintal
- `mandi_service.py` adds ±2% random noise at request time so prices "move"
- `last_updated` always shows "2 hours ago" for demo freshness

---

## Household Context: The WOW Moment

### Rule-based insights (fast, reliable):
```python
# Rule 1: Pest treatment + pregnant family member
if last_pest_analysis and is_organophosphate(pesticide) and has_pregnant_member:
    → "⚠️ Priya (28wk pregnant) — use Neem-based spray instead.
         Available at Ramu Agri Store, 2.3km."

# Rule 2: Red/Yellow triage + Mandi check within 72 hours
if recent_triage in ["RED","YELLOW"] and recent_mandi_query:
    → "Rest before traveling to Mandi. Your health comes first."

# Rule 3: Bedrock synthesis for complex multi-factor cases
```

### Data separation (logical vaults):
- `krishi_activity` table: farm, pest, mandi data
- `health_activity` table: triage, symptoms, health history
- Shared only: `household_id`, `district`, `family_members`
- Switch flag: `DATABASE_BACKEND=sqlite` locally, `=dynamodb` on AWS

---

## Deployment Architecture

```
[Mobile Browser]
     │ HTTPS
     ▼
[Vercel] ── Next.js frontend ── asha-gpt.vercel.app
     │ HTTPS REST
     ▼
[EC2 t3.micro] ── FastAPI + uvicorn
     │ boto3 SDK
     ▼
[Amazon Bedrock] ── Claude 3.5 Sonnet (us-east-1)
[DynamoDB] ── 3 tables (households, krishi_activity, health_activity)
```

**EC2 IAM Role policies needed:**
- `AmazonBedrockFullAccess`
- `AmazonDynamoDBFullAccess`

---

## Priority Order (If Falling Behind)

| Priority | Feature | Cut trigger |
|---|---|---|
| 🔴 Never cut | Pest-Vision end-to-end | Never |
| 🔴 Never cut | Health Triage chat + card | Never |
| 🟡 Keep | Mandi price comparison | Cut chart, keep table |
| 🟡 Keep | Household Context banner | Keep rule-based, cut Bedrock synthesis |
| 🟢 Cut if needed | Voice input | Show as "coming soon" |
| 🟢 Cut if needed | Hindi/English toggle | English only |
| ⚪ Skip | History pages | Never build |
| ⚪ Skip | Full DynamoDB migration | Keep SQLite for demo |

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Bedrock model not enabled | Day 1 morning: enable Claude 3.5 Sonnet + Claude 3 Haiku (fallback) in AWS Console → Bedrock → Model Access |
| Bedrock latency >10s for images | Resize image to max 512px before sending. Show "Asha is thinking..." loader |
| CORS issues | Add `CORSMiddleware(allow_origins=["*"])` in main.py |
| Web Speech API fails on Safari | Always keep text input visible. Test on Chrome. |
| Live demo breaks | Pre-record demo video on Day 3 morning as backup |

---

## Backend Dependencies (`requirements.txt`)

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
boto3==1.35.36
pydantic==2.9.2
pydantic-settings==2.5.2
python-multipart==0.0.12
Pillow==10.4.0
python-dotenv==1.0.1
aiofiles==24.1.0
httpx==0.27.2
```

## Frontend Dependencies

```json
{
  "next": "14.2.18",
  "react": "18.3.1",
  "tailwindcss": "3.4.11",
  "recharts": "2.12.7",
  "@headlessui/react": "2.1.8",
  "@heroicons/react": "2.1.5",
  "axios": "1.7.7",
  "framer-motion": "11.5.4",
  "react-dropzone": "14.2.3",
  "react-hot-toast": "2.4.1",
  "swr": "2.2.5"
}
```

## Color Palette

```js
// tailwind.config.js
colors: {
  asha: {
    green: '#128C7E',   // Primary (WhatsApp dark green)
    light: '#25D366',   // Accents (WhatsApp light green)
    teal:  '#075E54',   // Header
    chat:  '#ECE5DD',   // Chat background
  }
}
```
