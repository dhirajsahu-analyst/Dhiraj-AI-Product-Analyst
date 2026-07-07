# 🚀 The Alteryx AI Product Analytics Transformation Playbook

**Owner:** Principal Product Analyst  
**Audience:** Product Analytics Team, Data Engineers, Product Managers  
**Objective:** A step-by-step master guide and checklist to scale our elite, hallucination-free AI Product Analytics framework (Gemini CLI / Claude Code + Snowflake + GitHub) across the entire team.

---

## 🌟 Executive Summary: Why We Are Doing This
We are shifting from manual SQL queries and disparate dashboards to an **"AI-First Analytics Engineering"** paradigm. By combining local AI Agents with a strict Snowflake Semantic Layer and version-controlled GitHub repositories, we achieve:
1.  **Zero Hallucinations:** AI agents are grounded strictly in validated schemas.
2.  **Instant Answers:** PMs can query data in plain English and receive production-grade SQL and Markdown scorecards in seconds.
3.  **Reproducibility:** All metrics, RCAs (Root Cause Analyses), and data rules are version-controlled in GitHub.

---

## 🛠️ Phase 1: The Infrastructure Stack (Prerequisites)
Before onboarding a team member, ensure they have the following stack installed and authenticated on their local machine:

*   [ ] **Homebrew (macOS):** Package manager for installing CLIs.
*   [ ] **GitHub CLI (`gh`):** For secure repository cloning and CI/CD operations.
*   [ ] **Snowflake CLI (`snow`):** For Bring-Your-Own-Credentials (BYOC) database interaction.
*   [ ] **AI CLI Tools:** Either **Gemini CLI** or **Claude Code**.
*   [ ] **Python 3.9+:** To run the automated dashboard generators and SSO scripts.

---

## 📐 Phase 2: Building the "Flat" Semantic Layer (Snowflake)
The AI cannot operate effectively on messy, multi-layered ETL pipelines. We must enforce the **Flat Paradigm (Schema-on-Read)** for every product.

### The 3-Tier View Structure
For every new product (e.g., *Data Prep*, *Designer Cloud*), the analyst must build three views in `DISCOVERY_PRODUCT_MANAGEMENT.METRIC_STORE`:

1.  [ ] **`SEM_[PRODUCT]_USER_DAILY` (The Action Grain):** 
    *   *Rules:* 1 row per User, per Action, per Day. 
    *   *Must Include:* Lowercase email identity rescues (`COALESCE` logic) and internal tester exclusions (`NOT LIKE '%alteryx%'`).
2.  [ ] **`SEM_[PRODUCT]_ACCOUNT_MONTHLY` (The Executive Grain):** 
    *   *Rules:* 1 row per Salesforce Account, per Month.
    *   *Must Include:* Salesforce firmographics (ACV, Region, Industry) and safe division ratios (`NULLIF(denominator, 0)`).
3.  [ ] **`SEM_[PRODUCT]_OPERATIONAL_KPIS` (FinOps/Reliability):** 
    *   *Rules:* Live success/failure rates, error messages, and latency metrics.

---

## 📂 Phase 3: The Enterprise Repository Structure (GitHub)
Every analytics project must follow the elite directory architecture we established. This separates human documentation from machine-readable AI prompts.

### The Mandatory Directory Tree
*   [ ] **`.agent/` (Hidden AI Brain):** Contains `system_prompts/` (e.g., `master_directive.md`), `personas/` (e.g., `sql_surgeon.md`), and `expert_skills/` (e.g., `metric_layering.md`).
*   [ ] **`sql/` (The Codebase DAG):**
    *   `01_semantic_ddl/`: The `CREATE VIEW` scripts (Infrastructure-as-Code).
    *   `02_business_metrics/`: The standardized `SELECT` queries for dashboards.
    *   `03_data_quality/`: Freshness checks and duplicate audits.
*   [ ] **`src/` (Python Automation):** 
    *   `auth/snowflake_sso.py`: The secure BYOC connector.
    *   `runners/refresh_dashboard.py`: The local automation script for fetching data and writing Markdown.
*   [ ] **`docs/product_playbooks/`:** The human-readable markdown files containing metric catalogs and RCA logs.
*   [ ] **`Makefile` & `requirements.txt`:** For instant environment bootstrapping (`make install`, `make connect`).

---

## 🧠 Phase 4: Grounding the AI (Preventing Hallucinations)
The most critical step in the rollout is training the AI not to guess.

### The System Prompt Checklist (`master_directive.md`)
Every repository must have a master system prompt that explicitly tells the AI:
*   [ ] **The Disambiguation Mandate:** If a PM asks for "active users," the AI must stop and ask *which product* (AI Tools vs. Ask Alteryx) before writing SQL.
*   [ ] **The Paid-User Mandate:** Force the AI to inject `WHERE LICENSE_TYPE IN ('Subscription', 'Purchase')` into every generated query by default.
*   [ ] **The "So What?" Rule:** Force the AI to output a 2-sentence executive summary explaining the business impact of the generated numbers.
*   [ ] **Read-Only Mandate:** Strictly prohibit `CREATE`, `DROP`, or `UPDATE` commands.

---

## 🚀 Phase 5: The Team Rollout & Training Plan (Step-by-Step)

When you lead the workshop to roll this out to your team, follow this exact script:

### Step 1: Repository Cloning & Setup (15 Minutes)
1. Have the team run: `git clone https://github.com/dhirajsahu-analyst/Dhiraj-AI-Product-Analyst.git`
2. Run `make install` to load dependencies.
3. Run `make connect` to authenticate their local Snowflake SSO profiles (BYOC).

### Step 2: Running the First AI Copilot Session (15 Minutes)
1. Have the team open **Claude Code** or **Gemini CLI**.
2. Instruct them to load the master brain: `claude --append-system-prompt .agent/system_prompts/master_directive.md`
3. Have them ask a test question: *"How many paid subscription active users ran AI Tools last month, and what was the top tool?"*
4. *Watch the "Aha!" moment when the AI generates the perfect, pre-validated Snowflake SQL and an executive summary.*

### Step 3: Local Dashboard Automation (15 Minutes)
1. Show the team how to run: `python3 src/runners/refresh_dashboard.py`
2. Open `docs/EXECUTIVE_DASHBOARD.md` to show the dynamically injected Markdown scorecard.
3. Show them how to load the output `data/dashboard_data.json` into **Claude Artifacts** to instantly generate a React-based interactive chart.

### Step 4: Adding a New Product (The Capstone Assignment)
Assign the team a homework task:
1. Pick a new product (e.g., Designer Cloud).
2. Write the DDL view and place it in `sql/01_semantic_ddl/`.
3. Add a new product playbook in `docs/product_playbooks/`.
4. Update the `.agent/system_prompts/master_directive.md` to include the new catalog schema.
5. Commit and push to GitHub.

---

## 🛡️ Success Criteria (How to know you won)
You have successfully led this transformation when:
- PMs stop asking analysts to "pull a quick number" and start asking the AI directly via the standardized repo.
- The `main` branch of your GitHub repo becomes the undeniable source of truth for all metric formulas.
- Executive dashboards auto-refresh via the local Python runners or CI/CD pipelines without manual analyst intervention.
