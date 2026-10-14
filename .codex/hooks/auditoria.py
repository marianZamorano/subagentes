"""HOOK 4 (Codex) · PostToolUse (*) + SubagentStop
Registra en .codex/auditoria.log cada acción de Codex y cada subagente que termina.
Importante: en SubagentStop Codex solo acepta JSON en stdout, así que este hook NO imprime nada.
"""
import json
import os
import re
import sys
from datetime import datetime

datos = json.loads(sys.stdin.buffer.read().decode("utf-8"))
evento = datos.get("hook_event_name", "?")
entrada = datos.get("tool_input", {}) or {}

if evento == "SubagentStop":
    accion = "SUBAGENTE terminó"
    detalle = datos.get("agent_type") or datos.get("agent_name") or datos.get("agent_id", "")
else:
    accion = datos.get("tool_name", "?")
    comando = str(entrada.get("command", ""))
    if accion == "apply_patch":  # en un parche, mostrar solo los archivos tocados
        comando = ", ".join(re.findall(r"^\*\*\* \w+ File: (.+)$", comando, re.MULTILINE))
    detalle = comando

detalle = str(detalle).replace("\n", " ")[:120]
linea = f"{datetime.now():%Y-%m-%d %H:%M:%S} | {accion:<18} | {detalle}\n"

log = os.path.join(datos.get("cwd") or os.getcwd(), ".codex", "auditoria.log")
with open(log, "a", encoding="utf-8") as f:
    f.write(linea)

sys.exit(0)
