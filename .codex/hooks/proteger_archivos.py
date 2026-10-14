"""HOOK 1 (Codex) · PreToolUse (apply_patch)
Bloquea cualquier intento de modificar las pruebas o archivos de secretos.

Diferencia con Claude Code: Codex no manda "file_path". Edita con un parche (apply_patch)
y las rutas vienen dentro del texto, en líneas como "*** Update File: ruta".
Salida:  exit 0 → se permite  |  exit 2 → se BLOQUEA y el mensaje de stderr le llega al modelo
"""
import json
import re
import sys

sys.stderr.reconfigure(encoding="utf-8")

datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
parche = datos.get("tool_input", {}).get("command", "")
rutas = re.findall(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", parche, re.MULTILINE)

for ruta in rutas:
    ruta = ruta.strip().replace("\\", "/")
    nombre = ruta.rsplit("/", 1)[-1]

    if "tests/" in ruta:
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
