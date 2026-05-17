import unittest
from pricing_engine import PricingEngine

class TestPricingEngine(unittest.TestCase):

    def setUp(self):
        # Create an instance with 50 Rs per km, and 100 Rs flat overhead
        self.engine = PricingEngine(cost_per_km=50.0, base_travel_overhead=100.0)

    def test_standard_pricing(self):
        # Standard intermediate provider, standard distance (5km), standard timing (noon)
        provider = {
            "name": "Zahid Plumber",
            "experience_level": "Intermediate",
            "base_rate": 1000.0,
            "distance_km": 5.0
        }
        job_context = {
            "urgency": "Medium",
            "complexity": "Intermediate",
            "booking_hour": 12 # 12:00 PM
        }
        
        res = self.engine.calculate_pricing(provider, job_context)
        
        # Expected base = 1000.0
        # Expected distance = 100.0 + (5.0 * 50.0) = 350.0
        # Subtotal = 1350.0
        # Multipliers = 1.0 (medium) * 1.0 (day) = 1.0
        # Total = 1350.0
        self.assertEqual(res["subtotal"], 1350.0)
        self.assertEqual(res["final_total"], 1350.0)
        self.assertEqual(res["surcharges_total"], 0.0)
        self.assertEqual(res["line_items"]["base_fee"]["amount"], 1000.0)
        self.assertEqual(res["line_items"]["distance_cost"]["amount"], 350.0)

    def test_urgency_surcharges(self):
        provider = {
            "name": "Ali Electrician",
            "experience_level": "Senior",
            "base_rate": 1200.0,
            "distance_km": 8.0
        }
        # Emergency urgency, day hours
        job_context = {
            "urgency": "Emergency",
            "complexity": "Intermediate",
            "booking_hour": 14 # 2:00 PM
        }
        
        res = self.engine.calculate_pricing(provider, job_context)
        
        # Base = 1200.0
        # Distance = 100.0 + (8.0 * 50.0) = 500.0
        # Subtotal = 1700.0
        # Urgency multiplier = 1.40
        # Total = 1700.0 * 1.40 = 2380.0
        # Surcharge = 680.0
        self.assertEqual(res["subtotal"], 1700.0)
        self.assertEqual(res["final_total"], 2380.0)
        self.assertEqual(res["surcharges_total"], 680.0)
        self.assertEqual(res["line_items"]["urgency_surcharge"]["amount"], 680.0)

    def test_nighttime_peak_hour_surcharges(self):
        provider = {
            "name": "Irfan AC Tech",
            "experience_level": "Intermediate",
            "base_rate": 1000.0,
            "distance_km": 10.0
        }
        # High urgency, 11:00 PM (night surcharge)
        job_context = {
            "urgency": "High",
            "complexity": "Intermediate",
            "booking_hour": 23
        }
        
        res = self.engine.calculate_pricing(provider, job_context)
        
        # Base = 1000.0
        # Distance = 100.0 + (10.0 * 50.0) = 600.0
        # Subtotal = 1600.0
        # Urgency multiplier = 1.20
        # Night multiplier = 1.15
        # Combined multiplier = 1.20 * 1.15 = 1.38
        # Total = 1600.0 * 1.38 = 2208.0
        # Surcharges total = 2208.0 - 1600.0 = 608.0
        self.assertEqual(res["subtotal"], 1600.0)
        self.assertEqual(res["final_total"], 2208.0)
        self.assertEqual(res["surcharges_total"], 608.0)

    def test_budget_alternatives_generation(self):
        provider = {
            "name": "Naveed Carpenter",
            "experience_level": "Senior",
            "base_rate": 1500.0,
            "distance_km": 15.0
        }
        # Basic job matched with senior at night under Emergency
        job_context = {
            "urgency": "Emergency",
            "complexity": "Basic",
            "booking_hour": 22
        }
        
        res = self.engine.calculate_pricing(provider, job_context)
        
        # Subtotal = 1500 + 100 + 750 = 2350
        # Emergency (1.40) * Night (1.15) = 1.61
        # Total = 2350 * 1.61 = 3783.5
        
        # We expect multiple budget alternatives to be suggested:
        # 1. Time Shift (shifting from emergency + night to standard daytime medium = 1.0x multiplier)
        # 2. Tier Shift (swapping senior base 1500 to junior base 750 because complexity is Basic)
        # 3. Proximity Shift (swapping 15km distance to 2km closer provider)
        alts = {alt["type"]: alt for alt in res["budget_alternatives"]}
        
        self.assertTrue("time_shift" in alts)
        self.assertTrue("tier_shift" in alts)
        self.assertTrue("proximity_shift" in alts)
        
        # Verify time-shift calculations:
        # Time-shifted multiplier = 1.0
        # Time-shifted total = Subtotal * 1.0 = 2350.0
        # Savings = 3783.5 - 2350.0 = 1433.5
        self.assertEqual(alts["time_shift"]["new_total"], 2350.0)
        self.assertEqual(alts["time_shift"]["potential_savings"], 1433.5)

    def test_zero_distance_boundary(self):
        provider = {
            "name": "Local Tech",
            "experience_level": "Junior",
            "base_rate": 750.0,
            "distance_km": 0.0
        }
        job_context = {
            "urgency": "Low",
            "complexity": "Basic",
            "booking_hour": 10
        }
        
        res = self.engine.calculate_pricing(provider, job_context)
        
        # Base = 750.0
        # Distance = 0.0
        # Subtotal = 750.0
        # Urgency Low multiplier = 0.90
        # Total = 750 * 0.9 = 675.0
        self.assertEqual(res["subtotal"], 750.0)
        self.assertEqual(res["final_total"], 675.0)

if __name__ == "__main__":
    unittest.main()
