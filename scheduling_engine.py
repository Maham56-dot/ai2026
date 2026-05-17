from datetime import datetime, timedelta, date as date_type
from typing import Dict, List, Optional, Any

class SchedulingEngine:
    """
    Advanced Scheduling Module for AI Service Orchestrator.
    Manages provider calendars, travel/transit buffer times, urgency overrides, 
    and generates localized notifications.
    """
    
    def __init__(self, buffer_minutes: int = 30):
        # Mock database of provider schedules
        # Format: { provider_id: [ {"start": datetime, "end": datetime, "job_id": str, "urgency": str} ] }
        self.provider_calendars: Dict[str, List[Dict[str, Any]]] = {}
        
        # Buffer time in minutes between jobs (e.g., for travel and traffic)
        self.buffer_minutes = buffer_minutes

    def _is_overlap(self, provider_id: str, proposed_start: datetime, proposed_end: datetime) -> bool:
        """
        Checks if a proposed time slot overlaps with existing bookings,
        taking transit/travel buffer times into account.
        
        Overlap occurs if:
        (Proposed_Start < Booking_End + Buffer) AND (Proposed_End + Buffer > Booking_Start)
        """
        if provider_id not in self.provider_calendars:
            return False
            
        buffer_delta = timedelta(minutes=self.buffer_minutes)
        
        for booking in self.provider_calendars[provider_id]:
            # Apply buffer time between bookings
            buffered_booking_end = booking["end"] + buffer_delta
            buffered_proposed_end = proposed_end + buffer_delta
            
            # Math overlap condition:
            if proposed_start < buffered_booking_end and buffered_proposed_end > booking["start"]:
                return True
        return False

    def get_available_slots(
        self, 
        provider_id: str, 
        date: date_type, 
        work_hours: tuple = (9, 18), 
        slot_duration_mins: int = 60,
        is_emergency: bool = False
    ) -> List[datetime]:
        """
        Returns a list of available slot start times for a given day.
        
        Args:
            provider_id (str): ID of the service provider.
            date (date): Date to check.
            work_hours (tuple): Standard start and end hour (e.g., 9 AM to 6 PM).
            slot_duration_mins (int): Duration of the service slot in minutes.
            is_emergency (bool): If True, unlocks 24-hour round-the-clock emergency bookings.
            
        Returns:
            List[datetime]: Available start datetimes for booking.
        """
        available_slots = []
        
        # If emergency, unlock full 24 hours. Otherwise, limit to standard work hours.
        if is_emergency:
            start_hour = 0
            end_hour = 23
            end_minute = 59
        else:
            start_hour = work_hours[0]
            end_hour = work_hours[1]
            end_minute = 0
            
        current_time = datetime.combine(date, datetime.min.time()).replace(
            hour=start_hour, minute=0, second=0, microsecond=0
        )
        end_of_day = datetime.combine(date, datetime.min.time()).replace(
            hour=end_hour, minute=end_minute, second=0, microsecond=0
        )
            
        slot_delta = timedelta(minutes=slot_duration_mins)
        
        # Slide through the day at 30-minute intervals
        while current_time + slot_delta <= end_of_day:
            proposed_end = current_time + slot_delta
            
            # Skip if proposed start is in the past compared to absolute current time
            if current_time > datetime.now() and not self._is_overlap(provider_id, current_time, proposed_end):
                available_slots.append(current_time)
                
            current_time += timedelta(minutes=30)
            
        return available_slots

    def book_slot(
        self, 
        provider_id: str, 
        job_id: str, 
        start_time: datetime, 
        duration_mins: int = 60, 
        user_contact: str = "",
        urgency: str = "Medium",
        location: str = "Islamabad",
        price: float = 0.0,
        provider_name: str = "Provider"
    ) -> Dict[str, Any]:
        """
        Attempts to book a calendar slot for a provider.
        
        Returns a result status dictionary with confirmation message templates.
        """
        end_time = start_time + timedelta(minutes=duration_mins)
        
        # 1. Past booking validation
        if start_time < datetime.now():
            return {
                "success": False,
                "error_message": "Cannot book slots in the past.",
                "error_message_ur": "Maazi ke auqat book nahi kiye ja sakte."
            }
            
        # 2. Urgent Off-Hours Check
        is_emergency = urgency.lower() == "emergency"
        hour = start_time.hour
        is_off_hours = hour < 9 or hour >= 18
        
        if is_off_hours and not is_emergency:
            return {
                "success": False,
                "error_message": "Standard bookings are restricted to 9:00 AM - 6:00 PM. Change urgency to 'Emergency' to unlock off-hours booking.",
                "error_message_ur": "Aam bookings subah 9 se shaam 6 tak mehdood hain. Ghair auqat booking ke liye 'Emergency' muntakhib karein."
            }

        # 3. Schedule overlap check
        if self._is_overlap(provider_id, start_time, end_time):
            return {
                "success": False,
                "error_message": "Booking overlap detected! Another appointment or travel buffer blocks this time slot.",
                "error_message_ur": "Waqt ka tasadum! Is dauran koi doosra kaam ya safar ka waqt mehdood hai."
            }
            
        # Create booking record
        booking_record = {
            "start": start_time,
            "end": end_time,
            "job_id": job_id,
            "urgency": urgency,
            "location": location,
            "price": price,
            "user_contact": user_contact
        }
        
        if provider_id not in self.provider_calendars:
            self.provider_calendars[provider_id] = []
            
        self.provider_calendars[provider_id].append(booking_record)
        # Sort schedule by start time
        self.provider_calendars[provider_id].sort(key=lambda x: x["start"])
        
        # Generate Notifications
        notifications = self._generate_notification_templates(
            provider_name=provider_name,
            job_id=job_id,
            start_time=start_time,
            end_time=end_time,
            user_contact=user_contact,
            location=location,
            price=price,
            urgency=urgency
        )
        
        return {
            "success": True,
            "booking_details": booking_record,
            "notifications": notifications
        }

    def delete_booking(self, job_id: str) -> bool:
        """
        Deletes a booking record from all provider calendars.
        """
        deleted = False
        for provider_id in list(self.provider_calendars.keys()):
            original_len = len(self.provider_calendars[provider_id])
            self.provider_calendars[provider_id] = [
                b for b in self.provider_calendars[provider_id] if b["job_id"] != job_id
            ]
            if len(self.provider_calendars[provider_id]) < original_len:
                deleted = True
        return deleted

    def _generate_notification_templates(
        self,
        provider_name: str,
        job_id: str,
        start_time: datetime,
        end_time: datetime,
        user_contact: str,
        location: str,
        price: float,
        urgency: str
    ) -> Dict[str, str]:
        """
        Generates English and Roman Urdu notifications for SMS or WhatsApp.
        """
        formatted_date = start_time.strftime("%b %d, %Y")
        formatted_start = start_time.strftime("%I:%M %p")
        formatted_end = end_time.strftime("%I:%M %p")
        
        # English Template
        msg_en = (
            f"🔔 BOOKING CONFIRMED (Job: #{job_id})\n"
            f"Dear Customer,\n"
            f"Your service request has been booked with expert {provider_name}.\n"
            f"📅 Date: {formatted_date}\n"
            f"🕒 Time: {formatted_start} to {formatted_end} (Includes travel buffer)\n"
            f"📍 Location: {location}\n"
            f"💳 Estimated Cost: Rs. {price:,.2f} ({urgency} Rate)\n"
            f"Thank you for using the AI Service Orchestrator! Safe & reliable support is on its way."
        )
        
        # Roman Urdu Template (Standard for Pakistani SMS)
        msg_ur = (
            f"🔔 BOOKING MUBARAK! (Job: #{job_id})\n"
            f"Aap ki booking expert {provider_name} ke sath pakki ho chuki hai.\n"
            f"📅 Tareekh: {formatted_date}\n"
            f"🕒 Waqt: {formatted_start} se {formatted_end} (Safar ke waqt ke sath)\n"
            f"📍 Pata: {location}\n"
            f"💳 Kul Kharcha: Rs. {price:,.2f} ({urgency} Rate)\n"
            f"Humari service muntakhib karne ka shukriya! Aap ka provider jald hi pohnch jayega."
        )
        
        return {
            "english": msg_en,
            "roman_urdu": msg_ur
        }

# Local manual test execution
if __name__ == "__main__":
    scheduler = SchedulingEngine(buffer_minutes=30)
    
    # Standard booking for tomorrow at 10 AM
    tomorrow = datetime.now() + timedelta(days=1)
    booking_start1 = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    
    print("Test 1: Booking Standard Slot...")
    res1 = scheduler.book_slot(
        provider_id="P-101",
        provider_name="Kamran Plumber",
        job_id="JOB-501",
        start_time=booking_start1,
        duration_mins=60,
        user_contact="+923001234567",
        urgency="Medium",
        location="G-9 Markaz, Islamabad",
        price=1500.0
    )
    print(f"Booking Success: {res1['success']}")
    if res1['success']:
        print(f"SMS Send (Roman Urdu):\n{res1['notifications']['roman_urdu']}")
        
    print("\nTest 2: Booking Overlapping Slot (10:30 AM)...")
    booking_start2 = tomorrow.replace(hour=10, minute=30, second=0, microsecond=0)
    res2 = scheduler.book_slot(
        provider_id="P-101",
        provider_name="Kamran Plumber",
        job_id="JOB-502",
        start_time=booking_start2,
        duration_mins=60,
        user_contact="+923007654321",
        urgency="Medium",
        location="G-9 Islamabad",
        price=1500.0
    )
    print(f"Booking Success: {res2['success']} | Error: {res2.get('error_message')}")
    
    print("\nTest 3: Booking Late Night (11:00 PM) - Medium Urgency...")
    booking_start3 = tomorrow.replace(hour=23, minute=0, second=0, microsecond=0)
    res3 = scheduler.book_slot(
        provider_id="P-101",
        provider_name="Kamran Plumber",
        job_id="JOB-503",
        start_time=booking_start3,
        duration_mins=60,
        user_contact="+923007654321",
        urgency="Medium",
        location="G-9 Islamabad",
        price=1500.0
    )
    print(f"Booking Success: {res3['success']} | Error: {res3.get('error_message')}")
    
    print("\nTest 4: Booking Late Night (11:00 PM) - Emergency Override...")
    res4 = scheduler.book_slot(
        provider_id="P-101",
        provider_name="Kamran Plumber",
        job_id="JOB-504",
        start_time=booking_start3,
        duration_mins=60,
        user_contact="+923007654321",
        urgency="Emergency",
        location="G-9 Islamabad",
        price=2200.0
    )
    print(f"Booking Success: {res4['success']}")
    if res4['success']:
        print(f"SMS Send (Roman Urdu):\n{res4['notifications']['roman_urdu']}")
