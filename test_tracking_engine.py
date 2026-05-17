import unittest
import os
from tracking_engine import TrackingEngine

class TestTrackingEngine(unittest.TestCase):

    def setUp(self):
        # Initialize the tracker with a custom test log path
        self.test_log_path = "test_run_tracking_log.json"
        self.tracker = TrackingEngine(log_path=self.test_log_path)
        self.job_id = "TEST-JOB-999"
        self.provider_id = "P-88"
        self.provider_name = "Zahid Electrician"

    def tearDown(self):
        # Clean up the test database file
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_initial_status_defaults_to_pending(self):
        status = self.tracker.get_latest_status(self.job_id)
        self.assertEqual(status, self.tracker.PENDING)

    def test_valid_sequential_lifecycle(self):
        # PENDING -> ACCEPTED
        ev1 = self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.ACCEPTED)
        self.assertEqual(ev1["status"], self.tracker.ACCEPTED)
        self.assertEqual(self.tracker.get_latest_status(self.job_id), self.tracker.ACCEPTED)
        
        # ACCEPTED -> EN_ROUTE
        ev2 = self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.EN_ROUTE, eta_minutes=15)
        self.assertEqual(ev2["status"], self.tracker.EN_ROUTE)
        self.assertIn("15 mins", ev2["notes_en"])
        
        # EN_ROUTE -> STARTED
        ev3 = self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.STARTED)
        self.assertEqual(ev3["status"], self.tracker.STARTED)
        
        # STARTED -> COMPLETED
        ev4 = self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.COMPLETED)
        self.assertEqual(ev4["status"], self.tracker.COMPLETED)
        
        # Verify history trace size
        history = self.tracker.get_job_history(self.job_id)
        self.assertEqual(len(history), 4) # ACCEPTED, EN_ROUTE, STARTED, COMPLETED

    def test_invalid_transition_leaps(self):
        # Try to jump from PENDING directly to STARTED (illegal!)
        with self.assertRaises(ValueError):
            self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.STARTED)
            
        # Register a valid acceptance
        self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.ACCEPTED)
        
        # Try to jump from ACCEPTED directly to COMPLETED (illegal!)
        with self.assertRaises(ValueError):
            self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.COMPLETED)

    def test_state_cancellation_rules(self):
        # Allow PENDING -> ACCEPTED
        self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.ACCEPTED)
        
        # Allow ACCEPTED -> CANCELLED (cancellation from anywhere is legal)
        ev = self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.CANCELLED)
        self.assertEqual(ev["status"], self.tracker.CANCELLED)
        self.assertEqual(self.tracker.get_latest_status(self.job_id), self.tracker.CANCELLED)

    def test_json_database_persistence(self):
        # Update a status in this tracker instance
        self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.ACCEPTED)
        
        # Instantiate a separate TrackingEngine pointing to the same log path
        second_tracker = TrackingEngine(log_path=self.test_log_path)
        
        # The state must persist and be readable by the second instance
        self.assertEqual(second_tracker.get_latest_status(self.job_id), self.tracker.ACCEPTED)
        self.assertEqual(len(second_tracker.get_job_history(self.job_id)), 1)

    def test_bilingual_notifications(self):
        # Trigger 'EN_ROUTE'
        self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.ACCEPTED)
        ev = self.tracker.update_status(self.job_id, self.provider_id, self.provider_name, self.tracker.EN_ROUTE, eta_minutes=10)
        
        # English Notification Checks
        self.assertIn("Provider Zahid Electrician is en route", ev["notifications"]["english"])
        self.assertIn("10 mins", ev["notifications"]["english"])
        
        # Roman Urdu Notification Checks
        self.assertIn("Provider Zahid Electrician aap ke patay", ev["notifications"]["roman_urdu"])
        self.assertIn("10 minute", ev["notifications"]["roman_urdu"])

if __name__ == "__main__":
    unittest.main()
