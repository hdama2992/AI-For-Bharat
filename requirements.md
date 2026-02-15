# Requirements Document: VikasGPT

## 1. Functional Requirements (Evidence-First)

### 1.1 Goal-Oriented Dialogue
* **R1.1:** **Evidence Mandate:** The system shall NOT render medical or financial advice until all "Primary Slots" defined in the domain agent's schema are filled.
* **R1.2:** **Single-Turn Inquiry:** The agent must only ask one evidence-gathering question at a time to maintain clarity for low-literacy users.
* **R1.3:** **Persistence:** The system must save the "Interview Progress." If a farmer hangs up, the AI must resume the specific evidence-gathering step upon the next message.

### 1.2 Sahayak (Onboarding) Logic
* **R1.4:** **Automated Discovery:** If an agent fails to fetch a DPI record (e.g., ABHA Not Found), it must trigger the Sahayak Agent to initiate voice-based registration.
* **R1.5:** **Shadow Profiling:** For users without government accounts, the system shall maintain a "Local Context Profile" to provide limited, general assistance while onboarding is pending.

### 1.3 Action & Fulfillment
* **R1.6:** **Evidence-Backed Booking:** Logistics (Dhwani) shall only be triggered once the Krishi Agent confirms "Harvest Readiness" evidence.

## 2. Non-Functional Requirements

### 2.1 Accuracy & Trust
* **N2.1 Hallucination Prevention:** The system shall use a **Self-Correction loop** where the Supervisor double-checks worker output against gathered evidence before speaking to the user.
* **N2.2 Voice-First:** The system must deliver 100% of its data-gathering and onboarding flows via Voice Notes.

### 2.2 Safety & Privacy
* **N2.3 Informed Consent:** The system must record a "Voice Affirmation" before creating a government account or sharing health data with the Yojna agent.
* **N2.4 Residency:** In compliance with DPDP 2023, all evidence data must reside in the AWS Mumbai Region.

## 3. Deployment Constraints
* **Platform:** Entirely Serverless (AWS Lambda) for cost scalability.
* **API Standards:** Must use REST/OAuth 2.0 for all DPI integrations.