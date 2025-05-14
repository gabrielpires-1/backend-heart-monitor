import os
import firebase_admin
from firebase_admin import db, credentials
from typing import Dict, Optional, Any
from dotenv import load_dotenv


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