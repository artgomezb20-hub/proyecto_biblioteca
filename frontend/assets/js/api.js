const API_URL = "https://proyecto_biblioteca_backend.onrender.com";
async function buscarLibros(q) {
  const r = await fetch(`${API_URL}/api/search?q=${encodeURIComponent(q)}`);
  if (!r.ok) throw new Error("Error al buscar");
  return r.json();
}
async function obtenerLibro(id) {
  const r = await fetch(`${API_URL}/api/libro/${encodeURIComponent(id)}`);
  if (!r.ok) throw new Error("Error al cargar libro");
  return r.json();
}
