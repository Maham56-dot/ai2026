import sys
from datetime import datetime, timedelta
from nlu_module import IntentExtraction
from ranking_engine import RankingEngine
from pricing_engine import PricingEngine
from scheduling_engine import SchedulingEngine
from tracking_engine import TrackingEngine
from reputation_engine import ReputationEngine
from dispute_engine import DisputeEngine


def run_orchestrator_demo():
    print("=" * 60)
    print("⚡ AI SERVICE ORCHESTRATOR - END-TO-END BILINGUAL DEMO ⚡")
    print("=" * 60)
    
    # 1. Initialize Engines
    scheduler = SchedulingEngine(buffer_minutes=30)
    pricing = PricingEngine(cost_per_km=50.0, base_travel_overhead=100.0)
    ranking = RankingEngine()

    # Mock Database of service providers in Islamabad
    mock_providers = [
        {
            "id": "prov_01",
            "name": "Zafar Ali (Electrician)",
            "experience_level": "Senior",
            "base_rate": 1500.0,
            "distance_km": 2.4,
            "travel_time_mins": 8.0,
            "availability": "available_now",
            "skill_level": "Complex",
            "on_time_rate": 0.98,
            "rating": 4.9,
            "user_ratings_total": 42
        },
        {
            "id": "prov_02",
            "name": "Yasir Plumber (Sewerage Expert)",
            "experience_level": "Intermediate",
            "base_rate": 1000.0,
            "distance_km": 7.8,
            "travel_time_mins": 22.0,
            "availability": "available_soon",
            "skill_level": "Intermediate",
            "on_time_rate": 0.92,
            "rating": 4.6,
            "user_ratings_total": 29
        },
        {
            "id": "prov_03",
            "name": "Kamran Electricians",
            "experience_level": "Junior",
            "base_rate": 750.0,
            "distance_km": 8.9,
            "travel_time_mins": 25.0,
            "availability": "busy",
            "skill_level": "Basic",
            "on_time_rate": 0.85,
            "rating": 4.0,
            "user_ratings_total": 9
        }
    ]

    # 2. Simulate NLU intent parsing of a Roman Urdu request
    user_complaint = "bhai mere ghar ki light chali gayi hai jaldi aao emergency hai, F-8 Islamabad"
    print(f"\n[Step 1] Customer Raw Complaint (Urdu/English Roman Urdu):\n  --> \"{user_complaint}\"")
    
    # Mock NLU extraction representing the NLU module's output
    nlu_intent = IntentExtraction(
        service_type="Electrician",
        location="F-8 Islamabad",
        urgency="Emergency",
        preferred_time="Immediate",
        complexity="Intermediate"
    )
    
    print("\n[Step 2] Robust NLU Intent Parsing Output:")
    print(f"  - Detected Service: {nlu_intent.service_type}")
    print(f"  - Location Parsed:  {nlu_intent.location}")
    print(f"  - Urgency Level:    {nlu_intent.urgency}")
    print(f"  - Job Complexity:   {nlu_intent.complexity}")

    # 3. Dynamic Ranking of suitable Providers
    job_context = {
        "required_skill_level": nlu_intent.complexity,
        "complexity": nlu_intent.complexity,
        "user_risk_score": 0.1,
        "urgency": nlu_intent.urgency,
        "booking_hour": 21 # 9 PM (night/peak surcharge hour)
    }

    print("\n[Step 3] Executing Multi-Factor Provider Ranking Engine...")
    ranked_providers = ranking.rank_providers(job_context, mock_providers)
    
    for idx, p in enumerate(ranked_providers, 1):
        print(f"  {idx}. {p['name']} | Score: {p['ranking_score']:.3f} | Distance: {p['distance_km']}km | Rating: {p['rating']}")

    # Select the top match
    matched_provider = ranked_providers[0]
    print(f"\nMatched Top Provider: {matched_provider['name']}")

    # 4. Dynamic Pricing Calculation with Billing Transparency & Alternatives
    print("\n[Step 4] Calculating Dynamic Pricing Invoice Breakdown...")
    price_breakdown = pricing.calculate_pricing(matched_provider, job_context)
    
    print("-" * 55)
    print(f"RECEIPT FOR: {price_breakdown['provider_name']} ({price_breakdown['provider_tier']})")
    print("-" * 55)
    for key, item in price_breakdown["line_items"].items():
        print(f"{item['label_en']} ({item['label_ur']}):")
        print(f"  PKR {item['amount']:.2f} | {item['description_en']}")
    print("-" * 55)
    print(f"Bunyadi Cost (Subtotal):      PKR {price_breakdown['subtotal']:.2f}")
    print(f"Izafi Cost (Surcharges):      PKR {price_breakdown['surcharges_total']:.2f}")
    print(f"KUL KHARCHA (FINAL BILL):     PKR {price_breakdown['final_total']:.2f}")
    print("-" * 55)

    print("\n[Step 5] Suggesting Budget-Friendly Alternatives (Paise Bachayein):")
    for idx, alt in enumerate(price_breakdown["budget_alternatives"], 1):
        print(f"  Option {idx}: {alt['title_en']} ({alt['title_ur']})")
        print(f"    New Price: PKR {alt['new_total']:.2f} (Save PKR {alt['potential_savings']:.2f}!)")
        print(f"    Detail:    {alt['description_en']}")

    # 5. Scheduling & Booking with Transit Buffer Overlap Checks
    print("\n[Step 6] Booking Slot in the Provider Calendar Engine...")
    tomorrow = datetime.now() + timedelta(days=1)
    # Book at 10:00 AM tomorrow
    booking_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    j_id = "JOB-" + datetime.now().strftime("%M%S") # Dynamic Job ID to prevent transition locks on re-run
    
    booking_res = scheduler.book_slot(
        provider_id=matched_provider["id"],
        provider_name=matched_provider["name"],
        job_id=j_id,
        start_time=booking_time,
        duration_mins=60,
        user_contact="+923001234567",
        urgency=job_context["urgency"].capitalize(),
        location=nlu_intent.location,
        price=price_breakdown["final_total"]
    )
    
    if booking_res["success"]:
        print("  🎉 Calendar booking successfully finalized!")
        print("\n[Step 7] Automated Bilingual WhatsApp/SMS Confirmed Notification:")
        print(f"  --- [English] ---")
        print(booking_res["notifications"]["english"])
        print(f"\n  --- [Roman Urdu] ---")
        print(booking_res["notifications"]["roman_urdu"])
        
        # --- Simulate Real-time Status Tracking workflow (NEW!) ---
        print("\n" + "=" * 60)
        print("🛰️ REAL-TIME PROVIDER STATUS TRACKING SIMULATION")
        print("=" * 60)
        
        tracker = TrackingEngine(log_path="tracking_log.json")
        p_id = matched_provider["id"]
        p_name = matched_provider["name"]
        
        # 1. PENDING & ACCEPTED (logged on creation)
        tracker.update_status(j_id, p_id, p_name, tracker.PENDING, location=nlu_intent.location)
        ev_accept = tracker.update_status(j_id, p_id, p_name, tracker.ACCEPTED, location=nlu_intent.location)
        print(f"\n📌 Status Update: [{ev_accept['status']}]")
        print(f"  System Event: {ev_accept['notes_en']}")
        print(f"  SMS Roman Urdu:\n  {ev_accept['notifications']['roman_urdu']}")
        
        # 2. EN ROUTE (with ETA 15 minutes)
        ev_enroute = tracker.update_status(j_id, p_id, p_name, tracker.EN_ROUTE, location=nlu_intent.location, eta_minutes=15)
        print(f"\n📌 Status Update: [{ev_enroute['status']}]")
        print(f"  System Event: {ev_enroute['notes_en']}")
        print(f"  SMS Roman Urdu:\n  {ev_enroute['notifications']['roman_urdu']}")
        
        # 3. STARTED (Work initiated)
        ev_started = tracker.update_status(j_id, p_id, p_name, tracker.STARTED, location=nlu_intent.location)
        print(f"\n📌 Status Update: [{ev_started['status']}]")
        print(f"  System Event: {ev_started['notes_en']}")
        print(f"  SMS Roman Urdu:\n  {ev_started['notifications']['roman_urdu']}")
        
        # 4. COMPLETED (Service delivery finalized)
        ev_completed = tracker.update_status(j_id, p_id, p_name, tracker.COMPLETED, location=nlu_intent.location)
        print(f"\n📌 Status Update: [{ev_completed['status']}]")
        print(f"  System Event: {ev_completed['notes_en']}")
        print(f"  SMS Roman Urdu:\n  {ev_completed['notifications']['roman_urdu']}")
        print("=" * 60)
        
        # --- Post-Service Customer Feedback & Reputation Simulation (NEW!) ---
        print("\n" + "=" * 60)
        print("⭐ POST-SERVICE CUSTOMER FEEDBACK & REPUTATION ENGINE")
        print("=" * 60)
        
        rep_engine = ReputationEngine(providers_db_path="providers_db.json", reviews_log_path="reviews_log.json")
        review_text = "Zafar Ali ne bohot acha aur professional kaam kiya, behtareen service fast aur teek thi!"
        rating_stars = 5.0
        
        print(f"\nSubmitting customer rating: {rating_stars} Stars")
        print(f"Customer written review (Roman Urdu): \"{review_text}\"")
        
        fed_res = rep_engine.submit_feedback(
            job_id=j_id,
            provider_id=p_id,
            rating=rating_stars,
            review_text=review_text
        )
        
        if fed_res["success"]:
            print(f"\n📊 Feedback Ingested successfully!")
            print(f"  Sentiment Label:   [{fed_res['sentiment_label']}] (Score: {fed_res['sentiment_score']})")
            print(f"  Rating average:    {fed_res['rating_delta']['old_rating']:.2f} -> {fed_res['rating_delta']['new_rating']:.2f} (Total reviews: {fed_res['rating_delta']['total_reviews']})")
            print(f"  Reliability index: {(fed_res['reliability_delta']['old_reliability']*100):.1f}% -> {(fed_res['reliability_delta']['new_reliability']*100):.1f}% (Adjustment: {(fed_res['reliability_delta']['adjustment']*100):+.1f}%)")
        else:
            print(f"  ❌ Feedback submission failed: {fed_res.get('error_message')}")
        print("=" * 60)
        
        # --- Platform Dispute Resolution & Escalation Protocol Simulation (NEW!) ---
        print("\n" + "=" * 60)
        print("🚨 PLATFORM DISPUTE ESCALATION & ADMIN REASONING TRACE")
        print("=" * 60)
        
        dispute_eng = DisputeEngine(disputes_log_path="disputes_log.json")
        complaint_text = "I am disputing the total amount! PKR 688 urgency and PKR 361 off-hour night fee are far too expensive!"
        
        print(f"\nCustomer filed PRICE_DISAGREEMENT dispute ticket.")
        print(f"Customer complaint details: \"{complaint_text}\"")
        
        ticket = dispute_eng.raise_dispute(
            job_id=j_id,
            provider_id=p_id,
            provider_name=p_name,
            customer_contact="+923001234567",
            category=DisputeEngine.PRICE_DISAGREEMENT,
            customer_complaint=complaint_text,
            billing_info=price_breakdown
        )
        
        print(f"\n🎫 Support Ticket Created: {ticket['ticket_id']}")
        print(f"\n💬 Automated Acknowledgment Customer Alert (Bilingual):")
        print(f"  --- [English] ---")
        print(ticket["notifications"]["english"])
        print(f"\n  --- [Roman Urdu] ---")
        print(ticket["notifications"]["roman_urdu"])
        
        print(f"\n🛡️ Administrative Reasoning Audit Trace:")
        print("-" * 50)
        print(ticket["reasoning_trace"])
        print("-" * 50)
        
        print(f"\n🤖 Platform Resolution Recommendation:")
        print(f"  * {ticket['admin_recommendation']}")
        print("=" * 60)
        
    else:
        print(f"  ❌ Booking failed: {booking_res['error_message']}")

    # 6. Verify Overlap Buffering (Attempt booking an overlap at 10:15 AM)
    print("\n[Step 8] Verifying Transit Travel Buffer Overlap Prevention:")
    overlap_time = tomorrow.replace(hour=10, minute=15, second=0, microsecond=0)
    print(f"  Attempting to book 10:15 AM (during 10:00 AM booking + 30m travel buffer)...")
    
    overlap_res = scheduler.book_slot(
        provider_id=matched_provider["id"],
        provider_name=matched_provider["name"],
        job_id="JOB-993",
        start_time=overlap_time,
        duration_mins=60,
        user_contact="+923007654321",
        urgency=job_context["urgency"].capitalize(),
        location=nlu_intent.location,
        price=price_breakdown["final_total"]
    )
    
    if not overlap_res["success"]:
        print(f"  ✅ Correctly Blocked Overlap! Error: \"{overlap_res['error_message']}\"")
        print(f"  ✅ Urdu translation: \"{overlap_res['error_message_ur']}\"")
    else:
        print("  ❌ Bug: Allowed overlap double booking!")
        
    print("\n" + "=" * 60)
    print("⚡ DEMO COMPLETED SUCCESSFULLY! ⚡")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    # Reconfigure stdout to use UTF-8 encoding to support emojis and special characters on Windows CMD
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    run_orchestrator_demo()
