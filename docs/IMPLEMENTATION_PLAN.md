# VikasGPT Backend Implementation Plan

## Executive Summary

This document outlines the complete backend implementation for **VikasGPT (Asha-GPT)**, a conversational OS for rural Indian households built on Amazon Bedrock.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | FastAPI (Python 3.11) | Async REST API with SSE streaming |
| **AI** | Amazon Bedrock (Claude 3.5 Sonnet) | LLM for agents |
| **Database** | Amazon DynamoDB | User profiles, sessions |
| **Compute** | AWS Lambda / ECS Fargate | Serverless deployment |
| **Cache** | Redis (optional) | Session state caching |

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment settings
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── household.py        # /api/v1/household/*
│   │   ├── mandi.py            # /api/v1/mandi/*
│   │   ├── pest.py             # /api/v1/pest/*
│   │   └── health.py           # /api/v1/health/*
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bedrock.py          # Amazon Bedrock client
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── supervisor.py   # Supervisor agent (routing)
│   │   │   ├── sehat.py        # Health triage agent
│   │   │   ├── krishi.py       # Agriculture agent
│   │   │   └── prompts.py      # System prompts
│   │   └── dpi/
│   │       ├── __init__.py
│   │       ├── pmkisan.py      # PM-KISAN mock integration
│   │       ├── enam.py         # e-NAM Mandi prices mock
│   │       └── npss.py         # Pest surveillance mock
│   ├── models/
│   │   ├── __init__.py
│   │   ├── household.py        # Pydantic schemas
│   │   ├── health.py
│   │   ├── mandi.py
│   │   └── pest.py
│   └── db/
│       ├── __init__.py
│       └── dynamodb.py         # DynamoDB client
├── data/
│   ├── mandi_prices.json       # Mock Mandi price data
│   ├── msp_rates.json          # MSP 2025-26 rates
│   ├── crops.json              # Crop list
│   └── icmr_guidelines.json    # Health triage rules
├── tests/
│   ├── test_health.py
│   ├── test_mandi.py
│   └── test_household.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## API Endpoints (Required for Frontend)

### 1. Household Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/household` | Create new household profile |
| `GET` | `/api/v1/household/{id}` | Get household by ID |
| `POST` | `/api/v1/household/onboard-extract` | AI extraction from voice turns |
| `GET` | `/api/v1/household/context/{id}` | Get context insights |

### 2. Mandi Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/mandi/compare` | Compare prices across mandis |
| `GET` | `/api/v1/mandi/crops` | List available crops |
| `GET` | `/api/v1/mandi/districts` | List districts |

### 3. Health Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/health/chat` | Streaming health chat (SSE) |

### 4. Pest Module

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/pest/analyze` | Analyze crop image (multipart) |

---

## Database Schema (DynamoDB)

### Table: `households`
```json
{
  "household_id": "uuid",           // Partition Key
  "name": "string",
  "phone": "string",
  "state": "string",
  "district": "string",
  "crop_primary": "string",
  "crop_secondary": "string",
  "land_acres": "number",
  "family_members": [
    { "name": "string", "age": "number", "relation": "string", "is_pregnant": "boolean" }
  ],
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### Table: `health_sessions`
```json
{
  "household_id": "string",         // Partition Key
  "session_id": "string",           // Sort Key
  "messages": [],
  "slots": {
    "symptoms": "string",
    "duration": "string",
    "intensity": "string"
  },
  "triage_result": {},
  "created_at": "ISO8601"
}
```

---

## Health Triage Slot-Filling Flow

```
User Message → Check Required Slots → 
  IF missing → Ask clarifying question → Loop
  IF complete → RAG lookup ICMR guidelines → Generate Triage → Return GREEN/YELLOW/RED
```

**Required Slots:**
1. `symptoms` - What is the problem?
2. `duration` - How long?
3. `intensity` - How severe? (scale 1-10 or descriptive)
4. `age_group` - Child/Adult/Elderly?
5. `medical_history` - Diabetes, BP, pregnancy?

---

## Deployment Options

### Option A: Local Development
```bash
docker-compose up -d
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### Option B: AWS Serverless
- API Gateway + Lambda + DynamoDB
- Bedrock in ap-south-1 (Mumbai)

### Option C: AWS Container
- ECS Fargate + DynamoDB
- Better for streaming SSE responses

---

## Environment Variables

```env
# AWS
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# DynamoDB
DYNAMODB_TABLE_PREFIX=vikasgpt_

# App
API_BASE_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000
```

