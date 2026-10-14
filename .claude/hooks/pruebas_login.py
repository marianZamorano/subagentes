"""HOOK 5 · PreToolUse (Bash|PowerShell) + PostToolUse (Edit|Write)
Los hooks originales solo prueban proyecto-demo/. Este hook cubre login-app/:

- PostToolUse: tras editar un .py de login-app/ ejecuta sus pruebas.
  Si fallan → exit 2 y Claude recibe el reporte para corregir el código.
- PreToolUse: antes de un `git push` ejecuta las pruebas de login-app/.
  Si fallan → exit 2 y el push se BLOQUEA (así el CI nunca recibe código roto).
"""
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
evento = datos.get("hook_event_name", "")
entrada = datos.get("tool_input", {}) or {}
raiz = os.environ.get("CLAUDE_PROJECT_DIR") or datos.get("cwd") or "."

if evento == "PreToolUse":
    comando = entrada.get("command", "")
    if not re.search(r"\bgit(?:\.exe)?\b[^\r\n;&|]*\bpush\b", comando, re.IGNORECASE):
        sys.exit(0)
else:
    ruta = entrada.get("file_path", "").replace("\\", "/")
    if "/login-app/" not in ruta or not ruta.endswith(".py"):
        sys.exit(0)

try:
    resultado = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=os.path.join(raiz, "login-app"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=50,
    )
except (OSError, subprocess.TimeoutExpired) as error:
    print(f"⛔ Hook login-app: no se pudieron ejecutar las pruebas: {error}", file=sys.stderr)
    sys.exit(2)

salida = resultado.stderr.strip()  # unittest escribe su reporte en stderr
if resultado.returncode != 0 or not re.search(r"Ran [1-9]\d* tests?\b", salida):
    accion = "PUSH BLOQUEADO" if evento == "PreToolUse" else "Tu cambio rompió las pruebas"
    print(
        f"⛔ {accion}: las pruebas de login-app/ fallaron.\n"
        "Corrige el código de login-app/backend (los tests están protegidos), "
        "vuelve a ejecutar las pruebas, crea un commit y reintenta el push.\n\n" + salida[-4000:],
        file=sys.stderr,
    )
    sys.exit(2)

total = next((l for l in salida.splitlines() if l.startswith("Ran ")), "")
print(json.dumps({"systemMessage": f"✅ Hook login-app: {total} → OK"}, ensure_ascii=False))
sys.exit(0)
