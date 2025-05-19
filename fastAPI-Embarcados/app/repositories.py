import datetime
import os
import firebase_admin
from firebase_admin import db, credentials
from typing import Dict, Optional, Any
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

db_url = os.getenv("FIREBASE_DATABASE_URL")

cred = credentials.Certificate("./firebase-credentials.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': db_url
})

class HeartRateRepository:
    def __init__(self):
        self.ref = db.reference("heartrate")
    
    def get_all_readings(self) -> Dict[str, Any]:
        """Get all heart rate readings"""
        return self.ref.get() or {}
        
    def get_reading_by_id(self, reading_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific heart rate reading by ID"""
        return self.ref.child(reading_id).get()
    
    def add_reading(self, data: Dict[str, Any]) -> str:
        """Add a new heart rate reading"""
        new_ref = self.ref.push(data)
        return new_ref.key
    
class MeasurementControlRepository:
    def __init__(self):
        self.ref = db.reference("measurement_control")
    
    def get_control_status(self) -> Optional[Dict[str, Any]]:
        """Get the current measurement control status"""
        return self.ref.get()
    
    def set_control_status(self, is_paused: bool, updated_by: str = "api") -> Dict[str, Any]:
        """Set the measurement control status"""
        control_data = {
            "is_paused": is_paused,
            "last_updated": datetime.now().isoformat(),
            "updated_by": updated_by
        }
        self.ref.set(control_data)
        return control_data
    
    def listen_for_control_changes(self, callback):
        """Listen for changes in measurement control"""
        def on_event(event):
            if event.event_type in ['put', 'patch'] and event.data:
                callback(event.data)
        
        self.ref.listen(on_event)