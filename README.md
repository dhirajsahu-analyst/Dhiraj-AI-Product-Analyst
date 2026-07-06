# 🤖 Dhiraj AI Product Analyst: Standardized Grounding Agent Repo

Welcome to the **Dhiraj AI Product Analyst** repository. This is a production-ready, standardized package designed to instantiate, run, and scale an elite, grounded **AI Product Analyst Copilot** across Alteryx's entire GenAI product portfolio.

By combining detailed telemetry metadata schemas with validated, copy-paste-ready Snowflake SQL queries, this repository completely eliminates LLM hallucinations. Analysts and PMs can clone this repo, authenticate their local Snowflake CLI connections, and start asking complex engagement, adoption, or diagnostic questions immediately.

---

## 📁 Repository Structure

```text
Dhiraj-AI-Product-Analyst/
├── README.md                           # Main installation & configuration guide
├── Dhiraj-AI-Product-Analyst.md        # Master System Prompt / Agent Grounding file
├── prompts/                            # System instructions for active AI shells
│   ├── gemini.md
│   ├── claude.md
│   └── codex.md
├── examples/                           # In-depth product analytics guides
│   ├── ai_tools.md
│   ├── llm_connections.md
│   ├── auto_insights.md
│   └── ask_alteryx.md
└── sql/                                # Hardcoded, validated Snowflake SQL scripts
    ├── freshness.sql
    ├── ai_tools.sql
    └── llm_connections.sql
```

---

## 🚀 How to Install and Initialize

### Step 1: Clone this Repository
Clone the repository to your local development workspace:
```bash
git clone https://github.com/dhirajsahu-analyst/Dhiraj-AI-Product-Analyst.git
cd Dhiraj-AI-Product-Analyst
```

### Step 2: Set up your Local Snowflake CLI (BYOC)
This agent enforces a **Bring-Your-Own-Credentials (BYOC)** policy. It never asks for, stores, or logs passwords. Instead, it utilizes your authenticated local **Snowflake CLI (`snow`)** configuration.

1.  Ensure you have `snowflake-cli` installed:
    ```bash
    pip install snowflake-cli-labs
    ```
2.  Configure your credentials locally (add your user account, role, warehouse, and Azure AD/Okta browser SSO details):
    ```bash
    snow connection add
    ```
3.  Test your connection and active session:
    ```bash
    snow connection test
    snow sql -q "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();"
    ```
*(If you have multiple connection profiles, you can specify your Alteryx one with `--connection my_profile`).*

---

## 🤖 Running the Agent in your Preferred Shell

You can load our master system grounding file (`Dhiraj-AI-Product-Analyst.md`) directly into your terminal-based AI assistant to activate the **AI Product Analyst** persona:

### 1. Gemini CLI
```bash
gemini --context Dhiraj-AI-Product-Analyst.md
```

### 2. Claude Code CLI
```bash
claude --append-system-prompt Dhiraj-AI-Product-Analyst.md
```

### 3. Codex CLI
```bash
codex chat --system-file Dhiraj-AI-Product-Analyst.md
```

### 4. Cursor / VS Code Agent Mode
Add the `Dhiraj-AI-Product-Analyst.md` file as a persistent **System Prompt** or attach it as a reference file in your chatbot workspace (using `@Dhiraj-AI-Product-Analyst.md`).

---

## 📊 Standard Example Questions You Can Ask Immediately

Once the agent is loaded, you can run questions such as:

*   **AI Tools Adoption:** *"How many paid subscription active accounts and users ran AI Tools last month, and what is our success rate?"*
*   **LLM Connections Slicing:** *"Which private LLM connector displays the highest setup volume among paying enterprise tiers?"*
*   **Auto Insights Health:** *"Query the monthly trend of paid Auto Insights MAUs and aggregate report generation volumes."*
*   **Ask Alteryx (Copilot) Adoption:** *"Generate the Snowflake SQL to retrieve our 30-to-60 day returning users cohort retention rate for Copilot."*
*   **Telemetry Freshness Check:** *"Is our telemetry pipeline currently up to date? Write the query to check max dates."*

---

## 🏛️ How the Semantic Layer Works
To ensure maximum query performance and protect against upstream database duplication, the agent **always prefers semantic layer views and tables** over raw event logs:
1.  **Strict Paid Filters:** The agent automatically injects `WHERE LICENSE_TYPE IN ('Subscription', 'Purchase')` or `WHERE LICENSE_TYPE = 'Purchase'` to focus on paying cohorts.
2.  **No Join Fan-Outs:** The agent enforces `QUALIFY ROW_NUMBER() OVER (PARTITION BY ...)` filters on Salesforce or Billing account joins to suppress fanning out.
3.  **Cross-Pipeline lowercase Email Joins:** Bypasses implicit casting mismatches (e.g., joining numeric GUIDs to string emails) by linking pipelines on lowercase `USER_EMAIL` or `USER_ID` string keys.
