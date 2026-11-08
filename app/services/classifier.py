"""
Módulo de Clasificación de Criticidad de Alarmas y Cálculo de Duración.
Este servicio implementa las reglas de negocio de la prueba técnica:
1. Disponibilidad de tecnologías: 2G >= 0, 3G >= 0, 4G >= 0.
2. Capacidad al límite: Al menos una tecnología disponible debe tener un valor de 100.
3. Estado de notificación: El campo NOTIFICADA debe ser 'N'.
4. Nivel de criticidad según el tiempo transcurrido (duración acumulada):
   - CRÍTICO: Cumple condiciones base y duración > 24 horas.
   - WARN: Cumple condiciones base y 1 hora < duración <= 24 horas.
   - NORMAL: No cumple condiciones base o duración <= 1 hora.
"""

from datetime import datetime
from typing import Tuple, Optional

CRITICO = "CRITICO"
WARN = "WARN"
NORMAL = "NORMAL"

def validar_condiciones_base(tech_2g: int, tech_3g: int, tech_4g: int, notificada: str) -> bool:
    """
    Evalúa si un registro de alarma satisface las tres condiciones base:
    1. Disponibilidad: 2G >= 0, 3G >= 0, 4G >= 0
    2. Capacidad al límite: alguna tecnología disponible tiene valor == 100
    3. Estado de notificación: notificada == 'N'
    """
    # Condición 1: Disponibilidad de tecnologías (no negativas)
    if tech_2g < 0 or tech_3g < 0 or tech_4g < 0:
        return False

    # Condición 2: Capacidad al límite (al menos una es 100)
    if not (tech_2g == 100 or tech_3g == 100 or tech_4g == 100):
        return False

    # Condición 3: Estado de notificación negativo ('N')
    if str(notificada).strip().upper() != "N":
        return False

    return True


def calcular_duracion_y_criticidad(
    fecha_creacion: datetime,
    tech_2g: int,
    tech_3g: int,
    tech_4g: int,
    notificada: str,
    fecha_referencia: Optional[datetime] = None
) -> Tuple[float, str, str, bool]:
    """
    Calcula la duración transcurrida desde la creación de la alarma hasta la fecha de referencia
    (por defecto la hora actual) y clasifica la criticidad según las reglas de negocio.

    Retorna una tupla:
    (duracion_segundos, duracion_formateada, criticidad, cumple_condiciones_base)
    """
    if fecha_referencia is None:
        fecha_referencia = datetime.now()

    # Cálculo de duración
    delta = fecha_referencia - fecha_creacion
    duracion_segundos = max(0.0, delta.total_seconds())
    duracion_horas = duracion_segundos / 3600.0

    # Formateo legible de duración
    dias = int(duracion_segundos // 86400)
    horas = int((duracion_segundos % 86400) // 3600)
    minutos = int((duracion_segundos % 3600) // 60)

    if dias > 0:
        duracion_formateada = f"{dias}d {horas}h {minutos}m"
    elif horas > 0:
        duracion_formateada = f"{horas}h {minutos}m"
    else:
        duracion_formateada = f"{minutos}m"

    # Evaluación de criticidad
    cumple_base = validar_condiciones_base(tech_2g, tech_3g, tech_4g, notificada)

    if cumple_base:
        if duracion_horas > 24.0:
            criticidad = CRITICO
        elif duracion_horas > 1.0:
            criticidad = WARN
        else:
            criticidad = NORMAL
    else:
        criticidad = NORMAL

    return duracion_segundos, duracion_formateada, criticidad, cumple_base
