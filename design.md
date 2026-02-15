# Design Document: VikasGPT (Conversational OS)

## 1. System Overview
VikasGPT is a "Conversational Operating System" designed as a unified WhatsApp gateway for rural Indian households. It serves as a bridge between complex Digital Public Infrastructure (DPI) and the end-user, providing voice-first access to health and wealth resources.

## 2. Multi-Agent Architecture
The system uses an orchestrator-worker pattern to decompose complex household requests into specialized tasks.

### 2.1 Agentic Workflow Diagram

### 2.2 Core Agents & Responsibilities
* **The Orchestrator (Supervisor Agent):** Acting as the "Brain," this agent uses Amazon Bedrock (Claude) to analyze user intent and route tasks to specialized workers.
* **The Health Agent (Sehat-Bot):** Integrated with ABDM/ABHA, it performs voice-based triage and interacts with eSanjeevani guidelines.
* **The Agriculture Agent (Krishi-Bot):** Powered by Bharat-VISTAAR, it provides crop-specific advisory and connects to eNAM for market prices.
* **The Logistics Agent (Dhwani-Agent):** Interfaces with ONDC rails and India Post to coordinate physical movement of goods.

## 3. Technical Stack
* **Interface:** WhatsApp Business API for low-bandwidth 2G/3G resilience.
* **Language Engine:** Bhashini API for 22+ regional dialect translation.
* **Compute:** AWS Lambda (Serverless) for event-driven orchestration.
* **Data Grounding:** Amazon Bedrock Knowledge Bases (RAG) ensuring responses are anchored in verified ICMR and ICAR data.

## 4. Household Context Graph

VikasGPT maintains a "Context Graph" that understands the household as a single economic unit. For instance, if the Agriculture Agent detects a crop loss, the Health Agent is alerted to prioritize stress-related wellness checks.

## 5. Security & Privacy
* **Dual-Vault Storage:** Medical (ABHA) and Agricultural data are stored in separate encrypted DynamoDB tables.
* **DPDP Compliance:** Implements granular, voice-based consent for every data retrieval action.