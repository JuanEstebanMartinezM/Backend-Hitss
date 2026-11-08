import unittest
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.csv_parser import parse_fecha_alarma, procesar_archivo_csv

class TestCsvParser(unittest.TestCase):

    def test_parse_fecha_oracle_formato_muestra(self):
        # Formato '09-OCT-26 10.12.56.000000000 PM'
        dt = parse_fecha_alarma('09-OCT-26 10.12.56.000000000 PM')
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 10)
        self.assertEqual(dt.day, 9)
        self.assertEqual(dt.hour, 22)
        self.assertEqual(dt.minute, 12)
        self.assertEqual(dt.second, 56)

    def test_parse_fecha_iso_fallback(self):
        # Formato ISO estándar '2026-11-04 19:38:43'
        dt = parse_fecha_alarma('2026-11-04 19:38:43')
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 11)
        self.assertEqual(dt.day, 4)
        self.assertEqual(dt.hour, 19)

    def test_parse_fecha_invalida_lanza_error(self):
        with self.assertRaises(ValueError):
            parse_fecha_alarma('fecha_completamente_invalida')

    def test_procesar_archivo_csv_valido(self):
        csv_content = (
            '"ID_ALARMA"|"2G"|"3G"|"4G"|"FECHA_CREACION"|"MUNICIPIO"|"DEPARTAMENTO"|"NOTIFICADA"\n'
            '4661427|0|0|100|10-OCT-26 06.37.53.000000000 PM|"Quetame"|"Cundinamarca"|"N"\n'
        ).encode('utf-8')

        registros, errores = procesar_archivo_csv(csv_content)
        self.assertEqual(len(errores), 0)
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["id_alarma"], 4661427)
        self.assertEqual(registros[0]["tech_4g"], 100)
        self.assertEqual(registros[0]["notificada"], "N")
        self.assertEqual(registros[0]["municipio"], "Quetame")

    def test_procesar_archivo_vacio_lanza_error(self):
        with self.assertRaises(ValueError):
            procesar_archivo_csv(b'')

    def test_procesar_archivo_columnas_faltantes(self):
        csv_incompleto = 'ID_ALARMA|2G|3G\n1|0|0\n'.encode('utf-8')
        with self.assertRaises(ValueError):
            procesar_archivo_csv(csv_incompleto)

if __name__ == '__main__':
    unittest.main()

