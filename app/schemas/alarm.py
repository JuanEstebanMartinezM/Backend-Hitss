from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

class AlarmBase(BaseModel):
    id_alarma: int
    tech_2g: int
    tech_3g: int
    tech_4g: int
    fecha_creacion: datetime
    municipio: str
    departamento: str
    notificada: str

    model_config = ConfigDict(from_attributes=True)

class AlarmResponse(AlarmBase):
    duracion_segundos: float
    duracion_formato: str
    criticidad: str  # 'CRITICO' | 'WARN' | 'NORMAL'
    cumple_condiciones_base: bool

class AlarmListResponse(BaseModel):
    items: List[AlarmResponse]
    total: int
    total_critico: int
    total_warn: int
    total_normal: int

class HourlySummaryItem(BaseModel):
    hora: str  # ej. "08:00"
    total_alarmas: int

class DailySummaryResponse(BaseModel):
    fecha: str
    total_dia: int
    franjas: List[HourlySummaryItem]
    es_hoy: bool
    fechas_disponibles: List[str]

class UploadResponse(BaseModel):
    message: str
    total_procesadas: int
    total_guardadas: int
