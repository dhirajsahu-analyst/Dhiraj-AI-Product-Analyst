# 📐 Expert Skill: Metric Layer Design

This guide outlines our standard approach for modeling business metrics, establishing clean multi-tier view hierarchies, and documenting the KPI definitions inside the semantic layer.

---

## 📐 Topic 1: Standard view grains
When designing new semantic views inside Snowflake, you must enforce a strict **three-tier VIEW grain**:

1.  **Daily User Grain (`SEM_[PRODUCT]_USER_DAILY`):** 
    - *Purpose:* Standardizes transaction events down to individual daily actions. 
    - *Filter requirements:* Always enforce the **Identity Waterfall Join** (coalescing fallback keys like lowercase emails) and strip out internal testing domains (`USER_ID NOT LIKE '%alteryx%'`).
2.  **Monthly Account Grain (`SEM_[PRODUCT]_ACCOUNT_MONTHLY`):** 
    - *Purpose:* Roll-up aggregates of monthly active accounts, active creators/consumers, total sessions, and cumulative run volumes.
    - *Join requirements:* Incorporate Salesforce firmographic attributes (sales regions, market segments, Annual Contract Value [ACV], Global 2000 flags).
3.  **Operational FinOps/Reliability Grain (`SEM_[PRODUCT]_OPERATIONAL_KPIS`):**
    - *Purpose:* Live metrics for system execution success/failure rates, average duration, latency, and prompt/completion token costs.

---

## 📐 Topic 2: Standard Metric Alignments (AARRR Funnel)

Always map your database metrics to these formal AARRR framework tiers:

### 1. Acquisition / Eligibility (TAM)
*   *Definition:* The technically capable universe of accounts/users.
*   *Calculation logic:* Mapped accounts running eligible software versions (`2025.2+` for Copilot) with active subscription tiers (`LICENSE_TYPE = 'Purchase'`).

### 2. Activation / Onboarding
*   *Definition:* Users or accounts executing their first-ever tool session.
*   *Calculation logic:* Minimum timestamp recorded where `USER_ID IS NOT NULL`.

### 3. Engagement / Retention (Habit Loops)
*   *Definition:* Users successfully integrating the tool into their regular work schedule.
*   *Calculation logic:* 30–60 day cohort returning user percentage, and engagement intensity (ratio of runs per active user per month).
*   *Engaged threshold:* Formally defined as users initiating **5 or more conversations** containing chat messages.
