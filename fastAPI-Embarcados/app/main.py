from fastapi import FastAPI, HTTPException, Request
from app.services import HeartRateService
from app.models import HeartRateReading, HeartRateResponse
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from queue import Queue
import threading

# Queue for passing events between Firebase listener thread and FastAPI
event_queue = Queue()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - for development only
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

heart_rate_service = HeartRateService()

@app.get("/")
def read_root():
    return {"message": "Heart Rate Monitoring API"}

@app.get("/heartrate", response_model=List[HeartRateResponse])
def get_all_readings():
    """
    Retorna todas as leituras de batimentos cardíacos
    """
    return heart_rate_service.get_all_readings()

@app.get("/heartrate/stream")
async def stream_heartrate(request: Request):
    """
    Creates a real-time stream of heart rate data using Server-Sent Events,
    powered by Firebase real-time updates
    """
    if not hasattr(app.state, "firebase_listener_running"):
        def start_listener():
            def on_new_reading(reading_id, reading_data):
                try:
                    heart_rate = HeartRateReading.from_firebase(reading_data)
                    event_data = {
                        "id": reading_id,
                        "bpm": heart_rate.bpm,
                        "timestamp": heart_rate.timestamp or ""
                    }
                    event_queue.put(event_data)
                except Exception as e:
                    print(f"Error processing reading {reading_id}: {e}")

            heart_rate_service.listen_for_new_readings(on_new_reading)
        
        thread = threading.Thread(target=start_listener, daemon=True)
        thread.start()
        app.state.firebase_listener_running = True
    
    async def event_generator():
        initial_readings = heart_rate_service.get_latest_readings(10)
        for reading in initial_readings:
            data = {
                "id": reading.id,
                "bpm": reading.data.bpm,
                "timestamp": reading.data.timestamp or ""
            }
            yield {
                "event": "initial_reading",
                "id": reading.id,
                "data": json.dumps(data)
            }
        
        while True:
            if await request.is_disconnected():
                break

            try:
                if not event_queue.empty():
                    data = event_queue.get_nowait()
                    yield {
                        "event": "new_reading",
                        "id": data["id"],
                        "data": json.dumps(data)
                    }
                    continue
            except Exception as e:
                print(f"Error fetching from queue: {e}")
            
            await asyncio.sleep(0.1)
    
    return EventSourceResponse(event_generator())

@app.get("/heartrate/{reading_id}", response_model=HeartRateResponse)
def get_reading(reading_id: str):
    """
    Retorna uma leitura específica de batimentos cardíacos
    """
    reading = heart_rate_service.get_reading_by_id(reading_id)
    if not reading:
        raise HTTPException(
            status_code=404,
            detail=f"Reading with ID {reading_id} not found"
        )
    return reading

@app.get("/heartrate/latest/{count}", response_model=List[HeartRateResponse])
def get_latest_readings(count: int):
    """
    Returns the latest n heart rate readings
    """
    if count <= 0:
        raise HTTPException(
            status_code=400,
            detail="Count parameter must be a positive integer"
        )
    
    return heart_rate_service.get_latest_readings(count)