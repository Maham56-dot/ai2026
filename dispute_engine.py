import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class DisputeEngine:
    """
    Dispute Resolution Engine for AI Service Orchestrator.
    Handles 'Poor Quality' and 'Price Disagreement' customer complaints.
    Automatically generates a structured Reasoning Trace and Actionable Recommendation 
    for Platform Administrators, persisting tickets statefully to disk.
    """

    POOR_QUALITY = "Poor Quality"
    PRICE_DISAGREEMENT = "Price Disagreement"

    def __init__(self, disputes_log_path: str = "disputes_log.json"):
        self.disputes_log_path = disputes_log_path
        # Initialize disputes log file if it does not exist
        if not os.path.exists(self.disputes_log_path):
            self._write_disputes([])

    def _load_disputes(self) -> List[Dict[str, Any]]:
        """Loads dispute history from persistent JSON database."""
        try:
            with open(self.disputes_log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_disputes(self, disputes: List[Dict[str, Any]]):
        """Writes dispute history back to the persistent JSON database."""
        try:
            with open(self.disputes_log_path, "w", encoding="utf-8") as f:
                json.dump(disputes, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save disputes database: {e}")

    def raise_dispute(
        self,
        job_id: str,
        provider_id: str,
        provider_name: str,
        customer_contact: str,
        category: str,
        customer_complaint: str,
        billing_info: Optional[Dict[str, Any]] = None,
        provider_stats: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registers a customer dispute ticket.
        Generates a structured Admin Reasoning Trace and Platform Recommendation.
        Saves the ticket statefully to disk.
        """
        # Validate category
        valid_categories = [self.POOR_QUALITY, self.PRICE_DISAGREEMENT]
        if category not in valid_categories:
            raise ValueError(f"Invalid dispute category: '{category}'. Must be one of {valid_categories}")

        ticket_id = f"TKT-{datetime.now().strftime('%M%S')}"
        timestamp_str = datetime.now().isoformat()
        
        # 1. Generate Structured Admin Reasoning Trace & Operational Recommendation
        reasoning_trace = []
        platform_recommendation = ""
        risk_level = "Low"

        reasoning_trace.append(f"Dispute Ticket {ticket_id} opened at {timestamp_str} for Job {job_id}.")
        reasoning_trace.append(f"Customer reported complaint under category: '{category}'.")
        reasoning_trace.append(f"Customer Details: {customer_contact} | Affected Provider: {provider_name} ({provider_id})")

        if category == self.PRICE_DISAGREEMENT:
            reasoning_trace.append("\n--- [Audit 1: Financial Pricing Invoice Validation] ---")
            if billing_info:
                subtotal = billing_info.get("subtotal", 0.0)
                surcharges = billing_info.get("surcharges_total", 0.0)
                final_total = billing_info.get("final_total", 0.0)
                base_fee = billing_info.get("line_items", {}).get("base_fee", {}).get("amount", 0.0)
                distance_fee = billing_info.get("line_items", {}).get("distance_cost", {}).get("amount", 0.0)
                
                # Check pricing logic mathematical consistency
                expected_subtotal = base_fee + distance_fee
                is_subtotal_correct = abs(expected_subtotal - subtotal) < 0.01
                
                reasoning_trace.append(f"  - Logged Base Rate: Rs. {base_fee:.2f} | Logged Distance tariff: Rs. {distance_fee:.2f}")
                reasoning_trace.append(f"  - Math Check (Base + Distance): Expected Subtotal Rs. {expected_subtotal:.2f} | Actual subtotal: Rs. {subtotal:.2f} ({'PASS' if is_subtotal_correct else 'FAIL'})")
                reasoning_trace.append(f"  - Surcharges Incurred: Rs. {surcharges:.2f} | Final Invoiced Total: Rs. {final_total:.2f}")
                
                # Assess billing justification
                urgency = billing_info.get("line_items", {}).get("urgency_surcharge", {}).get("amount", 0.0)
                night_premium = billing_info.get("line_items", {}).get("time_surcharge", {}).get("amount", 0.0)
                
                reasoning_trace.append("  - Surcharges Trace:")
                if urgency > 0:
                    reasoning_trace.append(f"    * Urgency premium (Rs. {urgency:.2f}) was added due to prioritize scheduling.")
                if night_premium > 0:
                    reasoning_trace.append(f"    * Night premium (Rs. {night_premium:.2f}) was added due to booking outside normal 9 AM - 6 PM daytime range.")
                
                # Determine recommendation
                if surcharges > 0:
                    reasoning_trace.append("  - Client was charged surcharges due to off-hours/high priority. Billing calculation is mathematically correct.")
                    platform_recommendation = (
                        "Billing calculations are audited as 100% CORRECT. Surcharges were justified by urgency and booking time. "
                        "Action: Deny refund request, but offer a Rs. 150 Customer Goodwill Promo Coupon to resolve friction."
                    )
                else:
                    reasoning_trace.append("  - Standard daytime rates were applied without premiums. Billing calculated correctly.")
                    platform_recommendation = (
                        "Standard billing is fully justified. No surcharge error occurred. "
                        "Action: Maintain original price invoice. Admin to call client to explain base and mileage fees."
                    )
            else:
                reasoning_trace.append("  - WARNING: No invoice billing history attached. Auditing calculations against general tier parameters.")
                platform_recommendation = "Incomplete billing info attached. Action: platform rep to manually review invoice logs."
                
        elif category == self.POOR_QUALITY:
            reasoning_trace.append("\n--- [Audit 2: Service Quality & Provider Operational Risk Review] ---")
            if provider_stats:
                rating = provider_stats.get("rating", 4.0)
                reliability = provider_stats.get("on_time_rate", 0.85)
                reviews_count = provider_stats.get("user_ratings_total", 0)
                
                reasoning_trace.append(f"  - Provider Stats: Average Rating: {rating:.2f} ⭐ | Reliability Index: {(reliability*100):.1f}% | Historical Reviews: {reviews_count}")
                
                # Determine Operational Risk levels
                # Rating below 4.3 or Reliability below 90% is classified as High operational risk
                if rating < 4.3 or reliability < 0.90:
                    risk_level = "High"
                    reasoning_trace.append("  - ⚠️ RISK FLAG TRIGGERED: Provider stats fell below safe platform quality standards!")
                    reasoning_trace.append(f"  - Provider historical rating ({rating:.2f}) or reliability index ({(reliability*100):.1f}%) indicate recurring performance issues.")
                    platform_recommendation = (
                        "⚠️ HIGH PLATFORM OPERATIONAL RISK. Provider has a pattern of low performance reviews. "
                        "Action: 1) Issue 100% FULL REFUND to the customer immediately. 2) Suspend provider account temporarily pending retraining. "
                        "3) Inject a permanent -10% Search Ranking weight penalty multiplier to protect platform reputation."
                    )
                else:
                    risk_level = "Low"
                    reasoning_trace.append("  - Provider statistics are within normal operational benchmarks (Rating >= 4.3, Reliability >= 90%).")
                    reasoning_trace.append("  - This complaint is classified as a single isolated incident.")
                    platform_recommendation = (
                        "Low Operational Risk. Provider has a strong historical track record. "
                        "Action: 1) Issue a 50% PARTIAL REFUND or a Rs. 500 discount coupon. "
                        "2) Offer a free technician check-up (dispatch intermediate technician). 3) Log a warning note on the provider's file."
                    )
            else:
                reasoning_trace.append("  - WARNING: No provider metadata profile attached. Auditing against default baseline benchmarks.")
                platform_recommendation = "Incomplete provider stats attached. Action: Issue a Rs. 300 compensation coupon and manually investigate provider file."

        # 2. Formulate Bilingual SMS notifications for the Customer
        sms_en = (
            f"Dear Customer, your dispute ticket #{ticket_id} has been successfully logged. "
            f"Our administrative team is investigating the issue (Job #{job_id}) and will contact you within 24 hours. "
            f"Thank you for your patience! Support is our priority."
        )
        
        sms_ur = (
            f"Moaziz Saarif, aap ki shikayat ticket #{ticket_id} darj ho chuki hai. "
            f"Humari admin team aap ke kaam (Job #{job_id}) ke is maslay ki jaiza le rahi hai aur 24 ghantay ke andar aapse rabta kare gi. "
            f"Aap ke sabar ka shukriya!"
        )

        # 3. Create Dispute Ticket Record
        dispute_ticket = {
            "ticket_id": ticket_id,
            "timestamp": timestamp_str,
            "job_id": job_id,
            "provider_id": provider_id,
            "provider_name": provider_name,
            "customer_contact": customer_contact,
            "category": category,
            "complaint_details": customer_complaint,
            "risk_level": risk_level,
            "reasoning_trace": "\n".join(reasoning_trace),
            "admin_recommendation": platform_recommendation,
            "notifications": {
                "english": sms_en,
                "roman_urdu": sms_ur
            }
        }

        # 4. Save to Persistent disputes log database
        disputes = self._load_disputes()
        disputes.append(dispute_ticket)
        self._write_disputes(disputes)

        return dispute_ticket

# Local manual test execution
if __name__ == "__main__":
    disp_eng = DisputeEngine(disputes_log_path="test_disputes_log.json")
    
    # Simulate Price Disagreement Dispute
    billing_mock = {
        "subtotal": 1720.0,
        "surcharges_total": 1049.2,
        "final_total": 2769.2,
        "line_items": {
            "base_fee": {"amount": 1500.0},
            "distance_cost": {"amount": 220.0},
            "urgency_surcharge": {"amount": 688.0},
            "time_surcharge": {"amount": 361.2}
        }
    }
    
    print("Simulating Price Disagreement Dispute lodging:")
    tkt_price = disp_eng.raise_dispute(
        job_id="JOB-TKT-111",
        provider_id="prov_01",
        provider_name="Zafar Electrician",
        customer_contact="+923001234567",
        category=disp_eng.PRICE_DISAGREEMENT,
        customer_complaint="Urgency surcharge is too high! Why Rs 688?",
        billing_info=billing_mock
    )
    print(tkt_price["reasoning_trace"])
    print(f"\nPlatform Recommendation:\n  {tkt_price['admin_recommendation']}")
    
    print("\n" + "="*60 + "\n")
    
    # Simulate Poor Quality High Risk Dispute
    prov_mock = {
        "rating": 4.10,
        "on_time_rate": 0.85,
        "user_ratings_total": 8
    }
    
    print("Simulating Poor Quality Dispute lodging (High Risk Provider):")
    tkt_quality = disp_eng.raise_dispute(
        job_id="JOB-TKT-222",
        provider_id="prov_06",
        provider_name="Kamran Electricians",
        customer_contact="+923007654321",
        category=disp_eng.POOR_QUALITY,
        customer_complaint="Technician didn't complete the wiring and broke my socket!",
        provider_stats=prov_mock
    )
    print(tkt_quality["reasoning_trace"])
    print(f"\nPlatform Recommendation:\n  {tkt_quality['admin_recommendation']}")
    
    # Clean disputes log
    if os.path.exists("test_disputes_log.json"):
        os.remove("test_disputes_log.json")
