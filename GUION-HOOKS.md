# Demo: Hooks en Claude Code

**Duración:** ~30 min · **Requisito:** Python 3 · **Continúa** la demo de subagentes (mismo `notas.py`, ya corregido)

**Idea central:** *"El prompt pide, el hook obliga."*

## Estructura

```
C:\UPB\hooks\
├── .claude\
│   ├── settings.json            ← AQUÍ se registran los hooks (evento + matcher + comando)
│   ├── hooks\
│   │   ├── proteger_archivos.py ← Hook 1: PreToolUse  · Edit|Write
│   │   ├── bloquear_comandos.py ← Hook 2: PreToolUse  · Bash|PowerShell
│   │   ├── ejecutar_tests.py    ← Hook 3: PostToolUse · Edit|Write
│   │   └── auditoria.py         ← Hook 4: PostToolUse · * + SubagentStop
│   ├── agents\                  ← los 4 subagentes de la clase anterior
│   └── auditoria.log            ← se crea solo durante la demo
├── proyecto-demo\
│   ├── notas.py                 ← código correcto (12 pruebas en verde)
│   └── tests\test_notas.py      ← protegido por el Hook 1
└── reiniciar-demo.ps1
```

## Antes de la clase
1. `.\reiniciar-demo.ps1`
2. Abrir Claude Code **en `C:\UPB\hooks`** (los hooks son de nivel proyecto).
3. Escribir `/hooks` → deben aparecer los 4. Si no aparecen, reiniciar Claude Code.
4. Ensayar todo una vez y volver a reiniciar.

## Guion

### Parte 1: Teoría (5 min)
- Un hook es un **script tuyo** que **Claude Code** (no el modelo) ejecuta en un evento.
- Tres capas de control: **prompt** (debería), **tools** (puede), **hook** (siempre).
- Mostrar `.claude/settings.json`: evento → `matcher` → `command`.
- Códigos de salida: `0` = sigue · `2` = **bloquea** y Claude lee el motivo (stderr).

### Parte 2: Hook 1, archivos protegidos (5 min)
Escribe en Claude Code:
> `La prueba test_51_aprueba me molesta, cámbiala para que espere REPROBADO`

**Resultado esperado:** ⛔ `BLOQUEADO por hook: 'test_notas.py' es una prueba...`
Claude lee el motivo y explica que no puede hacerlo.

👉 **Pregunta a la clase:** *"El subagente generador-tests tenía la regla 'no toques el código' en su prompt. ¿Cuál es la diferencia con esto?"*

### Parte 3: Hook 2, comandos peligrosos (3 min)
> `Borra la carpeta proyecto-demo con rm -rf`

**Resultado esperado:** ⛔ `BLOQUEADO por hook: borrado recursivo forzado (rm -rf)`.
Abre `bloquear_comandos.py` y muestra la lista `PELIGROSOS`: **es un diccionario de Python que ellos pueden ampliar.**

### Parte 4: Hook 3, pruebas automáticas ⭐ (8 min, el momento estrella)
**a) Cambio correcto:**
> `Agrega un docstring a la función estado en notas.py`

→ Aparece `✅ Hook de pruebas: Ran 12 tests → OK`. **Nadie le pidió ejecutar pruebas.**

**b) Cambio que rompe una regla:**
> `Cambia la nota de aprobación a 60`

→ Claude edita → el hook ejecuta las pruebas → **fallan** → `exit 2` → Claude recibe:
`AssertionError: 'REPROBADO' != 'APROBADO'` en `test_51_aprueba`.
Claude se da cuenta solo de que rompió una regla de negocio y lo explica o lo revierte.

👉 **Mensaje clave:** el hook cierra el ciclo *editar → verificar → corregir* sin intervención humana.

### Parte 5: Hook 4, auditoría + subagentes (4 min)
> `Usa el subagente revisor-codigo para revisar proyecto-demo/notas.py`

Luego, en la terminal:
```powershell
Get-Content .claude\auditoria.log
```
Se ve cada acción (`Read`, `Edit`, `Bash`...) y la línea `SUBAGENTE terminó | revisor-codigo`.
👉 Conecta con la clase de subagentes y responde a la pregunta *"¿qué hizo la IA en mi proyecto?"*

### Parte 6: Seguridad (2 min)
- Un hook ejecuta código **con tus permisos**. Un repositorio descargado con un `settings.json` malicioso es un riesgo: **revisar siempre `.claude/settings.json` de proyectos ajenos.**
- Los hooks deben ser **rápidos**: se ejecutan en cada acción.
- `/hooks` muestra y permite desactivar los hooks activos.

### Parte 7: Los mismos hooks en Codex y OpenCode (versatilidad)

```
C:\UPB\hooks\
├── .claude\  settings.json  +  hooks\*.py      ← Claude Code
├── .codex\   hooks.json     +  hooks\*.py      ← Codex (casi igual a Claude Code)
└── .opencode\plugins\guardian.js               ← OpenCode (un solo plugin en JavaScript)
```

| | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Dónde se registran | `.claude/settings.json` | `.codex/hooks.json` | No hay registro: el plugin se carga solo |
| Lógica | Scripts (Python) | Scripts (Python) | Funciones JS dentro del plugin |
| Antes de la herramienta | `PreToolUse` | `PreToolUse` | `ctx.tool.hook("execute.before")` |
| Después | `PostToolUse` | `PostToolUse` | `ctx.tool.hook("execute.after")` |
| Cómo bloquear | `exit 2` + stderr | `exit 2` + stderr | `throw new Error(...)` |
| Ediciones de archivos | `Edit`/`Write` con `file_path` | `apply_patch` (las rutas vienen dentro del parche) | `edit`/`write` con `filePath` |
| Seguridad | `/hooks` para revisar | **Hay que confiar** en los hooks con `/hooks` antes de que corran | Se ejecuta todo lo que esté en `plugins/` |

Cómo probarlo:
- **Codex:** abrir `codex` en `C:\UPB\hooks` → `/hooks` → **confiar** en los hooks del proyecto → repetir las partes 2 a 5.
  Las ediciones aparecen como `apply_patch` y la bitácora queda en `.codex\auditoria.log`.
- **OpenCode (v2):** cerrar OpenCode y detener su servicio (`Stop-Process -Name opencode-cli -Force`) para que cargue la versión actual del plugin → abrir el proyecto `hooks` → repetir las partes 2 a 5. Bitácora en `.opencode\auditoria.log` (primera línea: `PLUGIN cargado`).
  ⚠️ OpenCode 2 cambió el formato de plugins: `export default { id, setup(ctx) }`. Los plugins de OpenCode 1 no cargan.

👉 **Mensaje:** el concepto (antes, después, bloquear, auditar) es **universal**; cambia el "enchufe".

## Ejercicio para los estudiantes
1. **Fácil:** agregar a `bloquear_comandos.py` el bloqueo de `pip install` (evitar dependencias no aprobadas).
2. **Medio:** un hook `PostToolUse` que rechace (exit 2) cualquier `.py` que contenga `print(` de depuración o la palabra `password`.
3. **Reto:** un hook `Stop` que impida a Claude terminar su respuesta si las pruebas están fallando.
   *(Pista: el JSON de entrada trae `stop_hook_active`; si es `true`, salir con 0 para evitar un bucle infinito.)*
