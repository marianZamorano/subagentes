"""HOOK 1 · PreToolUse (Edit|Write)
Bloquea cualquier intento de modificar las pruebas o archivos de secretos.

Entrada (stdin): JSON con tool_name y tool_input.file_path
Salida:  exit 0 → se permite  |  exit 2 → se BLOQUEA y el mensaje de stderr le llega a Claude
"""
import json
import sys

sys.stderr.reconfigure(encoding="utf-8")

datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
ruta = datos.get("tool_input", {}).get("file_path", "").replace("\\", "/")
nombre = ruta.rsplit("/", 1)[-1]

if "/tests/" in ruta:
    print(
        f"⛔ BLOQUEADO por hook: '{nombre}' es una prueba y las pruebas están protegidas. "
        "Las pruebas definen las reglas de negocio: si una falla, corrige el código, no la prueba.",
        file=sys.stderr,
    )
    sys.exit(2)

if nombre.startswith(".env"):
    print(f"⛔ BLOQUEADO por hook: '{nombre}' contiene secretos y no se puede modificar.", file=sys.stderr)
    sys.exit(2)

sys.exit(0)
