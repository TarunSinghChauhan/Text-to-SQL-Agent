# QueryPilot AI: Autonomous Data Investigator 🦇

QueryPilot AI is a production-grade, schema-aware **Autonomous Text-to-SQL Platform** designed as a high-fidelity "AI Data Investigator." It bridges the gap between natural language and complex database analytics by providing a specialized command center for data forensics, executive dashboarding, and automated business analysis.

## 🚀 Key Investigative Capabilities

### 🧠 1. Agentic Reasoning & Schema Logic
*   **Expert Surface Mapping**: Automatically identifies primary business keys (ID, Name, Country, Tier) during record retrieval to provide immediate context rather than isolated fragments.
*   **Intent Classification**: Pre-processes queries into high-level protocols: *Record Retrieval, Aggregation, Comparison, or Dashboard Generation.*
*   **Investigation Refusal Layer**: Rigorously validates schema "Evidence" before execution, refusing to generate logic if metrics are missing and suggesting forensic alternatives.

### 💼 2. Autonomous Analyst Agent (Post-Execution)
*   **Executive Dossier**: After every successful query, the AI Analyst synthesizes the result into a business narrative, performing automated distribution analysis and segment highlights.
*   **Strategic Findings**: Extracts latent trends like plan concentration, geographic dominance, and record integrity automatically.
*   **Next-Action Prediction**: Suggests the most logical "Follow-up Investigations" based on current results.

### 📊 3. Autonomous Dashboarding
*   **One-Click Command Hub**: Transform any analytical insight into a full-scale **Executive Dashboard** via natural language.
*   **KPI Synthesis**: Automatically identifies and renders KPIs, distribution charts, and executive summaries without manual visualization building.

### 🧛 4. Enterprise Investigator UI
*   **Three-Zone Architecture**: Inspired by high-end intelligence agency Command Centers (Crimson Sidebar, Ink-Black Core, Metallic Grey Intelligence Panel).
*   **Reasoning Timeline**: A transparent, vertical trace of the agent's work: *Schema Scanning → Intent Mapping → Validation → Insight Synthesis.*

## 🛠️ Technology Stack
*   **Core**: Python 3.10+, Streamlit (High-Density UI)
*   **Analytics Engine**: DuckDB (In-memory SQL Execution)
*   **Data Processing**: Pandas, NumPy
*   **Visuals**: Plotly Express (Forensic Charts)
*   **SQL Logic**: SQLGlot (Validation & Transpilation)
*   **Agent Flow**: LangGraph / LangChain (Intelligent Orchestration)

## 📦 Getting Started

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/TarunSinghChauhan/Text-to-SQL-Agent.git
    cd Text-to-SQL-Agent
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Launch the Investigator Hub**:
    ```bash
    streamlit run streamlit/ui.py
    ```

## 🎯 Sample Investigations
*   "Show top 5 customers from India"
*   "Compare plan tier distribution by revenue"
*   "Generate Executive Dashboard for the current segment"
*   "What are the primary growth trends?"

---
*Built for senior-level data engineering and AI analytics excellence.*
