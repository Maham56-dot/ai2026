import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class TrackingEngine:
    """
    Real-time status tracking engine for AI Service Orchestrator.
    Manages the sequential service lifecycle:
    PENDING -> ACCEPTED -> EN_ROUTE -> STARTED -> COMPLETED
    
    Persists transactions to an internal JSON log database and generates bilingual notifications.
    """
    
    # Valid tracking statuses
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EN_ROUTE = "EN_ROUTE"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    # Define valid transitions for the state machine
    VALID_TRANSITIONS = {
        PENDING: [ACCEPTED, CANCELLED],
        ACCEPTED: [EN_ROUTE, CANCELLED],
        EN_ROUTE: [STARTED, CANCELLED],
        STARTED: [COMPLETED, CANCELLED],
        COMPLETED: [],  # Final state
        CANCELLED: []   # Final state
    }

    def __init__(self, log_path: str = "tracking_log.json"):
        self.log_path = log_path
        # Initialize log file if it does not exist
        if not os.path.exists(self.log_path):
            self._write_logs([])

    def _load_logs(self) -> List[Dict[str, Any]]:
        """Loads transaction history from the internal JSON file log."""
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_logs(self, logs: List[Dict[str, Any]]):
        """Writes transaction history back to the internal JSON file log."""
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to write tracking logs: {e}")

    def get_job_history(self, job_id: str) -> List[Dict[str, Any]]:
        """Returns all status change records for a specific Job ID."""
        logs = self._load_logs()
        return [entry for entry in logs if entry.get("job_id") == job_id]

    def get_latest_status(self, job_id: str) -> str:
        """Returns the current state of the job, defaulting to PENDING if not found."""
        history = self.get_job_history(job_id)
        if not history:
            return self.PENDING
        # Sort history by timestamp to get the absolute newest state
        history.sort(key=lambda x: x.get("timestamp", ""))
        return history[-1]["status"]

    def update_status(
        self,
        job_id: str,
        provider_id: str,
        provider_name: str,
        new_status: str,
        location: str = "Islamabad",
        eta_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validates the state transition and updates the internal status log.
        Generates bilingual notification text.
        """
        current_status = self.get_latest_status(job_id)
        new_status = new_status.upper()
        
        # 1. Validate status names
        all_statuses = [self.PENDING, self.ACCEPTED, self.EN_ROUTE, self.STARTED, self.COMPLETED, self.CANCELLED]
        if new_status not in all_statuses:
            raise ValueError(f"Invalid status: '{new_status}'. Must be one of {all_statuses}")

        # 2. Validate transition legality
        allowed = self.VALID_TRANSITIONS.get(current_status, [])
        # Special case: allow creating a PENDING status initially
        if current_status == self.PENDING and not self.get_job_history(job_id) and new_status == self.PENDING:
            pass
        elif new_status not in allowed and new_status != current_status:
            raise ValueError(
                f"Invalid state transition! Cannot jump from '{current_status}' to '{new_status}'. "
                f"Allowed destinations: {allowed}"
            )

        # 3. Formulate Bilingual SMS templates & Event notes based on status
        timestamp_str = datetime.now().isoformat()
        notes_en = ""
        notes_ur = ""
        sms_en = ""
        sms_ur = ""

        if new_status == self.PENDING:
            notes_en = f"Job request #{job_id} submitted. Searching for matching providers."
            notes_ur = f"Kaam ki request #{job_id} darj ho chuki hai. Behtareen maahir ki talaash jaari hai."
            sms_en = f"Job #{job_id} received. We are matching you with the best provider."
            sms_ur = f"Aap ki request #{job_id} mil chuki hai. Hum jald hi maahir ka intekhab karein ge."
            
        elif new_status == self.ACCEPTED:
            notes_en = f"Provider {provider_name} has accepted request #{job_id}."
            notes_ur = f"Maahir {provider_name} ne request #{job_id} qabool kar li hai."
            sms_en = f"Good news! Provider {provider_name} has accepted your request #{job_id}."
            sms_ur = f"Khushkhabri! Provider {provider_name} ne aap ka kaam #{job_id} qabool kar liya hai."
            
        elif new_status == self.EN_ROUTE:
            eta_str = f" in {eta_minutes} mins" if eta_minutes else ""
            eta_ur_str = f" (takreeban {eta_minutes} minute mein)" if eta_minutes else ""
            notes_en = f"Provider {provider_name} is en route to customer site{eta_str}."
            notes_ur = f"Maahir {provider_name} customer ke patay par aane ke liye raste mein hain{eta_ur_str}."
            sms_en = f"🔔 TRAVEL UPDATE: Provider {provider_name} is en route to {location} and will arrive{eta_str}! Safe tracking active."
            sms_ur = f"🔔 SAFAR KI UPDATE: Provider {provider_name} aap ke patay ({location}) ke liye nikal chuke hain aur{eta_ur_str} pohnch jayen ge!"
            
        elif new_status == self.STARTED:
            notes_en = f"Provider {provider_name} has arrived and started job #{job_id}."
            notes_ur = f"Maahir {provider_name} ne pohnch kar kaam #{job_id} shuru kar diya hai."
            sms_en = f"🛠️ WORK STARTED: Provider {provider_name} has started work on Job #{job_id}. Safety verified."
            sms_ur = f"🛠️ KAAM SHURU: Provider {provider_name} ne aap ka kaam (Job #{job_id}) shuru kar diya hai. Hifazati checks active hain."
            
        elif new_status == self.COMPLETED:
            notes_en = f"Job #{job_id} completed successfully by {provider_name}."
            notes_ur = f"Kaam #{job_id} kamyabi se mukammal ho chuka hai."
            sms_en = f"✅ JOB COMPLETED! Job #{job_id} is finished. Please complete rating. Invoice receipt sent."
            sms_ur = f"✅ KAAM MUKAMMAL! Aap ka kaam #{job_id} khatam ho gaya hai. Feedback lazmi dein aur invoice jaiza lein."
            
        elif new_status == self.CANCELLED:
            notes_en = f"Job #{job_id} has been cancelled."
            notes_ur = f"Kaam #{job_id} mansookh kar diya gaya hai."
            sms_en = f"⚠️ CANCELLED: Job #{job_id} has been cancelled. Reach support for assistance."
            sms_ur = f"⚠️ MANSOOKH: Aap ka kaam #{job_id} mansookh ho gaya hai. Madad ke liye humse rabta karein."

        # 4. Save Event Record to internal JSON database
        event_record = {
            "timestamp": timestamp_str,
            "job_id": job_id,
            "provider_id": provider_id,
            "provider_name": provider_name,
            "status": new_status,
            "location": location,
            "notes_en": notes_en,
            "notes_ur": notes_ur,
            "notifications": {
                "english": sms_en,
                "roman_urdu": sms_ur
            }
        }
        
        logs = self._load_logs()
        logs.append(event_record)
        self._write_logs(logs)

        return event_record

# Local manual test execution
if __name__ == "__main__":
    tracker = TrackingEngine(log_path="test_tracking_log.json")
    
    # Run a sequential tracking workflow simulation
    j_id = "JOB-TRACK-777"
    p_id = "prov_01"
    p_name = "Zafar Electrician"
    
    print("Simulating Tracking Transitions:")
    print("-" * 60)
    
    # PENDING
    ev = tracker.update_status(j_id, p_id, p_name, tracker.PENDING)
    print(f"Status: {ev['status']} | SMS (Roman Urdu):\n  {ev['notifications']['roman_urdu']}\n")
    
    # ACCEPTED
    ev = tracker.update_status(j_id, p_id, p_name, tracker.ACCEPTED)
    print(f"Status: {ev['status']} | SMS (Roman Urdu):\n  {ev['notifications']['roman_urdu']}\n")
    
    # EN ROUTE
    ev = tracker.update_status(j_id, p_id, p_name, tracker.EN_ROUTE, eta_minutes=15)
    print(f"Status: {ev['status']} | SMS (Roman Urdu):\n  {ev['notifications']['roman_urdu']}\n")
    
    # STARTED
    ev = tracker.update_status(j_id, p_id, p_name, tracker.STARTED)
    print(f"Status: {ev['status']} | SMS (Roman Urdu):\n  {ev['notifications']['roman_urdu']}\n")
    
    # COMPLETED
    ev = tracker.update_status(j_id, p_id, p_name, tracker.COMPLETED)
    print(f"Status: {ev['status']} | SMS (Roman Urdu):\n  {ev['notifications']['roman_urdu']}\n")
    
    # Test illegal transition validation check
    try:
        print("Testing illegal transition back to EN_ROUTE...")
        tracker.update_status(j_id, p_id, p_name, tracker.EN_ROUTE)
    except ValueError as e:
        print(f"✅ Validation caught illegal transition correctly: {e}")
        
    # Clean up temp test log file
    if os.path.exists("test_tracking_log.json"):
        os.remove("test_tracking_log.json")
