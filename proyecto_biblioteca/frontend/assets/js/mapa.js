/* mapa.js: renderizado de marcadores y secciones en el plano SVG */
(function(){
  const overlay = document.getElementById("mapaOverlay");
  const img = document.getElementById("mapaImg");
  const container = document.getElementById("mapaContainer");
  const BASE_API = window.location.origin + "/api";

  if (!overlay || !img || !container) return;

  let vbW = parseFloat(container.getAttribute("data-viewbox-width")) || 600;
  let vbH = parseFloat(container.getAttribute("data-viewbox-height")) || 400;
  let secciones = [];

  function scaleX(x){
    const rect = container.getBoundingClientRect();
    return (x / vbW) * rect.width;
  }
  function scaleY(y){
    const rect = container.getBoundingClientRect();
    return (y / vbH) * rect.height;
  }

  function clearOverlay(){ overlay.innerHTML = ""; }

  function drawSecciones(){
    // Dibuja cajas de secciones para referencia visual (no interactivo)
    for(const s of secciones){
      const el = document.createElement("div");
      el.className = "seccion";
      el.style.left = `${(s.x/vbW)*100}%`;
      el.style.top = `${(s.y/vbH)*100}%`;
      el.style.width = `${(s.w/vbW)*100}%`;
      el.style.height = `${(s.h/vbH)*100}%`;
      const label = document.createElement("div");
      label.className = "seccion-label";
      label.textContent = s.name || s.id;
      el.appendChild(label);
      overlay.appendChild(el);
    }
  }

  function drawMarkers(books){
    for(const b of books){
      if (b.pos_x == null || b.pos_y == null) continue;
      const m = document.createElement("button");
      m.className = "marker";
      m.type = "button";
      m.style.left = `${(b.pos_x/vbW)*100}%`;
      m.style.top = `${(b.pos_y/vbH)*100}%`;
      m.setAttribute("aria-label", `${b.titulo} — Estante ${b.estante || "?"}`);
      m.addEventListener("click", () => {
        window.location.href = `detalle_libro.html?id=${encodeURIComponent(b.id)}`;
      });
      const tip = document.createElement("span");
      tip.className = "tooltip";
      tip.textContent = b.titulo || "Libro";
      m.appendChild(tip);
      overlay.appendChild(m);
    }
  }

  function layout(books){
    clearOverlay();
    drawSecciones();
    drawMarkers(books || []);
  }

  async function cargarMapa(){
    try {
      const res = await fetch(`${BASE_API}/map`);
      if (!res.ok) return;
      const meta = await res.json();
      if (meta && meta.viewBox){
        const [w, h] = meta.viewBox;
        vbW = w || vbW; vbH = h || vbH;
      }
      secciones = meta.sections || [];
      layout([]);
    } catch {}
  }

  function onResize(){
    // Recalcula posiciones relativas al tamaño del contenedor
    // Los marcadores usan % así que no hace falta recalcular; mantenemos por si en el futuro cambia
  }
  window.addEventListener("resize", onResize);

  img.addEventListener("load", cargarMapa);

  // API pública para main.js / detalle
  window.Mapa = {
    updateMarkers(books){
      layout(Array.isArray(books) ? books : []);
    }
  };
})();