"""Servidor HTTP del login (solo biblioteca estándar).

Ejecutar:  python backend/servidor.py   →  http://localhost:8000
"""
import json
import os
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import auth

RAIZ = Path(__file__).resolve().parents[1]
FRONTEND = RAIZ / "frontend"
conexion = auth.conectar(os.environ.get("LOGIN_DB", str(RAIZ / "usuarios.db")))
candado = threading.Lock()


class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def _responder(self, estado, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _token(self):
        return self.headers.get("Authorization", "").removeprefix("Bearer ").strip()

    def _leer_json(self):
        largo = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(largo) or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        if self.path == "/api/perfil":
            with candado:
                usuario = auth.usuario_de_token(conexion, self._token())
            if usuario is None:
                return self._responder(401, {"error": "Sesión no válida."})
            return self._responder(200, {"usuario": usuario})
        return super().do_GET()

    def do_POST(self):
        datos = self._leer_json()
        try:
            with candado:
                if self.path == "/api/registro":
                    auth.registrar(conexion, datos.get("usuario"), datos.get("password"))
                    return self._responder(201, {"mensaje": "Cuenta creada. Ya puedes iniciar sesión."})
                if self.path == "/api/login":
                    token = auth.iniciar_sesion(conexion, datos.get("usuario"), datos.get("password"))
                    return self._responder(200, {"token": token})
                if self.path == "/api/logout":
                    auth.cerrar_sesion(conexion, self._token())
                    return self._responder(200, {"mensaje": "Sesión cerrada."})
        except auth.ErrorAuth as error:
            return self._responder(400, {"error": str(error)})
        self._responder(404, {"error": "Ruta no encontrada."})


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8000))
    print(f"Login disponible en http://localhost:{puerto}")
    ThreadingHTTPServer(("127.0.0.1", puerto), Manejador).serve_forever()
