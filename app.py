import streamlit as st
import datetime as dt
from datetime import datetime, timedelta
import pandas as pd
from nlu_module import IntentExtraction
from ranking_engine import RankingEngine
from pricing_engine import PricingEngine
from scheduling_engine import SchedulingEngine
from tracking_engine import TrackingEngine
from reputation_engine import ReputationEngine
from dispute_engine import DisputeEngine

# Initialize core services in session state to maintain state across interactions
if "scheduling_engine" not in st.session_state:
    st.session_state.scheduling_engine = SchedulingEngine(buffer_minutes=30)
if "pricing_engine" not in st.session_state:
    st.session_state.pricing_engine = PricingEngine(cost_per_km=50.0, base_travel_overhead=100.0)
if "ranking_engine" not in st.session_state:
    st.session_state.ranking_engine = RankingEngine()
if "tracking_engine" not in st.session_state:
    st.session_state.tracking_engine = TrackingEngine(log_path="tracking_log.json")
if "reputation_engine" not in st.session_state:
    st.session_state.reputation_engine = ReputationEngine(
        providers_db_path="providers_db.json",
        reviews_log_path="reviews_log.json"
    )
if "dispute_engine" not in st.session_state:
    st.session_state.dispute_engine = DisputeEngine(disputes_log_path="disputes_log.json")

# Configure Streamlit page layout and custom themes
st.set_page_config(
    page_title="AI Service Orchestrator Dashboard",
    page_icon="⚡",
    layout="wide"
)

# inject premium custom CSS (emerald green & gold color system)
st.markdown("""
<style>
    :root {
        --primary-color: #0F5132; /* Emerald Green */
        --secondary-color: #FFD700; /* Gold Accent */
        --dark-bg: #121212;
        --card-bg: #1e1e1e;
        --text-color: #ffffff;
    }
    
    .stApp {
        background-color: #0e1117;
    }
    
    /* Header styling */
    .main-header {
        font-family: 'Outfit', sans-serif;
        color: #FFD700;
        text-align: center;
        margin-bottom: 2px;
        font-weight: 800;
        text-shadow: 1px 1px 10px rgba(15, 81, 50, 0.4);
    }
    
    .main-subheader {
        font-family: 'Outfit', sans-serif;
        color: #a0aec0;
        text-align: center;
        margin-bottom: 25px;
    }
    
    /* Elegant Cards */
    .premium-card {
        background: rgba(30, 30, 30, 0.6);
        border: 1px solid rgba(15, 81, 50, 0.3);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .premium-card:hover {
        border-color: rgba(255, 215, 0, 0.4);
        transform: translateY(-2px);
    }
    
    /* Badges */
    .badge-senior {
        background-color: #FFD700;
        color: #000000;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    
    .badge-inter {
        background-color: #0F5132;
        color: #ffffff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }
    
    .badge-junior {
        background-color: #4a5568;
        color: #ffffff;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }

    /* Sentiment badges */
    .sent-positive {
        background-color: #0F5132;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    
    .sent-neutral {
        background-color: #4a5568;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
    
    .sent-negative {
        background-color: #842029;
        color: #ffffff;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }

    /* Billing receipt */
    .receipt-container {
        font-family: 'Courier New', Courier, monospace;
        background: #111;
        border-left: 4px dashed #FFD700;
        border-right: 4px dashed #FFD700;
        padding: 20px;
        color: #00ff00;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    
    .receipt-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    
    .receipt-divider {
        border-bottom: 1px dashed #555;
        margin: 10px 0;
    }
    
    /* Notification */
    .sms-container {
        background-color: #1a202c;
        border-left: 4px solid #3182ce;
        padding: 15px;
        border-radius: 6px;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Admin Console reasoning trace */
    .admin-console-box {
        border: 2px dashed #FFD700;
        background-color: rgba(255, 215, 0, 0.03);
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
    }
    
    /* Tracking Timeline Stepper */
    .timeline-stepper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1e293b;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(15, 81, 50, 0.4);
        margin-bottom: 20px;
    }
    
    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 18%;
        position: relative;
    }
    
    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    .step-active {
        background-color: #FFD700;
        color: #000;
        box-shadow: 0 0 10px #FFD700;
    }
    
    .step-done {
        background-color: #0F5132;
        color: #fff;
    }
    
    .step-pending {
        background-color: #4a5568;
        color: #a0aec0;
    }
    
    .step-label {
        font-size: 12px;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Main Title Section
st.markdown("<h1 class='main-header'>⚡ AI SERVICE ORCHESTRATOR</h1>", unsafe_allow_html=True)
st.markdown("<p class='main-subheader'>Dynamic Matching, Dynamic Pricing, Calendar Scheduling, Status Tracking & Dispute Resolution in Islamabad</p>", unsafe_allow_html=True)

# Load Providers list dynamically from providers_db.json
providers_db = st.session_state.reputation_engine._load_providers()

# 👤 User Profile creation in sidebar
st.sidebar.markdown("### 👤 User Profile Settings")
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "name": "Maham Malik",
        "phone": "+92 300 1234567",
        "location": "Sector F-8, Islamabad",
        "risk_score": 0.1
    }

profile_name = st.sidebar.text_input("Name", value=st.session_state.user_profile["name"])
profile_phone = st.sidebar.text_input("Mobile Phone", value=st.session_state.user_profile["phone"])
profile_location = st.sidebar.selectbox("Sector Location (Islamabad)", [
    "Sector F-8, Islamabad",
    "DHA Phase 2, Islamabad",
    "Sector G-9, Islamabad",
    "Sector E-11, Islamabad",
    "Sector I-8, Islamabad"
], index=[
    "Sector F-8, Islamabad",
    "DHA Phase 2, Islamabad",
    "Sector G-9, Islamabad",
    "Sector E-11, Islamabad",
    "Sector I-8, Islamabad"
].index(st.session_state.user_profile["location"]))

profile_risk = st.sidebar.slider("Client Behavioral Risk Score", min_value=0.0, max_value=1.0, value=st.session_state.user_profile["risk_score"], step=0.05)

st.session_state.user_profile = {
    "name": profile_name,
    "phone": profile_phone,
    "location": profile_location,
    "risk_score": profile_risk
}

# Sidebar with Global Configs
st.sidebar.markdown("### ⚙️ Engine Parameters")
cost_km = st.sidebar.slider("Cost Per Kilometer (PKR)", min_value=10.0, max_value=100.0, value=50.0, step=5.0)
travel_base = st.sidebar.slider("Base Transport Fee (PKR)", min_value=50.0, max_value=300.0, value=100.0, step=10.0)
transit_buffer = st.sidebar.slider("Travel Transit Buffer (Mins)", min_value=15, max_value=60, value=30, step=5)

# Sync sidebar values to session state engines
st.session_state.pricing_engine.cost_per_km = cost_km
st.session_state.pricing_engine.base_travel_overhead = travel_base
st.session_state.scheduling_engine.buffer_minutes = transit_buffer

# Main Page Split Columns
col_left, col_right = st.columns([1, 1])

# Initialize session variables for inputs if not present
if "user_query" not in st.session_state:
    st.session_state.user_query = ""
if "selected_urgency" not in st.session_state:
    st.session_state.selected_urgency = "Medium"
if "selected_complexity" not in st.session_state:
    st.session_state.selected_complexity = "Intermediate"
if "selected_distance" not in st.session_state:
    st.session_state.selected_distance = 0.0
if "active_job_id" not in st.session_state:
    st.session_state.active_job_id = None
if "active_provider" not in st.session_state:
    st.session_state.active_provider = None

# ----------------- LEFT COLUMN: NLU INTENT & PROVIDER MATCHING -----------------
with col_left:
    st.markdown("### 🗣️ Step 1: User Request (NLU Intent)")
    
    # Pre-set scenario templates
    st.markdown("**Select a Roman Urdu preset or write your own:**")
    preset_col1, preset_col2 = st.columns(2)
    
    with preset_col1:
        if st.button("🚨 Emergency Electricity Fault", use_container_width=True):
            st.session_state.user_query = "bhai mere ghar ki light chali gayi hai jaldi aao emergency hai, F-8 Islamabad"
            st.session_state.selected_urgency = "Emergency"
            st.session_state.selected_complexity = "Intermediate"
    with preset_col2:
        if st.button("📆 Sunday Scheduled Car Wash", use_container_width=True):
            st.session_state.user_query = "yar gari dhoni hai sunday ko aam time mein, DHA Phase 2"
            st.session_state.selected_urgency = "Low"
            st.session_state.selected_complexity = "Basic"
            
    # Text input for query
    query_text = st.text_input("Raw Input Message (English, Urdu, Roman Urdu)", value=st.session_state.user_query)
    
    # Simulated NLU Intent Extraction result
    st.markdown("#### ⚡ Extracted NLU Intent")
    
    nlu_col1, nlu_col2, nlu_col3 = st.columns(3)
    with nlu_col1:
        urgency_options = ["Low", "Medium", "High", "Emergency"]
        urgency = st.selectbox("Urgency Level", urgency_options, index=urgency_options.index(st.session_state.selected_urgency))
    with nlu_col2:
        complexity_options = ["Basic", "Intermediate", "Complex"]
        complexity = st.selectbox("Job Complexity", complexity_options, index=complexity_options.index(st.session_state.selected_complexity))
    with nlu_col3:
        booking_hour = st.slider("Booking Hour (0-23)", min_value=0, max_value=23, value=12)

    # Resolve parsed service type based on query
    query_lower = query_text.lower()
    if "light" in query_lower or "electric" in query_lower or "bijli" in query_lower:
        resolved_service = "electrician"
    elif "plumb" in query_lower or "pipe" in query_lower or "leak" in query_lower or "sewer" in query_lower:
        resolved_service = "plumbing"
    elif "ac" in query_lower or "cooling" in query_lower or "ref" in query_lower:
        resolved_service = "ac repair"
    else:
        resolved_service = "electrician" # Fallback

    st.info(f"Normalised Service Intent Detected: **{resolved_service.upper()}**")

    # Match and rank providers
    st.markdown("### 🏆 Step 2: Multi-Factor Provider Ranking")
    
    # Pre-filter providers by specialty type
    specialized_providers = []
    for p in providers_db:
        name_lower = p["name"].lower()
        if resolved_service == "electrician" and "electrician" in name_lower:
            specialized_providers.append(p)
        elif resolved_service == "plumbing" and "plumber" in name_lower:
            specialized_providers.append(p)
        elif resolved_service == "ac repair" and "ac" in name_lower:
            specialized_providers.append(p)
        else:
            specialized_providers.append(p)

    job_ctx = {
        "required_skill_level": complexity,
        "complexity": complexity,
        "user_risk_score": st.session_state.user_profile["risk_score"],
        "urgency": urgency,
        "booking_hour": booking_hour
    }

    # Execute ranking engine
    ranked_list = st.session_state.ranking_engine.rank_providers(job_ctx, specialized_providers)

    st.markdown("Select a provider below to calculate dynamic pricing:")
    
    selected_prov_id = None
    for idx, p in enumerate(ranked_list):
        experience = p.get("experience_level", "Intermediate")
        badge_style = "badge-senior" if experience == "Senior" else ("badge-inter" if experience == "Intermediate" else "badge-junior")
        
        # Structure card columns
        with st.container():
            col_p1, col_p2, col_p3 = st.columns([2, 2, 1])
            with col_p1:
                st.markdown(f"**{idx+1}. {p['name']}**")
                st.markdown(f"<span class='{badge_style}'>{experience} Expert</span> | ⭐ {p['rating']:.2f} ({p['user_ratings_total']} reviews)", unsafe_allow_html=True)
            with col_p2:
                st.markdown(f"📍 Distance: **{p['distance_km']} km** ({p['travel_time_mins']} mins away)")
                st.markdown(f"📈 Reliability Rating: **{(p['on_time_rate']*100):.1f}%**")
            with col_p3:
                if st.button("Select Match", key=f"sel_{p['id']}"):
                    st.session_state.selected_provider = p
                    selected_prov_id = p["id"]

    # Set default selected provider if none chosen yet
    if "selected_provider" not in st.session_state and ranked_list:
        st.session_state.selected_provider = ranked_list[0]

    # Comparative Matrix Section
    st.markdown("#### 📊 Side-by-Side Provider Factor Comparison")
    comparison_rows = []
    for p in ranked_list:
        comp_price = st.session_state.pricing_engine.calculate_pricing(p, {
            "urgency": urgency,
            "complexity": complexity,
            "booking_hour": booking_hour
        })
        comparison_rows.append({
            "Specialist Name": p["name"],
            "Experience Tier": p["experience_level"],
            "Distance (km)": f"{p['distance_km']} km",
            "ETA (minutes)": f"{p['travel_time_mins']} mins",
            "Average Rating": f"⭐ {p['rating']:.2f} ({p['user_ratings_total']})",
            "On-Time Rate (%)": f"{(p['on_time_rate']*100):.1f}%",
            "Calculated Cost": f"Rs. {comp_price['final_total']:.2f}"
        })
    df_comparison = pd.DataFrame(comparison_rows)
    st.dataframe(df_comparison, use_container_width=True)

# ----------------- RIGHT COLUMN: DYNAMIC PRICING & BOOKING -----------------
with col_right:
    st.markdown("### 💰 Step 3: Transparent Dynamic Pricing")
    
    if "selected_provider" in st.session_state:
        # Load up to date stats from database rather than cached session copy
        prov_cached = st.session_state.selected_provider
        prov = next((p for p in providers_db if p["id"] == prov_cached["id"]), prov_cached)
        
        # Override distance slider to allow manual tuning for pricing demo
        manual_distance = st.slider("Tweak Travel Distance manually for demonstration (km)", min_value=0.0, max_value=30.0, value=float(prov["distance_km"]), step=0.5)
        prov_override = prov.copy()
        prov_override["distance_km"] = manual_distance
        
        # Setup trigger parameters in job_context for real-time recalculations
        current_job_context = {
            "urgency": urgency,
            "complexity": complexity,
            "booking_hour": booking_hour
        }
        
        # Handle stateful interactive "Apply Alternative Suggestion" updates
        if "applied_alternative" in st.session_state and st.session_state.applied_alternative:
            alt = st.session_state.applied_alternative
            if alt["type"] == "time_shift":
                current_job_context["urgency"] = "Medium"
                current_job_context["booking_hour"] = 12
                st.warning("⚠️ Applied: Shifting schedule to Standard Daytime hours to save surcharges!")
            elif alt["type"] == "tier_shift":
                prov_override["base_rate"] = 750.0
                prov_override["experience_level"] = "Junior"
                st.warning("⚠️ Applied: Swapped provider experience tier to Junior/Standard to save base fees!")
            elif alt["type"] == "proximity_shift":
                prov_override["distance_km"] = 2.0
                st.warning("⚠️ Applied: Swapped to a closer nearby provider (2km range)!")

        # Execute dynamic pricing calculations
        price_analysis = st.session_state.pricing_engine.calculate_pricing(prov_override, current_job_context)
        
        # Display elegant, structured pricing receipt
        st.markdown(f"#### 💳 Invoice Receipt: {price_analysis['provider_name']} ({price_analysis['provider_tier']})")
        
        st.markdown(f"""
        <div class='receipt-container'>
            <div style='text-align: center; font-weight: bold;'>--- AI SEEKHO ORCHESTRATOR INVOICE ---</div>
            <div style='text-align: center; font-size: 11px; color: #888;'>Islamabad, Pakistan</div>
            <div class='receipt-divider'></div>
            <div class='receipt-row'>
                <span>1. {price_analysis['line_items']['base_fee']['label_en']}</span>
                <span>Rs. {price_analysis['line_items']['base_fee']['amount']:.2f}</span>
            </div>
            <div style='font-size: 11px; color: #888;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['base_fee']['description_en']}</div>
            <div style='font-size: 11px; color: #ffd700;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['base_fee']['description_ur']}</div>
            
            <div class='receipt-row' style='margin-top: 10px;'>
                <span>2. {price_analysis['line_items']['distance_cost']['label_en']}</span>
                <span>Rs. {price_analysis['line_items']['distance_cost']['amount']:.2f}</span>
            </div>
            <div style='font-size: 11px; color: #888;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['distance_cost']['description_en']}</div>
            <div style='font-size: 11px; color: #ffd700;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['distance_cost']['description_ur']}</div>
            
            <div class='receipt-row' style='margin-top: 10px;'>
                <span>3. {price_analysis['line_items']['urgency_surcharge']['label_en']}</span>
                <span>Rs. {price_analysis['line_items']['urgency_surcharge']['amount']:.2f}</span>
            </div>
            <div style='font-size: 11px; color: #888;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['urgency_surcharge']['description_en']}</div>
            <div style='font-size: 11px; color: #ffd700;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['urgency_surcharge']['description_ur']}</div>

            <div class='receipt-row' style='margin-top: 10px;'>
                <span>4. {price_analysis['line_items']['time_surcharge']['label_en']}</span>
                <span>Rs. {price_analysis['line_items']['time_surcharge']['amount']:.2f}</span>
            </div>
            <div style='font-size: 11px; color: #888;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['time_surcharge']['description_en']}</div>
            <div style='font-size: 11px; color: #ffd700;'>&nbsp;&nbsp;&nbsp;{price_analysis['line_items']['time_surcharge']['description_ur']}</div>
            
            <div class='receipt-divider'></div>
            <div class='receipt-row' style='font-size: 14px; font-weight: bold;'>
                <span>SUBTOTAL (Bunyadi Kharcha):</span>
                <span>Rs. {price_analysis['subtotal']:.2f}</span>
            </div>
            <div class='receipt-row' style='font-size: 14px; font-weight: bold;'>
                <span>TOTAL SURCHARGES (Izafi Kharcha):</span>
                <span>Rs. {price_analysis['surcharges_total']:.2f}</span>
            </div>
            <div class='receipt-row' style='font-size: 18px; font-weight: bold; color: #FFD700;'>
                    <span>TOTAL INVOICE (Kul Kharcha):</span>
                    <span>Rs. {price_analysis['final_total']:.2f}</span>
                </div>
                <div class='receipt-divider'></div>
                <div style='text-align: center; font-size: 10px; color: #666;'>Toll adjustments are inclusive. Thank you!</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Reset Applied Alternatives
        if "applied_alternative" in st.session_state and st.session_state.applied_alternative:
            if st.button("Reset back to Original Pricing Engine Config"):
                st.session_state.applied_alternative = None
                st.rerun()

        # Display alternatives
        st.markdown("### 💡 Step 4: Budget-Friendly Alternatives (Paise Bachayein!)")
        
        for alt in price_analysis["budget_alternatives"]:
            with st.container():
                st.markdown(f"""
                <div style='background: rgba(15, 81, 50, 0.15); border: 1px solid rgba(255,215,0,0.2); border-radius: 8px; padding: 12px; margin-bottom: 10px;'>
                    <div style='display: flex; justify-content: space-between;'>
                        <strong style='color: #FFD700;'>💡 {alt['title_en']} ({alt['title_ur']})</strong>
                        <span style='color: #00ff00; font-weight: bold;'>Save Rs. {alt['potential_savings']:.2f}</span>
                    </div>
                    <div style='font-size: 12px; color: #ccc; margin-top: 5px;'>{alt['description_en']}</div>
                    <div style='font-size: 12px; color: #ffd700;'>{alt['description_ur']}</div>
                    <div style='font-size: 13px; font-weight: bold; color: #fff; margin-top: 5px;'>New Price: Rs. {alt['new_total']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
                is_applied = False
                if "applied_alternative" in st.session_state and st.session_state.applied_alternative:
                    if st.session_state.applied_alternative["type"] == alt["type"]:
                        is_applied = True
                        
                if not is_applied:
                    if st.button(f"Apply Option: {alt['title_en']}", key=f"btn_alt_{alt['type']}"):
                        st.session_state.applied_alternative = alt
                        st.rerun()

        # ----------------- CALENDAR BOOKING -----------------
        st.markdown("### 📅 Step 5: Transit-Buffered Calendar Booking")
        
        tomorrow = dt.date.today() + dt.timedelta(days=1)
        selected_date = st.date_input("Select Service Date", value=tomorrow)
        
        is_emerg = current_job_context["urgency"].lower() == "emergency"
        slots = st.session_state.scheduling_engine.get_available_slots(
            provider_id=prov["id"],
            date=selected_date,
            is_emergency=is_emerg
        )
        
        if slots:
            slot_labels = [s.strftime("%I:%M %p") for s in slots]
            selected_slot_str = st.selectbox("Select Start Time Slot (30m travel buffer is pre-allocated)", slot_labels)
            
            chosen_slot = slots[slot_labels.index(selected_slot_str)]
            contact_number = st.text_input("Enter Mobile Number (for booking SMS)", value=st.session_state.user_profile["phone"])
            
            if st.button("🔥 Confirm and Book Appointment Now!", type="primary", use_container_width=True):
                new_job_id = f"JOB-{dt.datetime.now().strftime('%M%S')}"
                booking_result = st.session_state.scheduling_engine.book_slot(
                    provider_id=prov["id"],
                    provider_name=prov["name"],
                    job_id=new_job_id,
                    start_time=chosen_slot,
                    duration_mins=60,
                    user_contact=contact_number,
                    urgency=current_job_context["urgency"].capitalize(),
                    location=st.session_state.user_profile["location"],
                    price=price_analysis["final_total"]
                )
                
                if booking_result["success"]:
                    st.success("🎉 Booking Confirmed successfully in the Calendar Engine!")
                    
                    # Set active stateful job tracker variables!
                    st.session_state.active_job_id = new_job_id
                    st.session_state.active_provider = prov
                    
                    # Log initial PENDING and ACCEPTED states in the TrackingEngine!
                    st.session_state.tracking_engine.update_status(
                        job_id=new_job_id,
                        provider_id=prov["id"],
                        provider_name=prov["name"],
                        new_status=st.session_state.tracking_engine.PENDING,
                        location=st.session_state.user_profile["location"]
                    )
                    st.session_state.tracking_engine.update_status(
                        job_id=new_job_id,
                        provider_id=prov["id"],
                        provider_name=prov["name"],
                        new_status=st.session_state.tracking_engine.ACCEPTED,
                        location=st.session_state.user_profile["location"]
                    )
                    st.rerun() # Refresh to display tracker
                else:
                    st.error(f"❌ Booking Overlap Mismatch: {booking_result.get('error_message')}")
        else:
            st.error("No slots are available on this date.")
    else:
        st.info("Please select a provider from the left panel.")

# ----------------- REAL-TIME TIMELINE TRACKING WORKFLOW -----------------
st.markdown("---")
st.markdown("### 🗺️ Step 6: Real-time Live Status Tracking, Reputation & Disputes")

if st.session_state.active_job_id:
    job_id = st.session_state.active_job_id
    prov_cached = st.session_state.active_provider
    prov = next((p for p in providers_db if p["id"] == prov_cached["id"]), prov_cached)
    tracker = st.session_state.tracking_engine
    
    current_status = tracker.get_latest_status(job_id)
    history = tracker.get_job_history(job_id)
    latest_event = history[-1] if history else None
    
    # Calculate circle styles based on state
    states_list = [tracker.PENDING, tracker.ACCEPTED, tracker.EN_ROUTE, tracker.STARTED, tracker.COMPLETED]
    labels_en = ["Pending Request", "Provider Matched", "Provider En Route", "Job Started", "Job Completed"]
    labels_ur = ["Kaam Darj", "Maahir Qabool", "Maahir Raste Mein", "Kaam Shuru", "Kaam Mukammal"]
    
    current_index = states_list.index(current_status) if current_status in states_list else -1
    
    # Render stepper timeline html
    stepper_html = "<div class='timeline-stepper'>"
    for i, state in enumerate(states_list):
        if i < current_index:
            circle_class = "step-circle step-done"
            symbol = "✓"
        elif i == current_index:
            circle_class = "step-circle step-active"
            symbol = "⚡"
        else:
            circle_class = "step-circle step-pending"
            symbol = str(i+1)
            
        stepper_html += f"""
        <div class='step-item'>
            <div class='{circle_class}'>{symbol}</div>
            <div class='step-label' style='color: {"#FFD700" if i==current_index else "#fff"};'>{labels_en[i]}</div>
            <div class='step-label' style='font-size: 10px; color: {"#FFD700" if i==current_index else "#ffd700"};'>{labels_ur[i]}</div>
        </div>
        """
    stepper_html += "</div>"
    st.markdown(stepper_html, unsafe_allow_html=True)

    # Split timeline layout
    track_col1, track_col2 = st.columns([1, 1])
    
    with track_col1:
        st.markdown("**🎮 Simulator Panel (Advance Workflow Status):**")
        
        if current_status == tracker.CANCELLED:
            st.error("❌ **BOOKING CANCELED:** Appointment has been cancelled in real-time. Travel and transit slots are released.")
            if st.button("🗑️ Delete Canceled Booking From Calendar"):
                st.session_state.scheduling_engine.delete_booking(job_id)
                st.session_state.active_job_id = None
                st.session_state.active_provider = None
                st.success("Canceled booking record successfully purged from schedules.")
                st.rerun()

        if current_status == tracker.ACCEPTED:
            eta = st.slider("Set Provider Travel ETA (Minutes)", min_value=5, max_value=60, value=15, step=5)
            if st.button("Start Traveling (Simulate Provider En Route) ➡️"):
                tracker.update_status(
                    job_id=job_id,
                    provider_id=prov["id"],
                    provider_name=prov["name"],
                    new_status=tracker.EN_ROUTE,
                    location=st.session_state.user_profile["location"],
                    eta_minutes=eta
                )
                st.rerun()
                
        elif current_status == tracker.EN_ROUTE:
            if st.button("Start Service Work (Simulate Job Started) ⚙️"):
                tracker.update_status(
                    job_id=job_id,
                    provider_id=prov["id"],
                    provider_name=prov["name"],
                    new_status=tracker.STARTED,
                    location=st.session_state.user_profile["location"]
                )
                st.rerun()
                
        elif current_status == tracker.STARTED:
            if st.button("Finish Service Delivery (Simulate Job Completed) ✅"):
                tracker.update_status(
                    job_id=job_id,
                    provider_id=prov["id"],
                    provider_name=prov["name"],
                    new_status=tracker.COMPLETED,
                    location=st.session_state.user_profile["location"]
                )
                st.rerun()
                
        elif current_status in [tracker.COMPLETED, tracker.CANCELLED]:
            st.success("🎉 This job is fully finalized! Thank you.")
            
            # --- POST-SERVICE RATING ENGINE MODULE ---
            st.markdown("### ⭐ Post-Service Customer Feedback & Reputation")
            
            rating_key = f"feedback_submitted_{job_id}"
            dispute_key = f"dispute_filed_{job_id}"
            
            # Show feedback panel if not rated yet
            if rating_key not in st.session_state:
                with st.container():
                    st.markdown("""
                    <div style='background: rgba(255,215,0,0.05); border: 1px solid rgba(255,215,0,0.3); border-radius: 8px; padding: 15px; margin-top: 10px;'>
                        <strong style='color: #FFD700;'>Rate Zafar's Work (Feedback Form):</strong><br/>
                        Share your experience to update provider rankings in Islamabad.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    star_val = st.slider("Star Rating", min_value=1.0, max_value=5.0, value=5.0, step=1.0)
                    review_msg = st.text_area("Written Review (English or Roman Urdu, e.g. 'bohot acha aur fast kaam kiya')", value="bohot acha aur professional electrician, shukriya!")
                    
                    # Manual toggle checkbox to trigger dispute intake directly
                    raise_manual_disp = st.checkbox("🚨 File an Operational Dispute / Complaint (Poor Quality or Price Disagreement)")
                    
                    if st.button("Submit Feedback & Update Reputation Engine"):
                        # Submit and process rating & sentiment analysis
                        fed_res = st.session_state.reputation_engine.submit_feedback(
                            job_id=job_id,
                            provider_id=prov["id"],
                            rating=star_val,
                            review_text=review_msg
                        )
                        if fed_res["success"]:
                            st.session_state[rating_key] = fed_res
                            st.toast("🎉 Reputation system updated statefully!")
                            
                            # Automatically auto-trigger dispute state if rating is low
                            if star_val <= 2.0 or raise_manual_disp:
                                st.session_state[f"force_dispute_intake_{job_id}"] = {
                                    "auto_category": "Poor Quality" if star_val <= 2.0 else "Price Disagreement",
                                    "auto_details": review_msg
                                }
                            st.rerun()
            else:
                fed_res = st.session_state[rating_key]
                sent_lbl = fed_res["sentiment_label"]
                sent_class = "sent-positive" if sent_lbl == "Positive" else ("sent-neutral" if sent_lbl == "Neutral" else "sent-negative")
                
                # Render results
                st.markdown(f"""
                <div style='background: rgba(15,81,50,0.1); border: 1px solid rgba(15,81,50,0.4); border-radius: 10px; padding: 20px; margin-top: 15px;'>
                    <h5 style='color: #FFD700; margin-top:0;'>📊 Feedback Logged & Analyzed!</h5>
                    <div style='margin-bottom: 10px;'>
                        <strong>Sentiment Parsed:</strong> 
                        <span class='{sent_class}'>{sent_lbl} (Score: {fed_res['sentiment_score']})</span>
                    </div>
                    <div style='font-size: 13px; color: #ccc; margin-bottom: 15px;'>
                        <i>" {fed_res['review_record']['review_text']} "</i>
                    </div>
                    <div style='border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 10px;'>
                        <strong>📈 Provider Average Rating Shift:</strong><br/>
                        {fed_res['rating_delta']['old_rating']:.2f} ➡️ <span style='color: #00ff00; font-weight:bold;'>{fed_res['rating_delta']['new_rating']:.2f}</span> (Total reviews: {fed_res['rating_delta']['total_reviews']})
                    </div>
                    <div style='margin-top: 8px;'>
                        <strong>🛡️ Provider Reliability Coefficient Shift:</strong><br/>
                        {(fed_res['reliability_delta']['old_reliability']*100):.1f}% ➡️ <span style='color: #00ff00; font-weight:bold;'>{(fed_res['reliability_delta']['new_reliability']*100):.1f}%</span> 
                        (Adjustment: <span style='color: {"#00ff00" if fed_res['reliability_delta']['adjustment'] >= 0 else "#ff0000"};'>{(fed_res['reliability_delta']['adjustment']*100):+.1f}%</span>)
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # --- DISPUTE RESOLUTION PROTOCOL ENGINE (NEW!) ---
            force_intake_key = f"force_dispute_intake_{job_id}"
            
            if (force_intake_key in st.session_state or st.session_state.get(dispute_key)) and dispute_key not in st.session_state:
                st.markdown("### 🚨 Ingest Operational Dispute Protocol")
                
                intake_defaults = st.session_state.get(force_intake_key, {"auto_category": "Poor Quality", "auto_details": ""})
                
                with st.container():
                    st.warning("⚠️ Critical Dispute logged. Please choose the category to generate platform reasoning traces.")
                    
                    disp_category = st.selectbox("Dispute Category", [DisputeEngine.POOR_QUALITY, DisputeEngine.PRICE_DISAGREEMENT], index=0 if intake_defaults["auto_category"] == "Poor Quality" else 1)
                    disp_complaint = st.text_area("Detailed Customer Complaint", value=intake_defaults["auto_details"] if intake_defaults["auto_details"] else "Technician did not execute the service correctly.")
                    
                    if st.button("🔥 Submit Dispute Ticket & File Platform Escalation"):
                        # Submit and process dispute ticket lodging
                        tkt_res = st.session_state.dispute_engine.raise_dispute(
                            job_id=job_id,
                            provider_id=prov["id"],
                            provider_name=prov["name"],
                            customer_contact=contact_number if 'contact_number' in locals() else "+923001234567",
                            category=disp_category,
                            customer_complaint=disp_complaint,
                            billing_info=price_analysis,
                            provider_stats=prov
                        )
                        st.session_state[dispute_key] = tkt_res
                        st.toast("🚨 Escalation logged to database!")
                        st.rerun()
            elif dispute_key in st.session_state:
                tkt = st.session_state[dispute_key]
                
                st.markdown("### 🚨 Support Dispute Filed & Escycled!")
                
                # Render bilingual Customer SMS trigger acknowledgement
                st.markdown(f"""
                <div class='sms-container' style='background-color: #1c1c1c; border-left: 4px solid #b7791f; margin-bottom: 15px;'>
                    <div style='color: #FFD700; font-weight: bold; border-bottom: 1px solid rgba(255,215,0,0.3); padding-bottom: 5px; margin-bottom: 8px;'>💬 CUSTOMER DISPUTE TICKET ACKNOWLEDGEMENT (Bilingual)</div>
                    <div style='font-size: 12px; margin-bottom: 5px;'><strong>[English]:</strong> {tkt['notifications']['english']}</div>
                    <div style='font-size: 12px; color: #ffd700;'><strong>[Roman Urdu]:</strong> {tkt['notifications']['roman_urdu']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render platform administrator reasoning trace & recommendation card!
                risk_style = "color: #ff0000; font-weight: bold;" if tkt["risk_level"] == "High" else "color: #00ff00; font-weight: bold;"
                
                st.markdown(f"""
                <div class='admin-console-box'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <strong style='color:#FFD700; font-size:15px;'>🛡️ PLATFORM ADMIN RESOLUTION CONSOLE</strong>
                        <span>Risk level: <strong style='{risk_style}'>{tkt['risk_level']} Risk</strong></span>
                    </div>
                    <div style='font-size:11px; color:#888; margin-bottom:10px;'>Ticket ID: {tkt['ticket_id']} | Persisted to disputes_log.json</div>
                    
                    <strong style='font-size:13px; color:#fff;'>📋 Administrative Reasoning Audit Trace:</strong>
                    <pre style='background:#111; color:#00ff00; border-radius:5px; padding:10px; font-size:12px; overflow-x:auto; margin-top:5px;'>{tkt['reasoning_trace']}</pre>
                    
                    <div style='background:rgba(255,215,0,0.1); border-left:4px solid #FFD700; padding:10px; margin-top:10px;'>
                        <strong style='color:#FFD700; font-size:13px;'>🤖 Actionable Platform Recommendation:</strong><br/>
                        <span style='font-size:12px; color:#fff;'>{tkt['admin_recommendation']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("Book Another Job / Reset Simulator", key="btn_reset_timeline"):
                st.session_state.active_job_id = None
                st.session_state.active_provider = None
                st.session_state.pop(force_intake_key, None)
                st.rerun()

        # Cancellation Trigger
        if current_status not in [tracker.COMPLETED, tracker.CANCELLED]:
            if st.button("❌ Cancel Appointment (Trigger Cancellation)"):
                tracker.update_status(
                    job_id=job_id,
                    provider_id=prov["id"],
                    provider_name=prov["name"],
                    new_status=tracker.CANCELLED,
                    location=st.session_state.user_profile["location"]
                )
                st.rerun()

    with track_col2:
        if latest_event:
            st.markdown(f"**📱 Live Customer Alert Triggered: ({latest_event['status']})**")
            
            # Format elegant notification popup
            st.markdown(f"""
            <div class='sms-container'>
                <div style='color: #FFD700; font-weight: bold; border-bottom: 1px solid rgba(255,215,0,0.3); padding-bottom: 5px; margin-bottom: 8px;'>💬 TIMELINE SMS NOTIFICATION PAYLOAD (Bilingual)</div>
                <div style='font-size: 13px; margin-bottom: 10px;'>
                    <strong>[English]:</strong><br/>
                    {latest_event['notifications']['english']}
                </div>
                <div style='font-size: 13px; color: #ffd700;'>
                    <strong>[Roman Urdu]:</strong><br/>
                    {latest_event['notifications']['roman_urdu']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display notes
            st.info(f"📋 **System Log Event:** {latest_event['notes_en']}")
else:
    st.info("No active booked job is running in the tracking workflow. Place a calendar booking above to launch the tracking timeline simulator!")

# Active Calendar Visualizer
st.markdown("---")
st.markdown("### 🗂️ Calendar Schedule (Live Overlap Buffer Visualization)")

# Gather current bookings
booking_rows = []
for p_id, bookings in st.session_state.scheduling_engine.provider_calendars.items():
    p_name = next((p["name"] for p in providers_db if p["id"] == p_id), "Unknown")
    for b in bookings:
        booking_rows.append({
            "Provider Name": p_name,
            "Job ID": b["job_id"],
            "Start Time": b["start"].strftime("%Y-%m-%d %I:%M %p"),
            "End Time": b["end"].strftime("%Y-%m-%d %I:%M %p"),
            "Buffered Transit Ends": (b["end"] + timedelta(minutes=st.session_state.scheduling_engine.buffer_minutes)).strftime("%I:%M %p"),
            "Urgency": b["urgency"],
            "Estimated Bill": f"Rs. {b['price']:.2f}",
            "User Contact": b["user_contact"]
        })

if booking_rows:
    df_bookings = pd.DataFrame(booking_rows)
    st.dataframe(df_bookings, use_container_width=True)
    
    # 🗑️ Manage Past Booking Data - Purging options
    st.markdown("**🗑️ Manage Booking Records:**")
    del_col1, del_col2 = st.columns([3, 1])
    with del_col1:
        job_ids = [row["Job ID"] for row in booking_rows]
        selected_job_to_del = st.selectbox("Select Booking Record to Delete", job_ids, key="sel_del_booking")
    with del_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Delete Record", use_container_width=True):
            st.session_state.scheduling_engine.delete_booking(selected_job_to_del)
            # Clear active trackers if matching
            if st.session_state.active_job_id == selected_job_to_del:
                st.session_state.active_job_id = None
                st.session_state.active_provider = None
            st.success(f"Purged record {selected_job_to_del} successfully!")
            st.rerun()
else:
    st.info("The schedules are currently empty.")
