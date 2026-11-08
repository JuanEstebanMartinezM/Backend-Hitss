from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alarm import AlarmModel
from app.schemas.alarm import (
    AlarmResponse,
    AlarmListResponse,
    DailySummaryResponse,
    UploadResponse
)
from app.services.csv_parser import procesar_archivo_csv
from app.services.classifier import calcular_duracion_y_criticidad
from app.services.summary import obtener_resumen_dia
from app.services.excel_exporter import exportar_alarmas_a_excel

router = APIRouter(prefix="/api/alarms", tags=["Alarmas"])


def _procesar_alarmas_en_memoria(
    alarmas_db: List[AlarmModel],
    filtro_status: str = "ALL",
    busqueda: Optional[str] = None
) -> tuple[List[AlarmResponse], int, int, int]:
    """
    Función de un solo paso (Single Pass O(N)) que:
    1. Calcula la duración acumulada y criticidad de cada alarma en tiempo real.
    2. Acumula los contadores globales (CRITICO, WARN, NORMAL).
    3. Aplica los filtros de búsqueda y estado a los registros resultantes.
    """
    ahora = datetime.now()
    filtradas: List[AlarmResponse] = []
    total_critico = 0
    total_warn = 0
    total_normal = 0

    term = busqueda.lower().strip() if busqueda else None
    status_target = filtro_status.upper()

    for item in alarmas_db:
        segundos, formato, criticidad, cumple_base = calcular_duracion_y_criticidad(
            fecha_creacion=item.fecha_creacion,
            tech_2g=item.tech_2g,
            tech_3g=item.tech_3g,
            tech_4g=item.tech_4g,
            notificada=item.notificada,
            fecha_referencia=ahora
        )

        # Acumular métricas globales
        if criticidad == "CRITICO":
            total_critico += 1
        elif criticidad == "WARN":
            total_warn += 1
        else:
            total_normal += 1

        # Filtro de búsqueda textual
        if term:
            coincide = (
                term in str(item.id_alarma) or
                term in item.municipio.lower() or
                term in item.departamento.lower()
            )
            if not coincide:
                continue

        # Filtro de estado
        if status_target != "ALL" and criticidad != status_target:
            continue

        filtradas.append(AlarmResponse(
            id_alarma=item.id_alarma,
            tech_2g=item.tech_2g,
            tech_3g=item.tech_3g,
            tech_4g=item.tech_4g,
            fecha_creacion=item.fecha_creacion,
            municipio=item.municipio,
            departamento=item.departamento,
            notificada=item.notificada,
            duracion_segundos=segundos,
            duracion_formato=formato,
            criticidad=criticidad,
            cumple_condiciones_base=cumple_base
        ))

    return filtradas, total_critico, total_warn, total_normal


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Requerimiento 1: Recibe e importa un archivo CSV separado por '|' desde la web.
    """
    if not file.filename.lower().endswith(('.csv', '.txt')):
        raise HTTPException(
            status_code=400,
            detail="Formato de archivo no soportado. Debe ser un archivo .csv o .txt delimitado por '|'."
        )

    try:
        contenido = await file.read()
        registros, errores = procesar_archivo_csv(contenido)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al analizar el archivo: {str(e)}")

    if not registros:
        raise HTTPException(status_code=400, detail="No se encontraron registros válidos en el archivo.")

    # Reemplazar datos existentes con la nueva importación
    try:
        db.query(AlarmModel).delete()

        model_objects = [
            AlarmModel(
                id_alarma=r["id_alarma"],
                tech_2g=r["tech_2g"],
                tech_3g=r["tech_3g"],
                tech_4g=r["tech_4g"],
                fecha_creacion=r["fecha_creacion"],
                municipio=r["municipio"],
                departamento=r["departamento"],
                notificada=r["notificada"]
            )
            for r in registros
        ]
        db.bulk_save_objects(model_objects)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al persistir registros en base de datos: {str(e)}")

    return UploadResponse(
        message=f"Archivo '{file.filename}' procesado exitosamente.",
        total_procesadas=len(registros) + len(errores),
        total_guardadas=len(registros)
    )


@router.post("/seed-demo", response_model=UploadResponse)
def seed_demo_alarms(db: Session = Depends(get_db)):
    """
    Inyecta registros de prueba en tiempo real para demostrar el distintivo WARN (1h a 24h)
    y registros con fecha de HOY en el módulo de Resumen Diario durante la sustentación.
    """
    ahora = datetime.now()
    demo_items = [
        AlarmModel(
            id_alarma=9999001,
            tech_2g=0,
            tech_3g=0,
            tech_4g=100,
            fecha_creacion=ahora - timedelta(hours=3, minutes=15),
            municipio="Medellín",
            departamento="Antioquia",
            notificada="N"
        ),
        AlarmModel(
            id_alarma=9999002,
            tech_2g=50,
            tech_3g=100,
            tech_4g=20,
            fecha_creacion=ahora - timedelta(hours=8, minutes=45),
            municipio="Bogotá, D.C.",
            departamento="Cundinamarca",
            notificada="N"
        ),
        AlarmModel(
            id_alarma=9999003,
            tech_2g=100,
            tech_3g=0,
            tech_4g=0,
            fecha_creacion=ahora - timedelta(minutes=25),
            municipio="Cali",
            departamento="Valle del Cauca",
            notificada="N"
        )
    ]

    # Eliminar previos con estos IDs si existen
    db.query(AlarmModel).filter(AlarmModel.id_alarma.in_([9999001, 9999002, 9999003])).delete(synchronize_session=False)
    db.add_all(demo_items)
    db.commit()

    return UploadResponse(
        message="Se inyectaron 3 alarmas de demostración (2 WARN y 1 NORMAL < 1h) con fecha de hoy.",
        total_procesadas=3,
        total_guardadas=3
    )


@router.get("", response_model=AlarmListResponse)
def get_alarms(
    status: str = Query("ALL", description="Filtro de estado: ALL, CRITICO, WARN, NORMAL"),
    search: Optional[str] = Query(None, description="Búsqueda por texto en ID, municipio o departamento"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=1000, description="Cantidad de registros por página"),
    db: Session = Depends(get_db)
):
    """
    Requerimiento 1 y 2: Lista alarmas con duración acumulada en tiempo real y filtros activos.
    """
    todas_db = db.query(AlarmModel).order_by(AlarmModel.fecha_creacion.desc()).all()

    # Procesar y filtrar en un solo paso
    filtradas, total_critico, total_warn, total_normal = _procesar_alarmas_en_memoria(
        todas_db, filtro_status=status, busqueda=search
    )

    # Paginación
    inicio = (page - 1) * page_size
    fin = inicio + page_size
    items_paginados = filtradas[inicio:fin]

    return AlarmListResponse(
        items=items_paginados,
        total=len(filtradas),
        total_critico=total_critico,
        total_warn=total_warn,
        total_normal=total_normal
    )


@router.get("/summary", response_model=DailySummaryResponse)
def get_summary(
    fecha: Optional[str] = Query(None, description="Fecha a consultar en formato YYYY-MM-DD. Por defecto: hoy."),
    db: Session = Depends(get_db)
):
    """
    Requerimiento 4: Módulo de Resumen del Día agrupado por franjas horarias.
    """
    return obtener_resumen_dia(db, fecha_filtro=fecha)


@router.get("/export")
def export_excel(
    status: str = Query("ALL", description="Filtro de estado aplicado: ALL, CRITICO, WARN, NORMAL"),
    search: Optional[str] = Query(None, description="Búsqueda por texto"),
    db: Session = Depends(get_db)
):
    """
    Requerimiento 3 (Exportación): Exporta a Excel la información exacta visible en la tabla.
    """
    todas_db = db.query(AlarmModel).order_by(AlarmModel.fecha_creacion.desc()).all()
    filtradas, _, _, _ = _procesar_alarmas_en_memoria(todas_db, filtro_status=status, busqueda=search)

    excel_buffer = exportar_alarmas_a_excel(filtradas, filtro_aplicado=status)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reporte_alarmas_{status.lower()}_{timestamp}.xlsx"

    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
