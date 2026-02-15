# Design Document: VikasGPT (Conversational OS)

## 1. Unified Multi-Agent Framework
VikasGPT is built on a **Supervisor-Worker** multi-agent architecture. It moves beyond "Q&A" to **Interactive Consulting**, using a state-aware loop to gather evidence before providing advice.

## 2. Evidence-Based Orchestration (Slot-Filling)
The system treats every interaction as a "Case File." No worker agent provides a resolution until the **Evidence Frame** is complete.

* **Stateful Memory:** Uses Amazon DynamoDB to track "Slots" (Evidence units).
* **Investigation Mode:** If a user says "I have a cough," the Supervisor identifies a missing slot: `[Duration]`. It pauses the resolution and generates a voice question: *"I understand. How many days have you had this cough?"*

### 2.1 System Architecture

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart TB
    subgraph User["👨‍🌾 Rural Household"]
        WA[WhatsApp Interface]
    end

    subgraph Gateway["🌐 Gateway Layer"]
        Bhashini[Bhashini API<br/>22+ Languages]
        WABA[WhatsApp Business API]
    end

    subgraph Brain["🧠 Orchestration Layer"]
        Supervisor[Supervisor Agent<br/>Amazon Bedrock - Claude]
        Memory[(Shared Memory<br/>Context Graph)]
    end

    subgraph Workers["⚙️ Specialized Agents"]
        Sehat[🏥 Sehat Agent<br/>Health Triage]
        Krishi[🌾 Krishi Agent<br/>Agri Advisory]
        Yojna[📜 Yojna Agent<br/>Scheme Matching]
        Dhwani[🚚 Dhwani Agent<br/>Logistics]
    end

    subgraph DPI["🇮🇳 Digital Public Infrastructure"]
        ABHA[ABHA/ABDM]
        AgriStack[AgriStack/eNAM]
        MyScheme[myScheme]
        ONDC[ONDC Rails]
    end

    WA <--> WABA
    WABA <--> Bhashini
    Bhashini <--> Supervisor
    Supervisor <--> Memory
    Supervisor <--> Sehat
    Supervisor <--> Krishi
    Supervisor <--> Yojna
    Supervisor <--> Dhwani
    Sehat <--> ABHA
    Krishi <--> AgriStack
    Yojna <--> MyScheme
    Dhwani <--> ONDC
```

### 2.2 Example: Multi-Domain Request Flow

```mermaid
%%{init: {'theme': 'forest'}}%%
sequenceDiagram
    participant User as 👨‍🌾 Farmer (WhatsApp)
    participant Super as 🧠 Supervisor (VikasGPT)
    participant Krishi as 🌾 Krishi Agent
    participant Yojna as 📜 Yojna Agent
    participant Sehat as 🏥 Sehat Agent

    User->>Super: "Crops are dying and I'm feeling weak."
    Note over Super: Intent: Agri + Health
    par Task 1: Agri Diagnostics
        Super->>Krishi: Analyze Crop Issue
        Krishi-->>Super: Result: Heat Stress detected
    and Task 2: Health Triage
        Super->>Sehat: Check Symptoms
        Sehat-->>Super: Result: Dehydration/Heatstroke
    end
    Note over Super: Integrated Insight: Both issues caused by Heatwave
    Super->>Yojna: Any heatwave compensation?
    Yojna-->>Super: Found: Disaster Relief Scheme eligible
    Super->>User: "You have heatstroke, please rest. I've also found a relief scheme for your heat-stressed crops. Should I apply for you?"
```

## 3. Integrated Specialized Workers

* **Sehat Agent (Health):**
    * **Evidence Slots:** [Symptoms, Location, Duration, Intensity, History].
    * **Grounding:** RAG-based lookup in ICMR manuals via Amazon Bedrock.
* **Krishi Agent (Agri):**
    * **Evidence Slots:** [Crop_Type, Growth_Stage, Visual_Symptoms, Soil_History].
    * **Tools:** Multimodal image analysis for "Evidence Photos" of pests.
* **Yojna Agent (Welfare):**
    * **Evidence Slots:** [Aadhaar_Linked, Income_Bracket, Land_Holding].
    * **Logic:** Matches "Life Events" from other agents to subsidies.
* **Sahayak Agent (Onboarding):**
    * **Function:** Bridges the gap for users without ABHA/AgriStack IDs.
    * **Logic:** Manages voice-based OTP authentication and account provisioning.

### 3.1 Sahayak Agent: Missing Account Fallback

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart TD
    subgraph Supervisor["🧠 Supervisor Agent"]
        CheckID{ID Exists?}
    end

    subgraph Sahayak["🤝 Sahayak (Onboarding) Agent"]
        CollectData[Collect Basic PII via Voice]
        TriggerOTP[Request Gov OTP]
        VerifyOTP[Verify OTP & Create ID]
    end

    subgraph DPI["🏛️ Government DPI"]
        ABHA_API[ABDM API]
        Agri_API[AgriStack API]
    end

    CheckID -- No --> CollectData
    CollectData -- Voice Input --> TriggerOTP
    TriggerOTP -- API Call --> ABHA_API
    ABHA_API -- SMS to User --> User((Farmer))
    User -- Speaks OTP --> VerifyOTP
    VerifyOTP -- Validation --> Agri_API
    Agri_API -- Account Created --> CheckID
    CheckID -- Yes --> Success[Resume Task Execution]
```

## 4. Technical Stack
* **Language:** Bhashini API (Speech-to-Speech in 22 dialects).
* **Brain:** Amazon Bedrock (Claude 3.5 Sonnet) for agent reasoning.
* **Execution:** AWS Step Functions to manage the "Interview State" and fallback logic.
* **Security:** AWS KMS Dual-Vault encryption (Health vs. Wealth isolation).

---

## 💡 Failsafe Design Principles

This architecture is designed to be **Failsafe**:

1. **If the user doesn't know what to say** → The Interview Logic guides them with one question at a time.
2. **If the user doesn't have an account** → The Sahayak Agent builds it via voice-based OTP.
3. **If the user has a cross-domain crisis** → The Supervisor coordinates all relevant agents in parallel.