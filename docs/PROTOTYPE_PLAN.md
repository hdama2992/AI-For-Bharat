# VikasGPT 2-Day Prototype Plan

## 🎯 Goal: End-to-End Working Demo

**Deadline:** 2 Days  
**Focus:** Health Triage + Onboarding + Mandi (Skip Pest-Vision)

---

## Day 1: Backend Foundation (8-10 hours)

### Morning (4 hours): Project Setup + Core APIs

| Hour | Task | Deliverable |
|------|------|-------------|
| **1** | Create FastAPI project structure | `backend/` folder with routers |
| **2** | Implement `/household` endpoints | Create + Get profile working |
| **3** | Add mock data files | `mandi_prices.json`, `msp_rates.json` |
| **4** | Implement `/mandi/*` endpoints | Price comparison logic working |

**Checkpoint:** Frontend Mandi page should work with real API!

### Afternoon (4 hours): Bedrock Integration

| Hour | Task | Deliverable |
|------|------|-------------|
| **5** | Setup Bedrock client | `services/bedrock.py` |
| **6** | Create Sehat agent prompt | Slot-filling system prompt |
| **7** | Implement `/health/chat` SSE | Streaming response working |
| **8** | Test end-to-end health flow | GREEN/YELLOW/RED triage |

**Checkpoint:** Health Triage chat should stream and return triage!

### Evening (2 hours): Onboarding AI

| Hour | Task | Deliverable |
|------|------|-------------|
| **9** | Implement `/onboard-extract` | AI extraction from voice turns |
| **10** | Test voice onboarding flow | Profile created from voice |

---

## Day 2: Polish + Demo Prep (8 hours)

### Morning (4 hours): Reliability + Edge Cases

| Hour | Task | Deliverable |
|------|------|-------------|
| **1** | Fix bugs from Day 1 testing | Stable APIs |
| **2** | Add proper error handling | Graceful failures |
| **3** | Improve triage prompts | Better ICMR guidelines |
| **4** | Add demo data | Pre-filled households |

### Afternoon (2 hours): Demo Flow

| Hour | Task | Deliverable |
|------|------|-------------|
| **5** | Record demo video script | 3-minute demo flow |
| **6** | Test on mobile device | PWA working |

### Final (2 hours): Presentation

| Hour | Task | Deliverable |
|------|------|-------------|
| **7** | Prepare slides if needed | Architecture diagram |
| **8** | Final testing + buffer | Ready for demo |

---

## Priority Modules (In Order)

### 🔴 P0: Must Have (Day 1)
1. **Health Triage Chat** - Streaming SSE, triage cards
2. **Household Create/Get** - Profile management
3. **Mandi Compare** - Price comparison with mock data

### 🟡 P1: Should Have (Day 1 Evening)
4. **Onboard Extract** - AI extraction from voice
5. **Context Insights** - Simple recommendations

### 🟢 P2: Nice to Have (Skip if short on time)
6. **Pest-Vision** - Image analysis (SKIP FOR NOW)

---

## Demo Script (3 minutes)

### Scene 1: Onboarding (45 sec)
*"Meet Rajesh, a soybean farmer in Harda, MP. He opens Asha-GPT for the first time..."*
- Show PM-KISAN lookup
- Voice onboarding in Hindi
- Profile created

### Scene 2: Mandi Advisor (45 sec)
*"Today Rajesh needs to sell his soybean harvest. Let's find the best price..."*
- Select crop + district
- Show price comparison
- Highlight ₹2,450 savings at Bhopal Mandi

### Scene 3: Health Triage (90 sec) ⭐ MAIN EVENT
*"That night, Rajesh's daughter has a high fever. Instead of panicking..."*
- Chat: "My 8-year-old daughter has high fever since morning"
- Asha asks: "How high? Any other symptoms?"
- Answer: "103°F, vomiting, won't eat"
- **RED TRIAGE CARD APPEARS** 🔴
- "Call 108 NOW" button
- Show ICMR-based reasoning

*"In 30 seconds, a family in rural India gets life-saving guidance."*

---

## Technical Shortcuts for Speed

### 1. Skip Real DynamoDB - Use In-Memory
```python
HOUSEHOLDS_DB = {}  # Simple dict for prototype
```

### 2. Hardcode Mock Data
```python
MANDI_PRICES = {
    "Soybean": {
        "Harda": {"modal_price": 4850, "distance": 0},
        "Bhopal": {"modal_price": 5120, "distance": 85},
    }
}
```

### 3. Simplified Triage Logic
```python
# Don't need full slot-filling for demo
# Just detect keywords and assign level
RED_KEYWORDS = ["chest pain", "breathing", "unconscious", "103", "104"]
YELLOW_KEYWORDS = ["fever", "vomiting", "3 days", "blood"]
```

### 4. Use Bedrock Converse API
```python
# Simpler than raw invoke
response = bedrock.converse(
    modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages=messages,
    system=[{"text": SEHAT_SYSTEM_PROMPT}],
)
```

---

## Minimum Backend Files Needed

```
backend/
├── main.py              # FastAPI app (all routes inline)
├── bedrock.py           # Bedrock streaming client
├── data/
│   └── mandi_prices.json
├── requirements.txt     # fastapi, uvicorn, boto3
└── .env
```

**That's it!** Single file for speed, refactor later.

---

## Success Criteria

✅ User can create profile (form or voice)  
✅ Dashboard loads with user name  
✅ Mandi shows price comparison  
✅ Health chat streams responses  
✅ Triage card (GREEN/YELLOW/RED) appears  
✅ Works on mobile viewport  
✅ Demo runs without errors for 3 minutes

