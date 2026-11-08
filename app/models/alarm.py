from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class AlarmModel(Base):
    __tablename__ = "alarmas"

    id_alarma = Column(Integer, primary_key=True, index=True)
    tech_2g = Column(Integer, nullable=False)
    tech_3g = Column(Integer, nullable=False)
    tech_4g = Column(Integer, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, index=True)
    municipio = Column(String(100), nullable=False)
    departamento = Column(String(100), nullable=False)
    notificada = Column(String(1), nullable=False)

