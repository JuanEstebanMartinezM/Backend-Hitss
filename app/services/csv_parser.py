import io
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd

# Mapeo de meses en español e inglés a formato numérico de dos dígitos
MESES_MAP = {
    "ENE": "01", "FEB": "02", "MAR": "03", "ABR": "04",
    "MAY": "05", "JUN": "06", "JUL": "07", "AGO": "08",
    "SEP": "09", "OCT": "10", "NOV": "11", "DIC": "12",
    "JAN": "01", "APR": "04", "AUG": "08", "DEC": "12"
}

def parse_fecha_alarma(fecha_str: str) -> datetime:
    """
    Parsea fechas en formato '09-OCT-26 10.12.56.000000000 PM' o formatos ISO estándar.
    """
    if not isinstance(fecha_str, str):
        raise ValueError(f"Fecha inválida: {fecha_str}")

    cleaned = fecha_str.strip()

    # Si viene con precisión de nanosegundos (ej: .000000000), se eliminan los decimales de segundos
    cleaned = re.sub(r'\.\d{6,9}', '', cleaned)

    # Caso formato Oracle: '09-OCT-26 10.12.56 PM'
    match = re.match(r'^(\d{1,2})-([A-Za-z]{3})-(\d{2})\s+(\d{1,2})\.(\d{2})\.(\d{2})\s+([APap][Mm])$', cleaned)
    if match:
        dia, mes_str, anio_2d, hora, minuto, segundo, ampm = match.groups()
        mes_num = MESES_MAP.get(mes_str.upper(), "01")
        anio_4d = f"20{anio_2d}"
        iso_str = f"{anio_4d}-{mes_num}-{dia.zfill(2)} {hora.zfill(2)}:{minuto}:{segundo} {ampm.upper()}"
        return datetime.strptime(iso_str, "%Y-%m-%d %I:%M:%S %p")

    # Intentos de fallback con formatos datetime estándar
    formatos_fallback = [
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %I:%M:%S %p",
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S"
    ]
    for fmt in formatos_fallback:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    raise ValueError(f"No se pudo parsear el formato de fecha: '{fecha_str}'")


def procesar_archivo_csv(contenido_bytes: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Lee los bytes del archivo CSV subido por el usuario, detecta codificación y procesa las filas.
    Retorna una tupla: (lista_de_registros_validos, lista_de_advertencias_o_errores).
    """
    errores = []
    registros = []

    if not contenido_bytes or not contenido_bytes.strip():
        raise ValueError("El archivo subido se encuentra vacío.")

    # Decodificar bytes (intentando utf-8-sig, utf-8 y latin-1 para compatibilidad)
    try:
        texto = contenido_bytes.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            texto = contenido_bytes.decode('utf-8')
        except UnicodeDecodeError:
            texto = contenido_bytes.decode('latin-1')

    # Detectar delimitador (por defecto '|' como especifica la prueba)
    delimitador = '|'
    primera_linea = texto.splitlines()[0] if texto.splitlines() else ""
    if '|' not in primera_linea and ';' in primera_linea:
        delimitador = ';'
    elif '|' not in primera_linea and ',' in primera_linea:
        delimitador = ','

    df = pd.read_csv(io.StringIO(texto), sep=delimitador, dtype=str)

    # Limpiar nombres de columnas (quitar comillas y espacios)
    df.columns = [col.strip().strip('"').strip("'").upper() for col in df.columns]

    columnas_requeridas = {"ID_ALARMA", "2G", "3G", "4G", "FECHA_CREACION", "MUNICIPIO", "DEPARTAMENTO", "NOTIFICADA"}
    columnas_faltantes = columnas_requeridas - set(df.columns)
    if columnas_faltantes:
        raise ValueError(f"El archivo carece de las siguientes columnas requeridas: {', '.join(sorted(columnas_faltantes))}")

    for idx, row in df.iterrows():
        fila_num = idx + 2  # Contando encabezado
        try:
            id_alarma = int(row["ID_ALARMA"].strip().strip('"'))
            tech_2g = int(row["2G"].strip().strip('"'))
            tech_3g = int(row["3G"].strip().strip('"'))
            tech_4g = int(row["4G"].strip().strip('"'))
            fecha_creacion = parse_fecha_alarma(row["FECHA_CREACION"].strip().strip('"'))
            municipio = str(row["MUNICIPIO"]).strip().strip('"')
            departamento = str(row["DEPARTAMENTO"]).strip().strip('"')
            notificada = str(row["NOTIFICADA"]).strip().strip('"').upper()

            registros.append({
                "id_alarma": id_alarma,
                "tech_2g": tech_2g,
                "tech_3g": tech_3g,
                "tech_4g": tech_4g,
                "fecha_creacion": fecha_creacion,
                "municipio": municipio,
                "departamento": departamento,
                "notificada": notificada
            })
        except Exception as e:
            errores.append(f"Fila {fila_num}: Error al procesar - {str(e)}")

    return registros, errores
