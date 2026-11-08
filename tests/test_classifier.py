import unittest
from datetime import datetime, timedelta
import sys
import os

# Asegurar que el directorio raíz de backend esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.classifier import (
    validar_condiciones_base,
    calcular_duracion_y_criticidad,
    CRITICO,
    WARN,
    NORMAL
)

class TestClassifier(unittest.TestCase):

    def test_validar_condiciones_base_exitoso(self):
        # Cumple: todos >= 0, al menos uno es 100, notificada == 'N'
        self.assertTrue(validar_condiciones_base(0, 0, 100, 'N'))
        self.assertTrue(validar_condiciones_base(100, 50, 20, 'N'))
        self.assertTrue(validar_condiciones_base(100, 100, 100, 'N'))

    def test_validar_condiciones_base_tecnologia_negativa(self):
        # Falla: 2G es -100
        self.assertFalse(validar_condiciones_base(-100, 100, 50, 'N'))
        # Falla: 3G es -100
        self.assertFalse(validar_condiciones_base(0, -100, 100, 'N'))

    def test_validar_condiciones_base_sin_limite_100(self):
        # Falla: ninguna tecnología alcanza 100
        self.assertFalse(validar_condiciones_base(99, 99, 99, 'N'))
        self.assertFalse(validar_condiciones_base(0, 0, 0, 'N'))

    def test_validar_condiciones_base_notificada_si(self):
        # Falla: ya fue notificada ('S')
        self.assertFalse(validar_condiciones_base(0, 0, 100, 'S'))

    def test_clasificacion_critico(self):
        # Cumple base y tiene más de 24 horas
        ahora = datetime(2026, 11, 7, 12, 0, 0)
        fecha_creacion = ahora - timedelta(hours=25)
        segundos, formato, criticidad, cumple = calcular_duracion_y_criticidad(
            fecha_creacion, 0, 0, 100, 'N', fecha_referencia=ahora
        )
        self.assertTrue(cumple)
        self.assertEqual(criticidad, CRITICO)
        self.assertEqual(segundos, 25 * 3600)
        self.assertIn("1d 1h 0m", formato)

    def test_clasificacion_warn(self):
        # Cumple base y tiene entre 1 y 24 horas
        ahora = datetime(2026, 11, 7, 12, 0, 0)
        fecha_creacion = ahora - timedelta(hours=5, minutes=30)
        segundos, formato, criticidad, cumple = calcular_duracion_y_criticidad(
            fecha_creacion, 0, 0, 100, 'N', fecha_referencia=ahora
        )
        self.assertTrue(cumple)
        self.assertEqual(criticidad, WARN)
        self.assertIn("5h 30m", formato)

    def test_clasificacion_normal_menor_una_hora(self):
        # Cumple base pero duración <= 1 hora -> NORMAL
        ahora = datetime(2026, 11, 7, 12, 0, 0)
        fecha_creacion = ahora - timedelta(minutes=45)
        segundos, formato, criticidad, cumple = calcular_duracion_y_criticidad(
            fecha_creacion, 0, 0, 100, 'N', fecha_referencia=ahora
        )
        self.assertTrue(cumple)
        self.assertEqual(criticidad, NORMAL)

    def test_clasificacion_normal_no_cumple_base_aunque_antigua(self):
        # Duración de 50 horas pero NOTIFICADA == 'S' -> NORMAL
        ahora = datetime(2026, 11, 7, 12, 0, 0)
        fecha_creacion = ahora - timedelta(hours=50)
        segundos, formato, criticidad, cumple = calcular_duracion_y_criticidad(
            fecha_creacion, 0, 0, 100, 'S', fecha_referencia=ahora
        )
        self.assertFalse(cumple)
        self.assertEqual(criticidad, NORMAL)

if __name__ == '__main__':
    unittest.main()
