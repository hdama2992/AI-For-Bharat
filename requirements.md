# Requirements Document: Asha-GPT

## 1. Functional Requirements

### 1.1 Krishi (Agriculture) Module
* [cite_start]**Smart Mandi Advisor:** The system shall compare real-time prices across nearby Mandis and calculate net profit after transport costs[cite: 32].
* [cite_start]**Pest-Vision:** The system must allow users to upload images of crops for AI-driven disease identification and pesticide recommendation[cite: 35, 36].
* [cite_start]**Scheme Matcher:** The system shall conduct conversational eligibility checks for government programs like PM-KISAN through voice-based questions[cite: 38].

### 1.2 Sehat (Healthcare) Module
* [cite_start]**AI Health Triage:** The system shall provide voice-based symptom assessment classified into Green (home care), Yellow (PHC visit), and Red (emergency) based on eSanjeevani guidelines[cite: 43, 44].
* [cite_start]**Misinformation Filter:** The system shall fact-check forwarded WhatsApp health claims against ICMR verified knowledge bases[cite: 46, 48].
* [cite_start]**Medicine Reminders:** The system shall support user-configured voice/text reminders for chronic illness medication[cite: 50, 51].

### 1.3 Cross-Domain Intelligence
* [cite_start]**Household Awareness:** The system shall proactively flag health-specific warnings (e.g., pesticide safety for pregnant residents) based on integrated household data[cite: 55, 56].

## 2. Non-Functional Requirements

### 2.1 Connectivity & Accessibility
* [cite_start]**Resilience:** The system must remain functional on 2G (text) and 3G (voice) connectivity[cite: 133].
* [cite_start]**Interface:** The system must require zero app downloads or UI training, operating entirely through WhatsApp[cite: 24, 25].
* [cite_start]**Language Support:** The system shall support 22+ Indian languages via voice-to-voice interaction[cite: 26, 134].

### 2.2 Performance
* [cite_start]**Latency:** Text responses shall be delivered in <3 seconds; voice responses in <8 seconds[cite: 157].
* [cite_start]**Accuracy:** Emergency (Red) triage escalations must maintain 95% accuracy validated against clinical data[cite: 154].

### 2.3 Regulatory & Security
* [cite_start]**DPDP Compliance:** The system must store medical and financial data in separate, encrypted vaults using unique encryption keys[cite: 28, 143].
* [cite_start]**Guardrails:** The AI must have hard-coded constraints against recommending prescription drugs or hallucinatory medical advice[cite: 113, 116].

## 3. Technical Constraints
* [cite_start]**Platform:** Development must utilize the AWS India Region for data residency compliance[cite: 138].
* [cite_start]**Infrastructure:** The backend must be serverless (AWS Lambda) to ensure a "pay-per-conversation" cost model[cite: 119, 121].