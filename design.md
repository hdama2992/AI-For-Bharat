# Design Document: Asha-GPT (Conversational OS)

## 1. System Overview
[cite_start]Asha-GPT is a "Conversational Operating System" designed as a unified WhatsApp gateway for rural Indian households[cite: 21]. [cite_start]It employs a voice-first, multi-agent architecture to integrate healthcare and agricultural advisory services through a single conversational interface[cite: 22, 53].

## 2. Technical Architecture
[cite_start]The system is built on a serverless AWS stack for high scalability and cost-efficiency[cite: 59, 119].

### 2.1 User & Translation Layer
* [cite_start]**Interface:** WhatsApp Business API (Meta Cloud API) for high resilience on 2G/3G networks[cite: 61, 133].
* [cite_start]**Translation Service:** Bhashini API integration for real-time Automated Speech Recognition (ASR) and Text-to-Speech (TTS) in 22+ regional dialects[cite: 62, 108, 134].

### 2.2 Logic & AI Layer (The "Brain")
* [cite_start]**Orchestration:** AWS Lambda functions serve as the "Conversation Manager," handling intent routing and session management[cite: 66, 68, 71].
* [cite_start]**Core AI Engine:** Amazon Bedrock utilizing Claude for reasoning and triage, plus multimodal capabilities for image analysis (Pest-Vision)[cite: 70, 74, 113].
* [cite_start]**Grounding (RAG):** Amazon Bedrock Knowledge Bases and Amazon Q provide Retrieval-Augmented Generation to ensure responses are grounded in verified ICMR, ICAR, and government datasets[cite: 77, 84, 115].

### 2.3 Data Layer (Dual-Sandbox Architecture)
[cite_start]To comply with the DPDP Act 2023, the system utilizes a "Dual-Vault" design[cite: 28, 88]:
* [cite_start]**Krishi Vault (Agri):** Amazon DynamoDB storing farm profiles, crop history, and market preferences[cite: 90, 95].
* [cite_start]**Sehat Vault (Health):** Amazon DynamoDB storing health records and triage history, linked via ABHA ID[cite: 93, 102].
* [cite_start]**Security:** Encrypted using separate AWS KMS keys (Key-A for Agri, Key-B for Health) to prevent unauthorized cross-access[cite: 103, 104, 124].

## 3. Key Innovation: Household Context Graph
[cite_start]The system implements a unified data model that links crop cycles, financial capacity, and health status[cite: 141]. [cite_start]This allows the AI to provide cross-domain insights, such as recommending non-toxic pesticides specifically when a pregnant family member is detected in the household records[cite: 55, 56].

## 4. External DPI Integrations
* [cite_start]**Health:** ABDM/ABHA Sandbox for health record linkage and eSanjeevani for triage guidelines[cite: 43, 109].
* [cite_start]**Agriculture:** eNAM/Agmarknet APIs for real-time Mandi price feeds and ICAR databases for pest identification[cite: 34, 37, 108].