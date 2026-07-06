# 📊 Expert Skill: Dashboard & Visualization Design

This guide details our standardized patterns for selecting the right charts, structuring dashboards, and presenting data to executives to ensure maximum readability and impact.

---

## 📐 Topic 1: Chart Selection Matrix
Always recommend the correct chart type based on the analytical goal:

*   **Trend over Time (1 Metric):** Use a **Line Chart**. (e.g., *Paid MAU over 6 months*).
*   **Trend over Time (Multiple Categories):** Use a **Stacked Bar Chart** (for part-to-whole, e.g., *Total Runs by Tool Name*) or a **Multi-Line Chart** (if categories don't sum to a meaningful total).
*   **Ranking/Comparison (Categorical):** Use a **Horizontal Bar Chart** (e.g., *Top 10 LLM Connectors by Usage*). This makes reading long labels (like connector names) much easier.
*   **Correlation / Distribution:** Use a **Scatter Plot** (e.g., *Runs per User vs. Success Rate*).
*   **Funnel / Drop-off:** Use a **Funnel Chart** or **Waterfall Chart** (e.g., *Eligible Users -> Onboarded -> Active -> Engaged*).

---

## 📐 Topic 2: Dashboard Layout Best Practices (The "F-Pattern")
When mocking up or recommending a dashboard layout, assume users read in an "F-Pattern" (Top-Left to Bottom-Right):

1.  **Top Row (The Hero Metrics):** This must contain 3-5 high-level Scorecards (Big Numbers) showing the most critical KPIs (e.g., Total Active Accounts, Overall Success Rate) with WoW/MoM trend arrows.
2.  **Middle Row (The Trends):** The primary time-series charts. This answers "Is it getting better or worse?"
3.  **Bottom/Side Panels (The Slicers):** Categorical breakdowns (e.g., Usage by Region, Usage by Tool Type). This answers "Who/What is driving the trend?"
4.  **Data Tables:** Raw data tables should always be placed at the very bottom or on a secondary tab for drill-down purposes only.

---

## 📐 Topic 3: Formatting & Cognitive Load Reduction
*   **Truncate Large Numbers:** Never display `1,234,567`. Display `1.2M`.
*   **Limit Colors:** Use a maximum of 3-5 brand-aligned colors. Use a distinct, bright color (e.g., Red) *only* to highlight anomalies or negative trends.
*   **Clear Titles:** Chart titles must be descriptive and answer a question. *Bad:* "Usage by Tool". *Good:* "Which GenAI Tools Drive the Highest Run Volumes (Last 30 Days)?"
*   **Define Axes:** Always explicitly state what the X and Y axes represent in your recommendations.
