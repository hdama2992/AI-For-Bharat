# Requirements Document: VikasGPT

## 1. Functional Requirements (Evidence-First)

### 1.1 Goal-Oriented Dialogue
| ID | Requirement | Priority |
|----|-------------|----------|
| R1.1 | **Evidence Mandate:** The system shall NOT render medical or financial advice until all "Primary Slots" defined in the domain agent's schema are filled. | Must Have |
| R1.2 | **Single-Turn Inquiry:** The agent must only ask one evidence-gathering question at a time to maintain clarity for low-literacy users. | Must Have |
| R1.3 | **Persistence:** The system must save "Interview Progress" in DynamoDB. If a farmer disconnects, the AI must resume from the exact evidence-gathering step upon next message. | Must Have |

### 1.2 Sahayak (Onboarding) Logic
| ID | Requirement | Priority |
|----|-------------|----------|
| R1.4 | **Automated Discovery:** If an agent fails to fetch a DPI record (e.g., ABHA Not Found), it must trigger the Sahayak Agent to initiate voice-based registration. | Must Have |
| R1.5 | **Shadow Profiling:** For users without government accounts, maintain a "Local Context Profile" to provide limited, general assistance while onboarding is pending. | Should Have |

### 1.3 Action & Fulfillment
| ID | Requirement | Priority |
|----|-------------|----------|
| R1.6 | **Evidence-Backed Booking:** Logistics (Dhwani) shall only be triggered once the Krishi Agent confirms "Harvest Readiness" evidence. | Must Have |
| R1.7 | **Proactive Scheme Matching:** The Yojna Agent shall automatically scan for eligible schemes when life events (crop loss, health emergency) are detected by other agents. | Should Have |

---

## 2. Non-Functional Requirements

### 2.1 Accuracy & Trust
| ID | Requirement | Target |
|----|-------------|--------|
| N2.1 | **Hallucination Prevention:** Use Amazon Bedrock Guardrails + Self-Correction loop where Supervisor validates worker output against gathered evidence. | 95% grounding accuracy |
| N2.2 | **Voice-First:** Deliver 100% of data-gathering and onboarding flows via Voice Notes using Bhashini API. | 100% coverage |
| N2.3 | **RAG Grounding:** All medical advice grounded in ICMR protocols; all agricultural advice grounded in ICAR guidelines via Amazon Bedrock Knowledge Bases. | Mandatory |

### 2.2 Safety & Privacy
| ID | Requirement | Compliance |
|----|-------------|------------|
| N2.4 | **Informed Consent:** Record "Voice Affirmation" before creating government accounts or sharing health data cross-agent. | DPDP 2023 |
| N2.5 | **Data Residency:** All citizen data must reside in AWS Mumbai Region (ap-south-1). | DPDP 2023 |
| N2.6 | **Dual-Vault Encryption:** Health and Wealth data stored in separate DynamoDB tables with different AWS KMS keys. | Security Best Practice |
| N2.7 | **PII Protection:** Aadhaar, phone numbers, and health records automatically redacted from logs using Bedrock Guardrails. | DPDP 2023 |

### 2.3 Performance & Accessibility
| ID | Requirement | Target |
|----|-------------|--------|
| N2.8 | **Latency:** Round-trip response time (Voice In → AI Processing → Voice Out) under 10 seconds on 3G networks. | < 10 sec |
| N2.9 | **Low Bandwidth:** System must function on 2G/3G networks common in rural India. | 64 kbps minimum |
| N2.10 | **Zero-UI:** All service flows navigable via voice dialogue only (no buttons or text menus required). | 100% |

### 2.4 Reliability
| ID | Requirement | Target |
|----|-------------|--------|
| N2.11 | **Fault Tolerance:** If a specialized agent (e.g., ONDC) is offline, Supervisor must provide fallback message while other agents remain active. | 99.9% uptime |
| N2.12 | **Graceful Degradation:** Network failures must not lose conversation state; resume on reconnection. | Mandatory |

---

## 3. Technical Requirements (AWS-Native)

### 3.1 Core Platform
| Component | AWS Service | Purpose |
|-----------|-------------|---------|
| **AI Brain** | Amazon Bedrock | Claude 3.5 Sonnet (reasoning) + Claude 3 Haiku (slot-filling) |
| **Multi-Agent** | Amazon Bedrock Multi-Agent Collaboration | Supervisor-Worker orchestration |
| **Knowledge Search** | Amazon Q Business | Enterprise search across ICMR/ICAR documents |
| **Knowledge Base** | Amazon Bedrock Knowledge Bases | RAG vector store for verified guidelines |
| **State Storage** | Amazon DynamoDB | Case files, slots, conversation history |
| **Compute** | AWS Lambda | Serverless agent execution |
| **Orchestration** | AWS Step Functions | Interview state machine, agent handoffs |
| **Security** | AWS KMS + Bedrock Guardrails | Encryption + content safety filters |

### 3.2 External Integrations (Complete DPI List)

| Category | Integration | Protocol | Purpose |
|----------|-------------|----------|---------|
| **Interface** | WhatsApp Business API | REST + Webhooks | Primary user interface |
| **Gateway** | Bhashini (NLTM) | gRPC/REST | 22-language Speech-to-Text and Text-to-Speech |
| **Gateway** | DigiLocker | REST + OAuth 2.0 | Verified ID document access |
| **Identity** | UIDAI (Aadhaar) | REST + OTP | e-KYC for user onboarding |
| **Health** | ABHA/ABDM | REST + OAuth 2.0 | Health ID and longitudinal records |
| **Health** | eSanjeevani | REST | Tele-consultation escalation |
| **Health** | Jan Aushadhi Sugam | REST | Generic medicine store locator |
| **Agriculture** | AgriStack | REST | Farmer ID, land records, crop history |
| **Agriculture** | e-NAM / AGMARKNET | REST | Real-time Mandi prices |
| **Agriculture** | Bharat-VISTAAR | REST | ICAR-integrated crop advisory |
| **Agriculture** | NPSS | REST | National Pest Surveillance System |
| **Welfare** | myScheme | REST | 2000+ scheme eligibility matching |
| **Welfare** | PM-Kisan / PMFBY | REST | Income support and crop insurance |
| **Welfare** | UMANG | REST | 1200+ government services |
| **Logistics** | ONDC Network | REST + Callbacks | Transport and e-commerce booking |
| **Logistics** | India Post | REST | Physical delivery in remote areas |

---

## 4. Deployment Constraints

| Constraint | Requirement |
|------------|-------------|
| **Architecture** | 100% Serverless (pay-per-conversation model) |
| **Region** | AWS Mumbai (ap-south-1) only |
| **API Standards** | REST/OAuth 2.0 for all DPI integrations |
| **Monitoring** | Amazon CloudWatch for latency and error tracking |
| **Cost Model** | Optimized for < Rs 0.50 per conversation |