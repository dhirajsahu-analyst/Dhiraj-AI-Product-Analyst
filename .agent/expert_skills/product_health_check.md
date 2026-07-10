# 🩺 Expert Skill: Product Data Health Check Methodology

This guide dictates the standardized, rigorous, 5-step methodology you must execute whenever a user asks you to perform a "Health Check," "Sanity Check," or "Data Audit" on a product telemetry table or view.

---

## 🎯 The Objective
A Health Check is not just describing the columns. It is an aggressive, proactive search for data leakages, logic flaws, stale pipelines, and structural anomalies (like join fan-outs) that could corrupt executive reporting.

When asked to audit a product, you must execute queries to test these 5 specific pillars:

---

## 🏗️ Step 1: Lineage & Grain Assessment (The Foundation)
You must determine what the table *claims* to be versus what it *actually* is.

1.  **Extract the DDL:** Run `SELECT GET_DDL('VIEW', '[table_name]')` to see the underlying code.
2.  **Determine the True Grain:** Look at the `GROUP BY` clause in the DDL. If a table is called "Monthly Account Summary" but it groups by Account *and* Region, the grain is actually Account+Region.
3.  **Identify the Source:** What raw (Bronze) tables feed this view? Are there unnecessary middle layers?

---

## ⏱️ Step 2: Temporal Freshness & Completeness
You must verify if the data pipeline is currently functioning or if it has silently failed.

1.  **Check Max Dates:** Query the `MAX(date_column)` to see the last time data was ingested.
    *   *Red Flag:* If the max date is more than 3 days old (for a daily pipeline), flag it as a "Stale Pipeline Outage."
2.  **Check Time Boundaries:** Query the `MIN(date_column)` to understand when telemetry began.
3.  **Check for Missing Months:** Group by month and count rows to ensure no entire months were silently dropped (e.g., due to harsh `WHERE` filters).

---

## 💥 Step 3: Primary Key Uniqueness (The Fan-Out Hunt)
You must aggressively test for duplicate rows that shouldn't exist based on the table's intended grain.

*   **The Diagnostic Query:** If the table is an "Account" table, test if Accounts duplicate within a single time period:
    ```sql
    SELECT time_column, account_id_column, COUNT(*) as row_count
    FROM target_table
    GROUP BY 1, 2
    HAVING COUNT(*) > 1
    ORDER BY row_count DESC;
    ```
*   *Red Flag:* If this returns rows, a Join Fan-Out has occurred. You must instruct the user to use `COUNT(DISTINCT)` instead of `SUM()` for all downstream metrics to avoid artificial inflation.

---

## 🧮 Step 4: Mathematical Integrity (Zero Leakage Check)
You must verify that logical subsets perfectly sum up to their parent totals.

*   **The Test:** If a table has `total_runs`, `manual_runs`, and `automated_runs`, test the math.
    ```sql
    SELECT time_column,
           SUM(total_runs) - SUM(COALESCE(manual_runs, 0) + COALESCE(automated_runs, 0)) AS variance
    FROM target_table
    GROUP BY 1
    HAVING variance != 0;
    ```
*   *Red Flag:* Any non-zero variance indicates data leakage (e.g., runs occurring that are missing a classification tag).

---

## 👻 Step 5: Orphaned Records & Identity Mismatches
You must check if usage is occurring without being properly mapped to a customer identity.

1.  **The Orphan Test:** Query how much usage is tied to a `NULL` or empty Account ID / Billing ID.
    ```sql
    SELECT COUNT(*) AS total_rows, 
           COUNT(CASE WHEN account_id IS NULL OR TRIM(account_id) = '' THEN 1 END) AS orphaned_rows
    FROM target_table;
    ```
2.  **Identity Casting Check:** If the telemetry uses `USER_ID`, profile a few rows to see if it is a String (Email) or a Numeric (GUID). Flag this so analysts know whether to use `LOWER()` string joins or explicit `CAST()` operations when bridging to other tables.

---

### 📝 Final Output Delivery
After executing these 5 steps, you must format your findings into a clear **"Product Health Check Report"**. 
Use clear headings (✅ **Passed**, ⚠️ **Warning**, ❌ **Critical Bug**) and always provide the exact SQL queries you used to uncover the anomalies.
