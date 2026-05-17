import unittest
from datetime import datetime, timedelta, date
from scheduling_engine import SchedulingEngine

class TestSchedulingEngine(unittest.TestCase):

    def setUp(self):
        # Initialize scheduler with standard 30 minute travel buffer
        self.scheduler = SchedulingEngine(buffer_minutes=30)
        self.tomorrow = date.today() + timedelta(days=1)

    def test_standard_booking_success(self):
        # Attempt to book a standard slot tomorrow at 10 AM
        start_time = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=10, minute=0)
        
        res = self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-01",
            start_time=start_time,
            duration_mins=60,
            user_contact="+923001112222",
            urgency="Medium",
            location="I-8 Markaz, Islamabad",
            price=1200.0
        )
        
        self.assertTrue(res["success"])
        self.assertIn("notifications", res)
        self.assertIn("roman_urdu", res["notifications"])
        self.assertIn("english", res["notifications"])
        
        # Verify provider calendar size
        self.assertEqual(len(self.scheduler.provider_calendars["P-01"]), 1)

    def test_overlap_direct_prevention(self):
        start_time1 = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=10, minute=0)
        
        # Book 1st appointment (10:00 AM - 11:00 AM)
        res1 = self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-01",
            start_time=start_time1,
            duration_mins=60,
            user_contact="+923001112222",
            urgency="Medium",
            location="I-8 Islamabad",
            price=1200.0
        )
        self.assertTrue(res1["success"])
        
        # Attempt to book an exact overlapping appointment (10:15 AM - 11:15 AM)
        start_time2 = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=10, minute=15)
        res2 = self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-02",
            start_time=start_time2,
            duration_mins=60,
            user_contact="+923002223333",
            urgency="Medium",
            location="I-8 Islamabad",
            price=1200.0
        )
        
        self.assertFalse(res2["success"])
        self.assertIn("overlap", res2["error_message"].lower())

    def test_overlap_buffer_prevention(self):
        start_time1 = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=10, minute=0)
        
        # Book 1st appointment (10:00 AM - 11:00 AM)
        self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-01",
            start_time=start_time1,
            duration_mins=60,
            user_contact="+923001112222",
            urgency="Medium",
            location="I-8 Islamabad",
            price=1200.0
        )
        
        # Attempt to book another appointment starting at 11:15 AM
        # Even though 11:15 AM is after the 11:00 AM end time, 
        # the 30-minute travel buffer of JOB-01 blocks it until 11:30 AM!
        start_time2 = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=11, minute=15)
        res2 = self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-02",
            start_time=start_time2,
            duration_mins=60,
            user_contact="+923002223333",
            urgency="Medium",
            location="I-8 Islamabad",
            price=1200.0
        )
        self.assertFalse(res2["success"])
        
        # Booking at 11:30 AM should succeed (just at the buffer limit)
        start_time3 = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=11, minute=30)
        res3 = self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-03",
            start_time=start_time3,
            duration_mins=60,
            user_contact="+923002223333",
            urgency="Medium",
            location="I-8 Islamabad",
            price=1200.0
        )
        self.assertTrue(res3["success"])

    def test_standard_hours_restrictions(self):
        # Attempt standard booking at 11:00 PM (23:00)
        late_time = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=23, minute=0)
        
        res = self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-04",
            start_time=late_time,
            duration_mins=60,
            user_contact="+923001112222",
            urgency="Medium",
            location="I-8 Islamabad",
            price=1200.0
        )
        
        self.assertFalse(res["success"])
        self.assertIn("restricted", res["error_message"].lower())

    def test_emergency_hours_override(self):
        # Attempt emergency booking at 11:00 PM (23:00) - should succeed!
        late_time = datetime.combine(self.tomorrow, datetime.min.time()).replace(hour=23, minute=0)
        
        res = self.scheduler.book_slot(
            provider_id="P-01",
            provider_name="Aslam Plumber",
            job_id="JOB-05",
            start_time=late_time,
            duration_mins=60,
            user_contact="+923001112222",
            urgency="Emergency",
            location="I-8 Islamabad",
            price=1800.0
        )
        
        self.assertTrue(res["success"])

    def test_get_available_slots(self):
        # Query available slots for a new provider
        slots = self.scheduler.get_available_slots(
            provider_id="P-02",
            date=self.tomorrow,
            work_hours=(9, 18),
            is_emergency=False
        )
        
        # Standard day from 9 AM to 6 PM (9 hours).
        # Slots of 60 mins checked at 30 min intervals:
        # 9:00-10:00, 9:30-10:30, 10:00-11:00, ... up to 5:00-6:00 PM (17:00).
        # Total possible slots should be 17 slots.
        self.assertTrue(len(slots) > 0)
        
        # Verify first slot is 9:00 AM
        self.assertEqual(slots[0].hour, 9)
        self.assertEqual(slots[0].minute, 0)
        
        # Verify last slot is 5:00 PM (17:00)
        self.assertEqual(slots[-1].hour, 17)
        self.assertEqual(slots[-1].minute, 0)

if __name__ == "__main__":
    unittest.main()
