# 🗺️ System Walkthrough & Execution Flow
**Project:** AI Service Orchestrator  
**Framework:** Google Antigravity™ Mandatory Verification Trace

This document provides a detailed walkthrough of how a user request flows through the decoupled micro-engines of the AI Service Orchestrator system, mapping execution states from text ingestion to final fulfillment.

---

## 🔄 Step-by-Step Execution Journey

### Step 1: User Request Ingestion (Bilingual Input)
* **Action:** The customer interacts with the Streamlit frontend and inputs a localized, code-switched text query.
* **Example Input:** *"mera ac khrab hy koi rider lahore available"*
* **Processing:** The request is passed immediately to the `NLUModule`. The system bypasses rigid English boundaries, using structured typing to classify the request.

### Step 2: Real-Time NLU Intent Extraction
* **Action:** Antigravity logs the text parsing process.
* **System Outputs:**
  - **Normalized Service Intent:** `AC REPAIR`
  - **Urgency Level:** `High` (Derived from the context of a broken appliance in summer)
  - **Job Complexity:** `Intermediate` / `Complex`
  - **Target Location:** Derived from user profile selection (e.g., Sector G-9, Islamabad).

### Step 3: Multi-Factor Provider Discovery & Ranking
* **Action:** The `RankingEngine` queries `providers_db.json`.
* **Processing:** The engine evaluates local vendors using a 6+ factor weight algorithm (Distance, Travel ETA, Experience Tier, Star Rating, Reliability Index, and Client Risk).
* **UI Output:** Renders an analytical side-by-side comparison matrix of top matching specialists (e.g., Sajid Plumbers vs. Zafar Ali) right on the user dashboard.

### Step 4: Dynamic Invoice Calculations & "Paise Bachayein" Options
* **Action:** The `PricingEngine` runs variable cost models live.
* **Processing:** Generates an itemized breakdown containing the Base Visit Fee, Distance Travel Premium, and Urgency/Off-Peak Surcharges, fully translated into localized terminology (*"Bunyadi Kharcha"*, *"Izafi Kharcha"*).
* **Alternative Route:** If prices are high, the *Paise Bachayein Engine* offers dynamic alternative swaps (Shift to Off-Peak / Standard Hours) showing instant text savings alerts.

### Step 5: Transit-Buffered Calendar Allocation
* **Action:** User clicks **"Confirm and Book Appointment Now!"**
* **Processing:** The `SchedulingEngine` checks the selected provider's agenda. It automatically inserts a strict 30-minute pre-allocated **Transit Travel Buffer** around the job timeline to prevent overlapping bookings across city zones.

### Step 6: Sequence-Guarded State Transitions & Dispatch
* **Action:** The booking triggers the automated backend `TrackingEngine`.
* **State Machine Execution:** The system forces strict sequential node movements, blocking illegal jumps:
  $$\text{PENDING} \rightarrow \text{ACCEPTED} \rightarrow \text{EN\_ROUTE} \rightarrow \text{STARTED} \rightarrow \text{COMPLETED}$$
* **Live Updates:** Logs are written to `tracking_log.json` and rendered as a real-time status timeline stepper on the client's screen.

### Step 7: Bilingual SMS Payload Generation
* **Action:** The system completes the orchestration pipeline by simulating an SMS dispatch.
* **Output Payload:** Generates automated twin notifications sent directly to both the consumer and provider smartphone strings, containing English status lines paired with exact Roman Urdu translations (*"Khushkhabri! Provider aapka kaam qabool kar chuka hai..."*).
