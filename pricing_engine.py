from typing import Dict, Any, List

class PricingEngine:
    """
    Dynamic Pricing Engine for AI Service Orchestrator.
    Calculates final costs based on:
    Final Cost = (Base Visit Fee + Distance Cost) * Urgency & Peak Surcharge Multiplier
    
    Provides:
    - Detailed, localized (English and Roman Urdu) billing transparency.
    - Multiple specific 'Budget-Friendly' alternative suggestions.
    """

    def __init__(self, cost_per_km: float = 50.0, base_travel_overhead: float = 100.0):
        # Default cost per kilometer (e.g., PKR 50/km)
        self.cost_per_km = cost_per_km
        
        # Base transport overhead to cover minimum fuel/logistics (e.g., PKR 100)
        self.base_travel_overhead = base_travel_overhead
        
        # Multipliers based on urgency level
        self.urgency_multipliers = {
            "low": 0.90,       # 10% discount for flexible timing
            "medium": 1.00,    # Standard rate
            "high": 1.20,      # 20% premium
            "emergency": 1.40  # 40% premium for immediate booking
        }
        
        # Surcharge multiplier for nighttime / off-hours booking (e.g., 8 PM to 8 AM)
        self.night_surcharge_multiplier = 1.15 # 15% surcharge

    def calculate_pricing(self, provider: Dict[str, Any], job_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the dynamic price and returns a highly detailed, transparent breakdown.
        
        Args:
            provider (Dict): Information about the matched service provider.
                e.g., { "name": "Ali Electrician", "base_rate": 1000, "experience_level": "Senior", "distance_km": 8.5 }
            job_context (Dict): Context of the request.
                e.g., { "urgency": "Emergency", "complexity": "Basic", "booking_hour": 21 }
                
        Returns:
            Dict: Comprehensive pricing analysis, line-item breakdown, and budget recommendations.
        """
        # 1. Base Visit Fee (calculated based on provider base_rate and adjusted by experience level)
        raw_base_rate = provider.get("base_rate", 1000.0)
        experience_level = provider.get("experience_level", "Intermediate").lower()
        
        # Adjust base rate based on provider tier/experience if not explicitly set
        if "base_rate" not in provider:
            if experience_level == "senior":
                base_fee = 1500.0
            elif experience_level == "junior":
                base_fee = 750.0
            else: # Intermediate / Standard
                base_fee = 1000.0
        else:
            base_fee = raw_base_rate

        # 2. Distance Cost Calculation
        distance_km = provider.get("distance_km", 0.0)
        distance_cost = self.base_travel_overhead + (distance_km * self.cost_per_km)
        if distance_km == 0.0:
            distance_cost = 0.0 # No travel if distance is zero

        # Subtotal of core physical expenses
        subtotal = base_fee + distance_cost

        # 3. Urgency & Peak Surcharge Multiplier
        urgency = job_context.get("urgency", "medium").lower()
        urgency_multiplier = self.urgency_multipliers.get(urgency, 1.0)
        
        # Check if booking hour represents nighttime/peak-off hours (8 PM to 8 AM)
        booking_hour = job_context.get("booking_hour", 12) # Default to noon
        is_night = booking_hour >= 20 or booking_hour < 8
        time_multiplier = self.night_surcharge_multiplier if is_night else 1.00

        # Combine multipliers
        combined_multiplier = urgency_multiplier * time_multiplier
        
        # Final Total Cost
        final_total = subtotal * combined_multiplier
        
        # Calculate individual adjustment amounts for breakdown transparency
        urgency_adjustment_amount = subtotal * (urgency_multiplier - 1.0)
        time_adjustment_amount = subtotal * urgency_multiplier * (time_multiplier - 1.0)
        total_surcharge_amount = final_total - subtotal

        # --- Dynamic Budget-Friendly Alternatives Recommendation Engine ---
        budget_alternatives = []

        # Alternative A: Time-Shifted Booking (Reduce Urgency / Off-peak)
        # If user booked as High/Emergency or during Night hours, they can shift timing to standard
        if urgency in ["high", "emergency"] or is_night:
            # Shift to standard urgency (medium) and day hours
            suggested_multiplier = self.urgency_multipliers["medium"] * 1.00
            time_shifted_total = subtotal * suggested_multiplier
            savings_time = final_total - time_shifted_total
            
            if savings_time > 10.0:
                budget_alternatives.append({
                    "type": "time_shift",
                    "title_en": "Shift to Off-Peak / Standard Hours",
                    "title_ur": "Standard ghantay mein book karein",
                    "description_en": "Wait for standard timing (within 24 hours, between 9 AM - 6 PM) to eliminate urgency and peak-hour surcharges.",
                    "description_ur": "Emergency aur peak hours ke izafi kharche se bachne ke liye aam auqat (subah 9 se shaam 6) mein kaam karwain.",
                    "new_total": round(time_shifted_total, 2),
                    "potential_savings": round(savings_time, 2)
                })

        # Alternative B: Provider Experience Tier Swap
        # If the job is Basic complexity but matched with a Senior expert, suggest a swap to Junior/Intermediate
        complexity = job_context.get("complexity", "Basic").lower()
        if complexity == "basic" and experience_level == "senior":
            # Conceptually swap with an Intermediate provider (base fee of Rs 1000) or Junior (Rs 750)
            suggested_base_fee = 750.0 # Junior rate
            suggested_subtotal = suggested_base_fee + distance_cost
            tier_shifted_total = suggested_subtotal * combined_multiplier
            savings_tier = final_total - tier_shifted_total
            
            if savings_tier > 10.0:
                budget_alternatives.append({
                    "type": "tier_shift",
                    "title_en": "Choose Standard/Junior Provider",
                    "title_ur": "Junior ya Aam Maahir muntakhib karein",
                    "description_en": "This is a basic task! You can swap to a standard or junior technician instead of a senior specialist and save on the base visit rate.",
                    "description_ur": "Ye aik sada kaam hai! Senior expert ki bajaye Junior ya standard technician muntakhib kar ke paise bachaein.",
                    "new_total": round(tier_shifted_total, 2),
                    "potential_savings": round(savings_tier, 2)
                })

        # Alternative C: Closer Provider (Proximity Swap)
        # If the current provider is far away (> 5km), recommend booking a closer provider if available
        if distance_km > 5.0:
            # Conceptually mock a closer provider at 2.0 km
            suggested_distance = 2.0
            suggested_distance_cost = self.base_travel_overhead + (suggested_distance * self.cost_per_km)
            suggested_subtotal = base_fee + suggested_distance_cost
            proximity_shifted_total = suggested_subtotal * combined_multiplier
            savings_proximity = final_total - proximity_shifted_total
            
            if savings_proximity > 10.0:
                budget_alternatives.append({
                    "type": "proximity_shift",
                    "title_en": "Match with a Closer Provider",
                    "title_ur": "Qareebi Maahir se rabta karein",
                    "description_en": "Match with an equivalent provider closer to your home (reducing travel distance from standard range to under 2km).",
                    "description_ur": "Apne ilaqay ke qareeb tareen maahir ko muntakhib kar ke safar ke akhrajaat kam karein.",
                    "new_total": round(proximity_shifted_total, 2),
                    "potential_savings": round(savings_proximity, 2)
                })

        # Ensure we always have at least a fallback "Flexible Timing" if no other alternative triggers
        if not budget_alternatives:
            flexible_total = subtotal * self.urgency_multipliers["low"]
            savings_flex = final_total - flexible_total
            budget_alternatives.append({
                "type": "flexible_timing",
                "title_en": "Super-Flexible Timing Discount",
                "title_ur": "Nihayat lachakdar auqat discount",
                "description_en": "Allow a wider 48-hour delivery window to receive a 10% discount on the standard base and transport fee.",
                "description_ur": "Kaam ke liye 48 ghantay tak ki mohlat dein aur 10% discount haasil karein.",
                "new_total": round(flexible_total, 2),
                "potential_savings": round(savings_flex, 2)
            })

        # --- Bilingual Transparent Breakdown Generation ---
        breakdown = {
            "calculation_formula": "Final Total = (Base Visit Fee + Distance Cost) * Urgency & Timing Multipliers",
            "provider_name": provider.get("name", "Local Service Provider"),
            "provider_tier": experience_level.capitalize(),
            
            "line_items": {
                "base_fee": {
                    "amount": round(base_fee, 2),
                    "label_en": "Base Visit Fee",
                    "label_ur": "Aane ki Fees (Base Fee)",
                    "description_en": f"Standard fee for a {experience_level.capitalize()} technician check-up and diagnostics.",
                    "description_ur": f"{experience_level.capitalize()} maahir ke aane aur jaiza lene ki standard fees."
                },
                "distance_cost": {
                    "amount": round(distance_cost, 2),
                    "label_en": "Distance Travel Fee",
                    "label_ur": "Safar ke Akhrajaat (Distance Fee)",
                    "description_en": f"Covers travel fuel and time. Calculated as flat Rs. {self.base_travel_overhead} base + Rs. {self.cost_per_km}/km for {round(distance_km, 1)} km.",
                    "description_ur": f"Fuel aur safar ka kharcha. Rs. {self.base_travel_overhead} flat + Rs. {self.cost_per_km} fi-km safar ({round(distance_km, 1)} km ke liye)."
                },
                "urgency_surcharge": {
                    "amount": round(urgency_adjustment_amount, 2),
                    "label_en": f"Urgency Premium ({urgency.capitalize()})",
                    "label_ur": f"Jaldi Kaam ka Surcharge ({urgency.capitalize()})",
                    "description_en": f"Multiplier of {urgency_multiplier}x applied to subtotal for prioritizing this schedule.",
                    "description_ur": f"Kaam jaldi karne ka surcharge. Subtotal par {urgency_multiplier}x multiplier lagaya gaya hai."
                },
                "time_surcharge": {
                    "amount": round(time_adjustment_amount, 2),
                    "label_en": "Off-Hours / Night Surcharge" if is_night else "Standard Hours Rate",
                    "label_ur": "Ghair-auqat / Raat ka Surcharge" if is_night else "Aam Auqat ki Rate",
                    "description_en": f"Additional {int((time_multiplier-1)*100)}% surcharge applied for booking outside normal hours (8 PM - 8 AM)." if is_night else "No off-hours surcharge applied.",
                    "description_ur": f"Raat ke waqt (8 baje se subah 8 baje tak) booking karne par {int((time_multiplier-1)*100)}% izafi kharcha." if is_night else "Aam auqat mein kaam karne par koi surcharge nahi."
                }
            },
            
            "subtotal": round(subtotal, 2),
            "surcharges_total": round(total_surcharge_amount, 2),
            "final_total": round(final_total, 2),
            
            "budget_alternatives": budget_alternatives
        }

        return breakdown

# Local manual test execution
if __name__ == "__main__":
    pricing = PricingEngine(cost_per_km=50.0, base_travel_overhead=100.0)
    
    mock_prov = {
        "name": "Zain Electrician",
        "experience_level": "Senior",
        "distance_km": 12.5
    }
    
    mock_job = {
        "urgency": "Emergency",
        "complexity": "Basic",
        "booking_hour": 21 # 9 PM (night surcharge)
    }
    
    res = pricing.calculate_pricing(mock_prov, mock_job)
    
    print(f"Receipt for: {res['provider_name']} ({res['provider_tier']})")
    print("-" * 50)
    for key, item in res["line_items"].items():
        print(f"{item['label_en']} ({item['label_ur']}):")
        print(f"  Rs. {item['amount']} | {item['description_en']}")
    print("-" * 50)
    print(f"SUBTOTAL:          Rs. {res['subtotal']}")
    print(f"SURCHARGES:        Rs. {res['surcharges_total']}")
    print(f"FINAL BILL:        Rs. {res['final_total']}")
    print("=" * 50)
    print("BUDGET-FRIENDLY ALTERNATIVES:")
    for alt in res["budget_alternatives"]:
        print(f"- {alt['title_en']} ({alt['title_ur']}):")
        print(f"  New Price: Rs. {alt['new_total']} (Save Rs. {alt['potential_savings']})")
        print(f"  Detail: {alt['description_en']}")
        print()
