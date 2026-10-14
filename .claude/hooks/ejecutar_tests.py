"""HOOK 3 · PostToolUse (Edit|Write)
Después de CADA edición a un archivo .py ejecuta las pruebas automáticamente.

Si fallan → exit 2: el resultado le llega a Claude, que se corrige solo.
Si pasan  → exit 0 + JSON con "systemMessage": el usuario ve un aviso verde.
"""
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
ruta = datos.get("tool_input", {}).get("file_path", "")

if not ruta.endswith(".py"):
    sys.exit(0)  # No es código Python: no hay nada que probar

proyecto = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), "proyecto-demo")
resultado = subprocess.run(
    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    cwd=proyecto,
    capture_output=True,
    text=True,
    encoding="utf-8",
    timeout=50,
)
salida = resultado.stderr.strip()  # unittest escribe su reporte en stderr
resumen = salida.splitlines()[-1] if salida else ""

if resultado.returncode != 0:
    print(
        "❌ El hook ejecutó las pruebas después de tu cambio y FALLARON.\n"
        "Revisa el error y corrige el código (las pruebas no se pueden modificar):\n\n"
        + salida[-3000:],
        file=sys.stderr,
    )
    sys.exit(2)

total = next((l for l in salida.splitlines() if l.startswith("Ran ")), "")
print(json.dumps({"systemMessage": f"✅ Hook de pruebas: {total} → {resumen}"}, ensure_ascii=False))
sys.exit(0)
