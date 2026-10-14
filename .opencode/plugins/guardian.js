// Hooks de OpenCode 2: los 4 hooks de la demo en UN plugin de JavaScript.
//
// Diferencia clave con Claude Code y Codex: no hay settings.json/hooks.json.
// El mismo archivo REGISTRA el evento y CONTIENE la lógica.
//   - ctx.tool.hook("execute.before") = PreToolUse  → lanzar un Error BLOQUEA la herramienta
//   - ctx.tool.hook("execute.after")  = PostToolUse → se puede modificar el resultado que ve el modelo
//
// Formato OpenCode 2: export default { id, setup(ctx) }  (en OpenCode 1 era una función que devolvía los hooks)
import { appendFileSync } from "node:fs"
import { join } from "node:path"
import { execFile } from "node:child_process"

const PELIGROSOS = [
  [/\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r/i, "borrado recursivo forzado (rm -rf)"],
  [/Remove-Item\b.*-Recurse/i, "borrado recursivo en PowerShell"],
  [/git\s+push\b.*(--force|-f\b)/i, "git push --force (reescribe la historia del equipo)"],
  [/git\s+reset\s+--hard/i, "git reset --hard (pierde cambios sin confirmar)"],
  [/DROP\s+(TABLE|DATABASE)/i, "eliminar tablas o bases de datos"],
  [/\bdel\s+\/[sq]/i, "borrado masivo en Windows"],
]

// ¿La herramienta modifica archivos? (edit, write, patch, multiedit...)
const editaArchivos = (tool) => /edit|write|patch/i.test(String(tool))

// Rutas que toca una herramienta: campo directo o, si es un parche, las líneas "*** Update File: ruta"
const rutasDe = (input = {}) => {
  const rutas = [input.filePath, input.path, input.file_path].filter(Boolean).map(String)
  for (const valor of Object.values(input)) {
    if (typeof valor === "string") {
      for (const m of valor.matchAll(/^\*\*\* (?:Add|Update|Delete) File: (.+)$/gm)) rutas.push(m[1].trim())
    }
  }
  return rutas.map((r) => r.replace(/\\/g, "/"))
}

// Ejecuta las pruebas y devuelve { ok, reporte }
const ejecutarPruebas = (proyecto) =>
  new Promise((resolve) => {
    execFile("python", ["-m", "unittest", "discover", "-s", "tests"], { cwd: proyecto, timeout: 50_000 }, (error, _stdout, stderr) =>
      resolve({ ok: !error, reporte: String(stderr).trim() }), // unittest escribe su reporte en stderr
    )
  })

export default {
  id: "upb.guardian",
  async setup(ctx) {
    const directorio = ctx.location.directory

    const auditar = (accion, detalle) => {
      const fecha = new Date().toLocaleString("sv-SE") // formato local AAAA-MM-DD HH:MM:SS
      const texto = String(detalle ?? "").replace(/\n/g, " ").slice(0, 120)
      appendFileSync(join(directorio, ".opencode", "auditoria.log"), `${fecha} | ${accion.padEnd(18)} | ${texto}\n`)
    }

    auditar("PLUGIN cargado", "guardian.js está activo") // prueba de que OpenCode cargó el plugin

    // ── HOOK 1 y 2 · ANTES de usar una herramienta ─────────────────────────
    await ctx.tool.hook("execute.before", (event) => {
      const input = event.input ?? {}

      // HOOK 1: archivos protegidos
      if (editaArchivos(event.tool)) {
        for (const ruta of rutasDe(input)) {
          const nombre = ruta.split("/").pop()
          if (ruta.includes("tests/")) {
            throw new Error(
              `⛔ BLOQUEADO por hook: '${nombre}' es una prueba y las pruebas están protegidas. ` +
                "Si una falla, corrige el código, no la prueba.",
            )
          }
          if (nombre.startsWith(".env")) {
            throw new Error(`⛔ BLOQUEADO por hook: '${nombre}' contiene secretos y no se puede modificar.`)
          }
        }
      }

      // HOOK 2: comandos peligrosos (cualquier herramienta que reciba un "command")
      if (typeof input.command === "string") {
        for (const [patron, motivo] of PELIGROSOS) {
          if (patron.test(input.command)) {
            throw new Error(`⛔ BLOQUEADO por hook: ${motivo}. Comando: ${input.command}`)
          }
        }
      }
    })

    // ── HOOK 3 y 4 · DESPUÉS de usar una herramienta ───────────────────────
    await ctx.tool.hook("execute.after", async (event) => {
      const input = event.input ?? {}

      // HOOK 4: auditoría (los subagentes se lanzan con una herramienta que recibe el tipo de agente)
      const subagente = input.subagent_type ?? input.agent
      if (subagente) auditar("SUBAGENTE terminó", subagente)
      else auditar(event.tool ?? "?", rutasDe(input)[0] ?? input.command ?? input.pattern ?? "")

      // HOOK 3: pruebas automáticas después de editar código Python
      if (event.status !== "completed" || !editaArchivos(event.tool)) return
      if (!rutasDe(input).some((r) => r.endsWith(".py"))) return

      const { ok, reporte } = await ejecutarPruebas(join(directorio, "proyecto-demo"))
      const aviso = ok
        ? `✅ Hook de pruebas: ${reporte.split("\n").find((l) => l.startsWith("Ran ")) ?? ""} → OK`
        : `❌ El hook ejecutó las pruebas y FALLARON. Corrige el código (no las pruebas):\n${reporte.slice(-3000)}`
      auditar("PRUEBAS", ok ? "OK" : "FALLARON")

      // Se agrega el aviso al resultado que ve el modelo para que se corrija solo
      // (en OpenCode 2, result.content es una lista de bloques { type: "text", text })
      const r = event.result ?? {}
      event.result = { ...r, content: [...(r.content ?? []), { type: "text", text: aviso }] }
    })
  },
}
