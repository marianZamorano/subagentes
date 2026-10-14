"""HOOK 3 (Codex) · PostToolUse (apply_patch)
Después de CADA parche a un archivo .py ejecuta las pruebas automáticamente.

Si fallan → exit 2: Codex reemplaza el resultado de la edición por este reporte y el modelo se corrige.
Si pasan  → JSON con "additionalContext": el modelo sabe que las pruebas pasaron.
"""
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
parche = datos.get("tool_input", {}).get("command", "")
rutas = re.findall(r"^\*\*\* (?:Add|Update) File: (.+)$", parche, re.MULTILINE)

if not any(r.strip().endswith(".py") for r in rutas):
    sys.exit(0)  # No se tocó código Python: no hay nada que probar

# Codex ejecuta el hook en la carpeta de la sesión (C:\UPB\hooks)
proyecto = os.path.join(datos.get("cwd") or os.getcwd(), "proyecto-demo")
resultado = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    cwd=proyecto,
    capture_output=True,
    text=True,
    encoding="utf-8",
    timeout=50,
)
salida = resultado.stderr.strip()  # unittest escribe su reporte en stderr

if resultado.returncode != 0:
    print(
        "❌ El hook ejecutó las pruebas después de tu cambio y FALLARON.\n"
        "Revisa el error y corrige el código (las pruebas no se pueden modificar):\n\n"
        + salida[-3000:],
        file=sys.stderr,
    )
    sys.exit(2)

total = next((l for l in salida.splitlines() if l.startswith("Ran ")), "")
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": f"✅ Hook de pruebas: {total} → OK",
    }
}, ensure_ascii=False))
sys.exit(0)
