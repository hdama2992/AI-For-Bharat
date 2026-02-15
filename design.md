# Design Document: VikasGPT (Conversational OS)

## 1. Unified Multi-Agent Framework
VikasGPT is built on a **Supervisor-Worker** multi-agent architecture designed to handle concurrent tasks across health, wealth, and welfare domains through a single conversational thread.

### 2. Multi-Agent Orchestration Detail

#### 2.1 System Architecture

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

#### 2.2 Example: Multi-Domain Request Flow

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

#### 2.3 Supervisor Agent (The Brain)
* **Technology:** Amazon Bedrock (Claude 3.5 Sonnet).
    * **Logic:** Employs a **Hierarchical Orchestration** model. It decomposes complex user inputs (e.g., "I'm sick and my onions are rotting") into parallel sub-tasks.
    * **State Management:** Uses **Shared Memory** to maintain context across agents, ensuring the Sehat agent knows the Krishi agent's findings for cross-domain insights.

### 3. Integrated Specialized Workers
* **Sehat Agent (Health):** * **Data Source:** Connects via **ABHA Sandbox** APIs to medical records.
    * **Logic:** Uses RAG (Retrieval-Augmented Generation) grounded in **ICMR triage protocols** to classify cases into Green/Yellow/Red severity levels.
* **Krishi Agent (Agri):** * **Integrations:** **Bharat-VISTAAR** for advisory and **eNAM** for real-time Mandi price parity.
    * **Tools:** Implements a **Vision-Language Model (VLM)** for pest and disease identification from user-uploaded images.
* **Yojna Agent (Social Welfare):** * **Logic:** A proactive "Scanning Agent" that continuously matches the household's profile (from AgriStack) against **myScheme** databases to find eligible subsidies.
* **Dhwani Agent (Logistics):** * **Execution:** Acts as the "Tool Agent" to book services via **ONDC** shared mobility rails and **India Post** APIs.

### 4. Security & Compliance (Privacy-by-Design)
* **Dual-Vault Encryption:** Data is logically separated into a "Health Vault" and "Wealth Vault" using different **AWS KMS keys**.
* **Governance:** Implements a **Reviewer Agent** (Critique Mechanism) to validate advice against government safety standards before transmission to the user, mitigating hallucinations.