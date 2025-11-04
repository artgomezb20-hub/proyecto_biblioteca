document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#form-busqueda");
  const input = document.querySelector("#q");
  const cont = document.querySelector("#resultados");
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    cont.innerHTML = "Buscando...";
    try {
      const data = await buscarLibros(input.value.trim());
      cont.innerHTML = data.map(item => `
        <article class="item">
          <h3>${item.titulo}</h3>
          <p>${item.autor}</p>
          <a href="detalle_libro.html?id=${encodeURIComponent(item.id)}">Ver detalle</a>
        </article>
      `).join("");
    } catch (err) {
      cont.textContent = "Error al buscar.";
      console.error(err);
    }
  });
});
