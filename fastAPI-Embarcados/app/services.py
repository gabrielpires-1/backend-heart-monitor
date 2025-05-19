from app.repositories import HeartRateRepository, MeasurementControlRepository
from app.models import HeartRateReading, HeartRateResponse, MeasurementControlResponse
from typing import List, Optional

class HeartRateService:
    def __init__(self):
        self.repository = HeartRateRepository()
    
    def get_all_readings(self) -> List[HeartRateResponse]:
        readings_dict = self.repository.get_all_readings()
        readings = []
        
        for reading_id, reading_data in readings_dict.items():
            try:
                heart_rate = HeartRateReading.from_firebase(reading_data)
                readings.append(HeartRateResponse(id=reading_id, data=heart_rate))
            except Exception as e:
                print(f"Erro ao processar leitura {reading_id}: {e}")
                print(f"Dados: {reading_data}")
                continue
            
        return readings
    
    def get_reading_by_id(self, reading_id: str) -> Optional[HeartRateResponse]:
        reading_data = self.repository.get_reading_by_id(reading_id)
        if not reading_data:
            return None
            
        try:
            heart_rate = HeartRateReading.from_firebase(reading_data)
            return HeartRateResponse(id=reading_id, data=heart_rate)
        except Exception as e:
            print(f"Erro ao processar leitura {reading_id}: {e}")
            return None
        
    def get_latest_readings(self, count: int) -> List[HeartRateResponse]:
        """
        Get the most recent n heart rate readings
        """
        all_readings = self.get_all_readings()
        
        sorted_readings = sorted(
            all_readings,
            key=lambda x: x.data.timestamp if x.data.timestamp else "",
            reverse=True
        )
        
        return sorted_readings[:count]
    
    def listen_for_new_readings(self, callback):
        """
        Set up a listener for new heart rate readings
        """
        def on_event(event):
            # Para debug
            print(f"Firebase event received: type={event.event_type}, path={event.path}, data={event.data}")
            
            # Reage a eventos 'put' e 'patch' que indicam novas entradas ou atualizações
            if event.event_type in ['put', 'patch']:
                data = event.data
                
                # Se for um evento na raiz ('/') e contiver múltiplos registros
                if event.path == '/' and isinstance(data, dict):
                    for reading_id, reading_data in data.items():
                        callback(reading_id, reading_data)
                
                # Se for um evento em um nó específico (ex: '/reading_id')
                elif event.path.startswith('/') and len(event.path) > 1:
                    reading_id = event.path[1:]  # Remove o '/' inicial
                    callback(reading_id, data)
                
                # Se for um evento de um novo registro direto
                elif event.path == '/' and data:
                    # Verifica se data tem informações identificáveis como uma leitura
                    if isinstance(data, dict) and any(k in data for k in ['bpm', 'timestamp']):
                        # Gera um ID se não existir
                        reading_id = str(int(time.time() * 1000))
                        callback(reading_id, data)
        
        self.repository.ref.listen(on_event)

    def add_reading(self, reading_data: dict) -> str:
        """
        Adiciona uma nova leitura de batimento cardíaco
        """
        if "timestamp" not in reading_data or not reading_data["timestamp"]:
            from datetime import datetime
            reading_data["timestamp"] = datetime.now().isoformat()
        reading_id = self.repository.add_reading(reading_data)
        return reading_id
    
class MeasurementControlService:
    def __init__(self):
        self.repository = MeasurementControlRepository()
    
    def get_control_status(self) -> MeasurementControlResponse:
        """Get current measurement control status"""
        status_data = self.repository.get_control_status()
        
        if not status_data:
            # Se não existe, cria com status inicial (não pausado)
            status_data = self.repository.set_control_status(False, "system")
        
        return MeasurementControlResponse(
            is_paused=status_data.get("is_paused", False),
            last_updated=status_data.get("last_updated"),
            updated_by=status_data.get("updated_by", "system")
        )
    
    def pause_measurements(self) -> MeasurementControlResponse:
        """Pause heart rate measurements"""
        status_data = self.repository.set_control_status(True, "api")
        return MeasurementControlResponse(
            is_paused=status_data["is_paused"],
            last_updated=status_data["last_updated"],
            updated_by=status_data["updated_by"]
        )
    
    def resume_measurements(self) -> MeasurementControlResponse:
        """Resume heart rate measurements"""
        status_data = self.repository.set_control_status(False, "api")
        return MeasurementControlResponse(
            is_paused=status_data["is_paused"],
            last_updated=status_data["last_updated"],
            updated_by=status_data["updated_by"]
        )
    
    def toggle_measurements(self) -> MeasurementControlResponse:
        """Toggle measurement state (pause/resume)"""
        current_status = self.get_control_status()
        
        if current_status.is_paused:
            return self.resume_measurements()
        else:
            return self.pause_measurements()