import io
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.schemas.alarm import AlarmResponse

def exportar_alarmas_a_excel(alarmas: List[AlarmResponse], filtro_aplicado: str) -> io.BytesIO:
    """
    Genera un archivo Excel (.xlsx) en memoria con la información exacta que se está
    visualizando en la tabla, respetando los filtros aplicados.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Alarmas Filtradas"

    # Estilos
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")

    thin_border = Border(
        left=Side(style='thin', color='E5E7EB'),
        right=Side(style='thin', color='E5E7EB'),
        top=Side(style='thin', color='E5E7EB'),
        bottom=Side(style='thin', color='E5E7EB')
    )

    # Fila de Título y Filtro
    ws.merge_cells("A1:J1")
    title_cell = ws["A1"]
    title_cell.value = f"REPORTE DE ALARMAS - VISTA: {filtro_aplicado.upper()}"
    title_cell.font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 25

    # Encabezados
    headers = [
        "ID ALARMA",
        "2G (%)",
        "3G (%)",
        "4G (%)",
        "FECHA CREACIÓN",
        "MUNICIPIO",
        "DEPARTAMENTO",
        "NOTIFICADA",
        "DURACIÓN ACUMULADA",
        "CRITICIDAD"
    ]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    ws.row_dimensions[3].height = 22

    # Filas de Datos
    fill_critico = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    font_critico = Font(name="Calibri", color="991B1B", bold=True)

    fill_warn = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    font_warn = Font(name="Calibri", color="92400E", bold=True)

    fill_normal = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
    font_normal = Font(name="Calibri", color="374151")

    for row_idx, item in enumerate(alarmas, start=4):
        cells = [
            ws.cell(row=row_idx, column=1, value=item.id_alarma),
            ws.cell(row=row_idx, column=2, value=item.tech_2g),
            ws.cell(row=row_idx, column=3, value=item.tech_3g),
            ws.cell(row=row_idx, column=4, value=item.tech_4g),
            ws.cell(row=row_idx, column=5, value=item.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")),
            ws.cell(row=row_idx, column=6, value=item.municipio),
            ws.cell(row=row_idx, column=7, value=item.departamento),
            ws.cell(row=row_idx, column=8, value=item.notificada),
            ws.cell(row=row_idx, column=9, value=item.duracion_formato),
            ws.cell(row=row_idx, column=10, value=item.criticidad)
        ]

        # Alineación y bordes
        for c in cells:
            c.border = thin_border
            c.alignment = center_align

        # Estilo según criticidad en la celda de criticidad
        crit_cell = cells[9]
        if item.criticidad == "CRITICO":
            crit_cell.fill = fill_critico
            crit_cell.font = font_critico
        elif item.criticidad == "WARN":
            crit_cell.fill = fill_warn
            crit_cell.font = font_warn
        else:
            crit_cell.fill = fill_normal
            crit_cell.font = font_normal

        ws.row_dimensions[row_idx].height = 19

    # Ajuste automático del ancho de columnas
    for col_idx, col in enumerate(ws.columns, start=1):
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
