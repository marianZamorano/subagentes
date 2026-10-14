"""Lógica de cuentas de usuario: registro e inicio de sesión sobre SQLite.

Reglas de negocio:
- El usuario debe tener entre 3 y 30 caracteres (letras, números o _).
- La contraseña debe tener 8 caracteres o más.
- No pueden existir dos usuarios con el mismo nombre (sin distinguir mayúsculas).
- Las contraseñas se guardan con hash PBKDF2 + sal, nunca en texto plano.
"""
import hashlib
import hmac
import re
import secrets
import sqlite3

LARGO_MINIMO_PASSWORD = 8
PATRON_USUARIO = re.compile(r"^[A-Za-z0-9_]{3,30}$")
ITERACIONES = 100_000


class ErrorAuth(Exception):
    """Error de validación o de credenciales que se muestra al usuario."""


def conectar(ruta_db="usuarios.db"):
    conexion = sqlite3.connect(ruta_db, check_same_thread=False)
    conexion.execute(
        """CREATE TABLE IF NOT EXISTS usuarios (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
               sal TEXT NOT NULL,
               hash TEXT NOT NULL
           )"""
    )
    conexion.execute(
        """CREATE TABLE IF NOT EXISTS sesiones (
               token TEXT PRIMARY KEY,
               usuario_id INTEGER NOT NULL REFERENCES usuarios(id)
           )"""
    )
    conexion.commit()
    return conexion


def _hashear(password, sal):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(sal), ITERACIONES).hex()


def validar_password(password):
    """Devuelve True si la contraseña tiene 8 caracteres o más."""
    return len(password) >= LARGO_MINIMO_PASSWORD


def registrar(conexion, usuario, password):
    """Crea la cuenta y devuelve su id. Lanza ErrorAuth si los datos no son válidos."""
    usuario = (usuario or "").strip()
    password = password or ""
    if not PATRON_USUARIO.match(usuario):
        raise ErrorAuth("El usuario debe tener de 3 a 30 caracteres (letras, números o _).")
    if not validar_password(password):
        raise ErrorAuth(f"La contraseña debe tener al menos {LARGO_MINIMO_PASSWORD} caracteres.")

    sal = secrets.token_hex(16)
    try:
        cursor = conexion.execute(
            "INSERT INTO usuarios (usuario, sal, hash) VALUES (?, ?, ?)",
            (usuario, sal, _hashear(password, sal)),
        )
    except sqlite3.IntegrityError:
        raise ErrorAuth("Ese usuario ya existe.") from None
    conexion.commit()
    return cursor.lastrowid


def iniciar_sesion(conexion, usuario, password):
    """Valida las credenciales y devuelve un token de sesión nuevo."""
    fila = conexion.execute(
        "SELECT id, sal, hash FROM usuarios WHERE usuario = ?", ((usuario or "").strip(),)
    ).fetchone()
    # Mismo mensaje para usuario inexistente y contraseña errónea: no revela qué cuentas existen.
    if fila is None or not hmac.compare_digest(_hashear(password or "", fila[1]), fila[2]):
        raise ErrorAuth("Usuario o contraseña incorrectos.")

    token = secrets.token_urlsafe(32)
    conexion.execute("INSERT INTO sesiones (token, usuario_id) VALUES (?, ?)", (token, fila[0]))
    conexion.commit()
    return token


def usuario_de_token(conexion, token):
    """Devuelve el nombre de usuario dueño del token, o None si no es válido."""
    fila = conexion.execute(
        "SELECT u.usuario FROM sesiones s JOIN usuarios u ON u.id = s.usuario_id WHERE s.token = ?",
        (token or "",),
    ).fetchone()
    return fila[0] if fila else None


def cerrar_sesion(conexion, token):
    conexion.execute("DELETE FROM sesiones WHERE token = ?", (token or "",))
    conexion.commit()
