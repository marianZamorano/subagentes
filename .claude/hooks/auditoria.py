"""HOOK 4 · PostToolUse (*) + SubagentStop
Registra en .claude/auditoria.log cada acción de Claude y cada subagente que termina.
Responde a la pregunta: "¿qué hizo la IA en mi proyecto?"
"""
import json
import os
import sys
from datetime import datetime

datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
evento = datos.get("hook_event_name", "?")
entrada = datos.get("tool_input", {}) or {}

if evento == "SubagentStop":
    accion = "SUBAGENTE terminó"
    detalle = datos.get("agent_type") or datos.get("subagent_type") or datos.get("agent_id", "")
else:
    accion = datos.get("tool_name", "?")
    detalle = entrada.get("file_path") or entrada.get("command") or entrada.get("pattern") or ""

detalle = str(detalle).replace("\n", " ")[:120]
linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {accion:<18} | {detalle}\n"

log = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), ".claude", "auditoria.log")
with open(log, "a", encoding="utf-8") as f:
    f.write(linea)

sys.exit(0)
