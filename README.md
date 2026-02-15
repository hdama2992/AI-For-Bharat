# VikasGPT - Conversational OS for Rural India

> A **Stateful Agentic Workflow** on Amazon Bedrock that provides voice-first access to health, agriculture, and welfare services for rural Indian households via WhatsApp.

![AWS](https://img.shields.io/badge/AWS-Amazon%20Bedrock-orange)
![Status](https://img.shields.io/badge/Status-Hackathon%20Prototype-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Problem Statement

700+ million rural Indians lack easy access to:
- **Healthcare guidance** in their local language
- **Agricultural advisory** for crop diseases and market prices
- **Government schemes** they are eligible for
- **Logistics** to transport their harvest to better markets

Existing solutions require apps, literacy, and high-speed internet — none of which are universally available in rural India.

---

## Our Solution

**VikasGPT** is a WhatsApp-based "Conversational Operating System" that:

1. **Speaks their language** — Voice-first interaction in 22+ regional dialects via Bhashini
2. **Gathers evidence before advising** — No hallucinations; every response is grounded in verified data
3. **Connects to Digital Public Infrastructure** — ABHA, AgriStack, eNAM, myScheme, ONDC
4. **Works on 2G/3G networks** — Optimized for low-bandwidth rural connectivity

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        👨‍🌾 FARMER (WhatsApp)                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Voice Note
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 GATEWAY LAYER                              │
│     WhatsApp Business API  ←→  Bhashini API (22 Languages)      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Text
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 🧠 ORCHESTRATION LAYER                           │
│            Amazon Bedrock Multi-Agent Collaboration              │
│    ┌─────────────────────────────────────────────────────┐      │
│    │              SUPERVISOR AGENT                        │      │
│    │         (Claude 3.5 Sonnet on Bedrock)              │      │
│    └─────────────────────┬───────────────────────────────┘      │
│                          │                                       │
│    ┌──────────┬──────────┼──────────┬──────────┐                │
│    ▼          ▼          ▼          ▼          ▼                │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │
│ │Sehat │ │Krishi│ │Yojna │ │Dhwani│ │Sahayak│                   │
│ │Agent │ │Agent │ │Agent │ │Agent │ │Agent │                   │
│ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘                   │
└────┼────────┼────────┼────────┼────────┼────────────────────────┘
     │        │        │        │        │
     ▼        ▼        ▼        ▼        ▼
┌─────────────────────────────────────────────────────────────────┐
│                 🇮🇳 DIGITAL PUBLIC INFRASTRUCTURE                 │
│    ABHA/ABDM    AgriStack    myScheme    ONDC    India Post     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Evidence-First Slot-Filling** | Agents gather all required information before providing advice |
| **Multi-Agent Collaboration** | Supervisor routes to specialized workers (Health, Agri, Welfare, Logistics) |
| **RAG-Grounded Responses** | All advice verified against ICMR/ICAR knowledge bases |
| **Voice-First UX** | 100% navigable via voice in 22 regional languages |
| **Proactive Scheme Matching** | Automatically finds eligible government schemes |
| **Failsafe Onboarding** | Creates ABHA/AgriStack IDs via voice OTP if missing |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **AI Brain** | Amazon Bedrock (Claude 3.5 Sonnet + Claude 3 Haiku) |
| **Multi-Agent** | Amazon Bedrock Multi-Agent Collaboration |
| **Knowledge** | Amazon Bedrock Knowledge Bases + Amazon Q Business |
| **Compute** | AWS Lambda (Serverless) |
| **State** | Amazon DynamoDB |
| **Orchestration** | AWS Step Functions |
| **Security** | AWS KMS + Bedrock Guardrails |
| **Voice** | Bhashini API (22 languages) |
| **Interface** | WhatsApp Business API |

---

## Agents & DPI Integration

| Agent | Domain | Function | Government DPIs |
|-------|--------|----------|-----------------|
| **Supervisor** | Orchestration | Routes requests, manages state | Bhashini (22 languages), DigiLocker |
| **Sehat** | Health | Voice-based triage using ICMR protocols | ABHA/ABDM, eSanjeevani, Jan Aushadhi Sugam |
| **Krishi** | Agriculture | Crop advisory, pest detection, Mandi prices | AgriStack, e-NAM, Bharat-VISTAAR, NPSS |
| **Yojna** | Welfare | Government scheme eligibility matching | myScheme (2000+ schemes), PM-Kisan, UMANG |
| **Dhwani** | Logistics | Transport booking and delivery | ONDC Network, India Post |
| **Sahayak** | Onboarding | Voice OTP-based ID creation | UIDAI (Aadhaar e-KYC) |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Design Document](./design.md) | System architecture, agent schemas, workflow diagrams |
| [Requirements Document](./requirements.md) | Functional and non-functional requirements |

---

## Team

Built with ❤️ for Rural India

---

## License

MIT License - See [LICENSE](./LICENSE) for details

