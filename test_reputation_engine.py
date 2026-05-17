import unittest
import os
import json
from reputation_engine import ReputationEngine

class TestReputationEngine(unittest.TestCase):

    def setUp(self):
        # Paths for temporary test database files
        self.test_providers_db = "test_run_providers_db.json"
        self.test_reviews_log = "test_run_reviews_log.json"
        
        # Write dummy provider record to the test database
        dummy_provider = [
            {
                "id": "test_p_1",
                "name": "Arsalan Plumber",
                "experience_level": "Intermediate",
                "base_rate": 1000.0,
                "distance_km": 5.0,
                "travel_time_mins": 15.0,
                "availability": "available_now",
                "skill_level": "Intermediate",
                "on_time_rate": 0.900,
                "rating": 4.50,
                "user_ratings_total": 10
            }
        ]
        
        with open(self.test_providers_db, "w", encoding="utf-8") as f:
            json.dump(dummy_provider, f)
            
        self.engine = ReputationEngine(
            providers_db_path=self.test_providers_db,
            reviews_log_path=self.test_reviews_log
        )

    def tearDown(self):
        # Delete temporary test files
        for path in [self.test_providers_db, self.test_reviews_log]:
            if os.path.exists(path):
                os.remove(path)

    def test_sentiment_analysis_positive_english(self):
        res = self.engine.analyze_sentiment("Arsalan did an excellent and highly professional work!")
        self.assertEqual(res["label"], "Positive")
        self.assertGreater(res["score"], 0.0)

    def test_sentiment_analysis_positive_roman_urdu(self):
        res = self.engine.analyze_sentiment("arsalan ne bohot acha kaam kiya hai fit pipe fit kia shukriya")
        self.assertEqual(res["label"], "Positive")
        self.assertGreater(res["score"], 0.0)

    def test_sentiment_analysis_negative_english(self):
        res = self.engine.analyze_sentiment("terrible service, unprofessional, very late and dirty work")
        self.assertEqual(res["label"], "Negative")
        self.assertLess(res["score"], 0.0)

    def test_sentiment_analysis_negative_roman_urdu(self):
        res = self.engine.analyze_sentiment("bohot late aya, kaam kharab kiya aur bekaar tameez thi")
        self.assertEqual(res["label"], "Negative")
        self.assertLess(res["score"], 0.0)

    def test_sentiment_analysis_neutral(self):
        res = self.engine.analyze_sentiment("normal service sector G-11 Islamabad")
        self.assertEqual(res["label"], "Neutral")
        self.assertEqual(res["score"], 0.0)

    def test_feedback_submit_rating_math_recalculation(self):
        # 10 reviews with 4.50 average. Adding a 5.0 star feedback should result in:
        # ((4.50 * 10) + 5.0) / 11 = 50.0 / 11 = 4.5454... (rounds to 4.55)
        res = self.engine.submit_feedback(
            job_id="JOB-TEST-FEED",
            provider_id="test_p_1",
            rating=5.0,
            review_text="excellent work!"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["rating_delta"]["new_rating"], 4.55)
        self.assertEqual(res["rating_delta"]["total_reviews"], 11)

    def test_reputation_reliability_increase(self):
        # Start at 0.900. Ingest positive review (sentiment score = 1.0).
        # Shift: +0.02 * 1.0 = +0.02. New reliability: 0.900 + 0.02 = 0.920
        res = self.engine.submit_feedback(
            job_id="JOB-TEST-FEED",
            provider_id="test_p_1",
            rating=5.0,
            review_text="excellent best professional!"
        )
        self.assertEqual(res["reliability_delta"]["new_reliability"], 0.920)

    def test_reputation_reliability_decrease(self):
        # Start at 0.900. Ingest negative review with 1.0 star (sentiment score = -1.0).
        # Shift: -0.05 * (-1.0) = -0.05. New reliability: 0.900 - 0.05 = 0.850
        res = self.engine.submit_feedback(
            job_id="JOB-TEST-FEED",
            provider_id="test_p_1",
            rating=1.0,
            review_text="terrible, slow and unprofessional"
        )
        self.assertEqual(res["reliability_delta"]["new_reliability"], 0.850)

    def test_reputation_reliability_clipping_bounds(self):
        # Force reliability to cap at 1.000 max.
        # Submit positive feedback repeatedly on a high reliability provider
        for i in range(10):
            self.engine.submit_feedback(
                job_id=f"JOB-MOCK-{i}",
                provider_id="test_p_1",
                rating=5.0,
                review_text="excellent professional best"
            )
            
        p = self.engine.get_provider("test_p_1")
        self.assertEqual(p["on_time_rate"], 1.000) # Must not exceed 1.00

if __name__ == "__main__":
    unittest.main()
