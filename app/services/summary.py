from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.alarm import AlarmModel
from app.schemas.alarm import DailySummaryResponse, HourlySummaryItem

def obtener_resumen_dia(
    db: Session,
    fecha_filtro: Optional[str] = None
) -> DailySummaryResponse:
    """
    Agrupa las alarmas por hora para una fecha específica.
    Por defecto utiliza la fecha de 'hoy' (datetime.now().date()).
    """
    hoy = datetime.now().date()

    # Obtener todas las fechas distintas con registros para permitir navegación histórica si se desea
    fechas_db = db.query(func.date(AlarmModel.fecha_creacion)).distinct().order_by(AlarmModel.fecha_creacion.desc()).all()
    fechas_disponibles = [str(f[0]) for f in fechas_db if f[0] is not None]

    # Determinar qué fecha consultar
    if fecha_filtro:
        try:
            target_date = datetime.strptime(fecha_filtro, "%Y-%m-%d").date()
        except ValueError:
            target_date = hoy
    else:
        target_date = hoy

    es_hoy = (target_date == hoy)

    # Consultar alarmas del día seleccionado
    alarmas_del_dia = db.query(AlarmModel).filter(
        func.date(AlarmModel.fecha_creacion) == target_date.strftime("%Y-%m-%d")
    ).all()

    # Inicializar las 24 franjas horarias (00:00 a 23:00)
    conteo_por_hora = {f"{h:02d}:00": 0 for h in range(24)}

    for alarma in alarmas_del_dia:
        hora_str = f"{alarma.fecha_creacion.hour:02d}:00"
        conteo_por_hora[hora_str] += 1

    franjas = [
        HourlySummaryItem(hora=h, total_alarmas=count)
        for h, count in conteo_por_hora.items()
    ]

    return DailySummaryResponse(
        fecha=target_date.strftime("%Y-%m-%d"),
        total_dia=len(alarmas_del_dia),
        franjas=franjas,
        es_hoy=es_hoy,
        fechas_disponibles=fechas_disponibles
    )
