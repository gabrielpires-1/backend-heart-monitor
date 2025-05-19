from pydantic import BaseModel
from typing import Dict, Any, Optional, Union

class HeartRateReading(BaseModel):
    bpm: Optional[int] = None
    timestamp: Optional[str] = None

    @classmethod
    def from_firebase(cls, data: Dict[str, Any]):
        if not data:
            return cls()
        
        if isinstance(data, dict) and "bpm" in data:
            timestamp_key = next((k for k in data.keys() if k != "bpm"), None)
            timestamp = data.get(timestamp_key) if timestamp_key else None
            return cls(bpm=data.get("bpm"), timestamp=timestamp)
        
        if isinstance(data, int):
            return cls(bpm=data)
            
        return cls()

class HeartRateResponse(BaseModel):
    id: str
    data: HeartRateReading

class MeasurementControl(BaseModel):
    is_paused: bool = False
    last_updated: Optional[str] = None
    updated_by: Optional[str] = "api"

class MeasurementControlResponse(BaseModel):
    is_paused: bool
    last_updated: Optional[str] = None
    updated_by: Optional[str] = None