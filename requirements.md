# Requirements Document: VikasGPT

## 1. Functional Requirements (Integrated)

### 1.1 Intent-Aware Voice Gateway
* **R1.1:** The system shall utilize **Bhashini's ASR/TTS** to support voice-to-voice interaction in 22 regional languages.
* **R1.2:** The system must detect multi-domain intent (e.g., Agri + Health) within a single 15-second voice note.

### 1.2 Proactive Welfare Discovery
* **R1.3:** The **Yojna Agent** shall automatically trigger an eligibility alert if a user's health or agricultural situation changes (e.g., recommending *PM Fasal Bima* after a reported crop failure).
* **R1.4:** Form-Filling Automation: The system must pre-populate 70%+ of government scheme applications using data existing in the **Household Context Graph**.

### 1.3 Actionable Fulfillment
* **R1.5:** The system shall enable **one-click logistics booking** (ONDC/India Post) directly through the WhatsApp interface without requiring external apps.

## 2. Non-Functional Requirements

### 2.1 Performance & Accessibility
* **N2.1 Latency:** Round-trip response time (Audio -> AI Logic -> Audio) must be <10 seconds on 3G network conditions.
* **N2.2 Zero-UI:** All complex service flows must be navigable via voice dialogue only (No buttons or text menus required).

### 2.2 Safety & Data Integrity
* **N2.3 Accuracy:** Medical and agricultural advice must maintain a **95% grounding accuracy** against RAG-verified sources.
* **N2.4 Residency:** In compliance with the **DPDP Act 2023**, all PII (Personally Identifiable Information) must reside within the AWS Mumbai Region.
* **N2.5 Fault Tolerance:** If a specialized agent (e.g., ONDC) is offline, the Supervisor must provide a fallback message while keeping other agents (Health/Agri) active.

## 3. Deployment Constraints
* **Platform:** Must be **Serverless (AWS Lambda)** to minimize operational costs for the "pay-per-conversation" model.
* **Security:** Use **OAuth 2.0** for all external DPI (ABHA/eNAM) API integrations.