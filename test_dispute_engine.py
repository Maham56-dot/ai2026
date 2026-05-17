import unittest
import os
import json
from dispute_engine import DisputeEngine

class TestDisputeEngine(unittest.TestCase):

    def setUp(self):
        # Paths for temporary test database file
        self.test_disputes_log = "test_run_disputes_log.json"
        self.engine = DisputeEngine(disputes_log_path=self.test_disputes_log)
        
        self.job_id = "JOB-1122"
        self.provider_id = "prov_01"
        self.provider_name = "Zafar Ali"
        self.contact = "+923001234567"

    def tearDown(self):
        # Delete temporary test files
        if os.path.exists(self.test_disputes_log):
            os.remove(self.test_disputes_log)

    def test_price_disagreement_financial_audit(self):
        billing_info = {
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
        
        ticket = self.engine.raise_dispute(
            job_id=self.job_id,
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            customer_contact=self.contact,
            category=self.engine.PRICE_DISAGREEMENT,
            customer_complaint="Why is there a Rs 688 surcharge?",
            billing_info=billing_info
        )
        
        self.assertEqual(ticket["category"], self.engine.PRICE_DISAGREEMENT)
        self.assertEqual(ticket["risk_level"], "Low")
        self.assertIn("Expected Subtotal Rs. 1720.00", ticket["reasoning_trace"])
        self.assertIn("surcharges due to off-hours", ticket["reasoning_trace"].lower())
        self.assertIn("Goodwill Promo Coupon", ticket["admin_recommendation"])

    def test_poor_quality_low_risk_evaluation(self):
        # Provider with good statistics (rating 4.70, reliability 0.95)
        provider_stats = {
            "rating": 4.70,
            "on_time_rate": 0.95,
            "user_ratings_total": 30
        }
        
        ticket = self.engine.raise_dispute(
            job_id=self.job_id,
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            customer_contact=self.contact,
            category=self.engine.POOR_QUALITY,
            customer_complaint="Technician left a minor scratch on the board.",
            provider_stats=provider_stats
        )
        
        self.assertEqual(ticket["category"], self.engine.POOR_QUALITY)
        self.assertEqual(ticket["risk_level"], "Low")
        self.assertIn("isolated incident", ticket["reasoning_trace"])
        self.assertIn("50% PARTIAL REFUND", ticket["admin_recommendation"])

    def test_poor_quality_high_risk_evaluation(self):
        # Provider with low statistics (rating 4.00, reliability 0.85)
        provider_stats = {
            "rating": 4.00,
            "on_time_rate": 0.85,
            "user_ratings_total": 9
        }
        
        ticket = self.engine.raise_dispute(
            job_id=self.job_id,
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            customer_contact=self.contact,
            category=self.engine.POOR_QUALITY,
            customer_complaint="Electrician arrived very late and broke the main switchboard!",
            provider_stats=provider_stats
        )
        
        self.assertEqual(ticket["category"], self.engine.POOR_QUALITY)
        self.assertEqual(ticket["risk_level"], "High")
        self.assertIn("RISK FLAG TRIGGERED", ticket["reasoning_trace"])
        self.assertIn("suspend provider account", ticket["admin_recommendation"].lower())
        self.assertIn("FULL REFUND", ticket["admin_recommendation"])

    def test_invalid_dispute_category(self):
        with self.assertRaises(ValueError):
            self.engine.raise_dispute(
                job_id=self.job_id,
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                customer_contact=self.contact,
                category="NonExistentCategory",
                customer_complaint="Bad service"
            )

    def test_dispute_ticket_persistence(self):
        # Submit a dispute
        self.engine.raise_dispute(
            job_id=self.job_id,
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            customer_contact=self.contact,
            category=self.engine.POOR_QUALITY,
            customer_complaint="Poor service."
        )
        
        # Instantiate second dispute engine pointing to same database file
        second_engine = DisputeEngine(disputes_log_path=self.test_disputes_log)
        disputes = second_engine._load_disputes()
        
        self.assertEqual(len(disputes), 1)
        self.assertEqual(disputes[0]["job_id"], self.job_id)

    def test_bilingual_notifications(self):
        ticket = self.engine.raise_dispute(
            job_id=self.job_id,
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            customer_contact=self.contact,
            category=self.engine.POOR_QUALITY,
            customer_complaint="Bad service."
        )
        
        # English Notification Checks
        self.assertIn("dispute ticket", ticket["notifications"]["english"].lower())
        self.assertIn("within 24 hours", ticket["notifications"]["english"])
        
        # Roman Urdu Notification Checks
        self.assertIn("shikayat ticket", ticket["notifications"]["roman_urdu"].lower())
        self.assertIn("24 ghantay", ticket["notifications"]["roman_urdu"])

if __name__ == "__main__":
    unittest.main()
