document.addEventListener("DOMContentLoaded", async () => {
  const params = new URLSearchParams(location.search);
  const id = params.get("id");
  const cont = document.querySelector("#detalle");

  if (!id) {
    cont.textContent = "Falta id de libro.";
    return;
  }
  cont.textContent = "Cargando...";
  try {
    const libro = await obtenerLibro(id);
    cont.innerHTML = `
      <h1>${libro.titulo}</h1>
      <p><strong>Autor:</strong> ${libro.autor}</p>
      <p><strong>Año:</strong> ${libro.anio}</p>
      <p>${libro.descripcion || ""}</p>
    `;
  } catch (err) {
    cont.textContent = "No se pudo cargar el libro.";
    console.error(err);
  }
});
