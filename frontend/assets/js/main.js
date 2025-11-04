/* main.js: lógica principal de búsqueda y renderizado */
(function(){
  const $ = (sel, ctx=document) => ctx.querySelector(sel);
  const $$ = (sel, ctx=document) => Array.from(ctx.querySelectorAll(sel));
  const BASE_API = window.location.origin + "/api";

  const searchInput = $("#searchInput");
  const categoryFilter = $("#categoryFilter");
  const resultsEl = $("#results");
  const resultCountEl = $("#resultCount");
  const form = $("#searchForm");

  function setYear(){ const yEl = document.getElementById("year"); if (yEl) yEl.textContent = new Date().getFullYear(); }
  setYear();

  function debounce(fn, wait=300){
    let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn.apply(null, args), wait); };
  }

  async function cargarCategorias(){
    try {
      const res = await fetch(`${BASE_API}/categories`);
      if (!res.ok) return;
      const cats = await res.json();
      const frag = document.createDocumentFragment();
      for(const c of cats){
        const opt = document.createElement("option");
        opt.value = c; opt.textContent = c;
        frag.appendChild(opt);
      }
      categoryFilter.appendChild(frag);
    } catch {}
  }

  function cardTemplate(book){
    const cover = book.portada_url || "assets/img/portada_libro_1.jpg";
    const html = `
      <article class="card">
        <header><h3>${book.titulo || "—"}</h3></header>
        <img class="cover" src="${cover}" alt="Portada de ${book.titulo || "libro"}" onerror="this.style.display='none'"/>
        <div class="body">
          <div class="meta">
            <span class="badge" title="Autor">👤 ${book.autor || "Autor desconocido"}</span>
            <span class="badge" title="Categoría">🏷️ ${book.categoria || "Sin categoría"}</span>
            ${book.isbn ? `<span class="badge" title="ISBN">🔢 ${book.isbn}</span>` : ""}
          </div>
          <a class="more" href="detalle_libro.html?id=${encodeURIComponent(book.id)}" aria-label="Abrir detalle de ${book.titulo}">Ver detalle →</a>
        </div>
      </article>
    `;
    return html.trim();
  }

  function renderResults(payload){
    const { total=0, results=[] } = payload || {};
    resultCountEl.textContent = `${total} resultado${total===1?"":"s"}`;
    resultsEl.innerHTML = results.map(cardTemplate).join("");
    if (window.Mapa && typeof window.Mapa.updateMarkers === "function"){
      window.Mapa.updateMarkers(results);
    }
  }

  async function buscar({ q="", categoria="" } = {}){
    resultsEl.setAttribute("aria-busy", "true");
    try {
      const url = new URL(`${BASE_API}/books`, window.location.origin);
      if (q) url.searchParams.set("q", q);
      if (categoria) url.searchParams.set("categoria", categoria);
      url.searchParams.set("limit", "24");
      const res = await fetch(url.toString());
      const data = await res.json();
      renderResults(data);
    } catch (e){
      resultsEl.innerHTML = "<p>No se pudo cargar el contenido.</p>";
    } finally {
      resultsEl.setAttribute("aria-busy", "false");
    }
  }

  const handleSubmit = (ev) => {
    ev.preventDefault();
    buscar({ q: searchInput.value.trim(), categoria: categoryFilter.value });
  };

  form.addEventListener("submit", handleSubmit);
  searchInput.addEventListener("input", debounce(() => handleSubmit(new Event("submit")), 350));
  categoryFilter.addEventListener("change", handleSubmit);

  cargarCategorias();
  buscar({}); // inicial
})();