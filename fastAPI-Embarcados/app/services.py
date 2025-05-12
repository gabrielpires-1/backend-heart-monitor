from app.repositories import HeartRateRepository
from app.models import HeartRateReading, HeartRateResponse
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
        
        self.ref.listen(on_event)