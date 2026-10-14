const $ = (id) => document.getElementById(id);
let modo = "login";

function cambiarModo(nuevo) {
  modo = nuevo;
  const esLogin = modo === "login";
  $("tab-login").classList.toggle("activa", esLogin);
  $("tab-registro").classList.toggle("activa", !esLogin);
  $("titulo").textContent = esLogin ? "Iniciar sesión" : "Crear cuenta";
  $("enviar").textContent = esLogin ? "Entrar" : "Registrarme";
  $("password").autocomplete = esLogin ? "current-password" : "new-password";
  mostrarMensaje("");
}

function mostrarMensaje(texto, tipo = "error") {
  $("mensaje").textContent = texto;
  $("mensaje").className = tipo;
}

async function api(ruta, opciones = {}) {
  const token = localStorage.getItem("token");
  const respuesta = await fetch(ruta, {
    ...opciones,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  return { ok: respuesta.ok, datos: await respuesta.json() };
}

async function mostrarPerfil() {
  const { ok, datos } = await api("/api/perfil");
  if (!ok) {
    localStorage.removeItem("token");
    return;
  }
  $("nombre").textContent = datos.usuario;
  $("vista-auth").hidden = true;
  $("vista-perfil").hidden = false;
}

$("tab-login").addEventListener("click", () => cambiarModo("login"));
$("tab-registro").addEventListener("click", () => cambiarModo("registro"));

$("formulario").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const cuerpo = JSON.stringify({ usuario: $("usuario").value, password: $("password").value });
  const { ok, datos } = await api(modo === "login" ? "/api/login" : "/api/registro", {
    method: "POST",
    body: cuerpo,
  });
  if (!ok) return mostrarMensaje(datos.error);

  if (modo === "registro") {
    cambiarModo("login");
    $("password").value = "";
    return mostrarMensaje(datos.mensaje, "exito");
  }
  localStorage.setItem("token", datos.token);
  $("formulario").reset();
  mostrarPerfil();
});

$("salir").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  localStorage.removeItem("token");
  $("vista-perfil").hidden = true;
  $("vista-auth").hidden = false;
  cambiarModo("login");
});

if (localStorage.getItem("token")) mostrarPerfil();
