<table id="tabla" border="1"></table>
<script>
  fetch("http://localhost:5000/api/mapa")
    .then(r => r.json())
    .then(datos => {
      const columnas = Object.keys(datos[0] || {});
      const tabla = document.getElementById('tabla');

      const thead = document.createElement('thead');
      const trHead = document.createElement('tr');
      columnas.forEach(c => {
        const th = document.createElement('th');
        th.textContent = c;
        trHead.appendChild(th);
      });
      thead.appendChild(trHead);

      const tbody = document.createElement('tbody');
      datos.forEach(fila => {
        const tr = document.createElement('tr');
        columnas.forEach(c => {
          const td = document.createElement('td');
          td.textContent = fila[c] ?? '';
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });

      tabla.appendChild(thead);
      tabla.appendChild(tbody);
    });
</script>
