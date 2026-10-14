import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import auth  # noqa: E402


class PruebasAuth(unittest.TestCase):
    def setUp(self):
        self.db = auth.conectar(":memory:")

    def tearDown(self):
        self.db.close()

    def test_1_registro_exitoso_guarda_hash(self):
        auth.registrar(self.db, "marian", "clave-segura")
        sal, hash_guardado = self.db.execute("SELECT sal, hash FROM usuarios WHERE usuario = 'marian'").fetchone()
        self.assertNotEqual(hash_guardado, "clave-segura")
        self.assertTrue(sal)

    def test_2_usuario_duplicado_falla(self):
        auth.registrar(self.db, "marian", "clave-segura")
        with self.assertRaises(auth.ErrorAuth):
            auth.registrar(self.db, "MARIAN", "otra-clave-123")

    def test_3_password_de_8_caracteres_es_valida(self):
        # Regla de negocio: la contraseña debe tener 8 caracteres o más.
        self.assertTrue(auth.validar_password("12345678"))
        self.assertFalse(auth.validar_password("1234567"))

    def test_4_login_correcto_devuelve_token_valido(self):
        auth.registrar(self.db, "marian", "clave-segura")
        token = auth.iniciar_sesion(self.db, "marian", "clave-segura")
        self.assertEqual(auth.usuario_de_token(self.db, token), "marian")

    def test_5_login_con_password_incorrecta_falla(self):
        auth.registrar(self.db, "marian", "clave-segura")
        with self.assertRaises(auth.ErrorAuth):
            auth.iniciar_sesion(self.db, "marian", "clave-mala")
        with self.assertRaises(auth.ErrorAuth):
            auth.iniciar_sesion(self.db, "nadie", "clave-segura")


if __name__ == "__main__":
    unittest.main()
