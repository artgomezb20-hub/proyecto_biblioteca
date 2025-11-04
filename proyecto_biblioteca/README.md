# Proyecto Biblioteca (catálogo + mapa)

Este proyecto implementa una aplicación web sencilla para **buscar libros** y **ver su ubicación en un mapa** de la biblioteca.

## Estructura de carpetas

```
proyecto_biblioteca/ (carpeta raíz)
├── frontend/
│   ├── assets/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── mapa.css
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   └── mapa.js
│   │   └── img/
│   │       ├── plano_biblioteca.svg
│   │       └── portada_libro_1.jpg
│   ├── index.html
│   └── detalle_libro.html
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── search.py
│   ├── data/
│   │   ├── libros.json
│   │   └── libros.xlsx
│   ├── app.py
│   └── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10+
- (Opcional para desarrollo de datos) `pandas` y `openpyxl` — ya listados en `requirements.txt`

## Puesta en marcha (desarrollo)

1. **Crear y activar** un entorno virtual (recomendado):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Ejecutar el servidor**:
   ```bash
   python backend/app.py
   ```

4. Abre en el navegador: <http://127.0.0.1:5000>

> El servidor Flask sirve también los archivos del frontend, por lo que **no necesitas** levantar otro servicio para los HTML/CSS/JS.

## API

- `GET /api/health` → estado del servidor.
- `GET /api/categories` → lista de categorías únicas.
- `GET /api/books?q=&categoria=&estante=&limit=&offset=` → resultados paginados.
- `GET /api/books/<id>` → ficha de un libro.
- `GET /api/map` → metadatos del plano (tamaño y secciones).
- `POST /api/reload` → recarga los datos desde \`data/libros.xlsx\` (útil si reemplazas el Excel).

### Esquema de `libros.xlsx` / `libros.json`

Columnas esperadas:

| campo        | tipo     | descripción                                       |
|--------------|----------|---------------------------------------------------|
| id           | str/int  | Identificador único del libro                     |
| titulo       | str      | Título                                            |
| autor        | str      | Autor/es                                          |
| isbn         | str      | ISBN                                              |
| categoria    | str      | Categoría (p.ej. Novela, Ciencia, etc.)           |
| anio         | int      | Año de publicación                                |
| paginas      | int      | Número de páginas                                 |
| descripcion  | str      | Resumen                                           |
| portada_url  | str      | URL o ruta relativa a la portada                  |
| sala         | str      | Sala o zona                                       |
| estante      | str      | Estante (A1, B2, etc.)                            |
| pos_x        | float    | Coordenada X en el plano (sistema 600x400)        |
| pos_y        | float    | Coordenada Y en el plano (sistema 600x400)        |

> El plano SVG usa un **sistema de coordenadas 600 × 400**. Las posiciones de los libros (`pos_x`, `pos_y`) se expresan en ese sistema. El frontend escala automáticamente los marcadores al tamaño visible del mapa.

## Personalización del plano

- El archivo `frontend/assets/img/plano_biblioteca.svg` contiene **4 secciones** de ejemplo (A, B, C, D).
- El API `GET /api/map` define las **cajas** de esas secciones para dibujar contornos visuales. Ajusta ambas cosas si rediseñas el mapa.

## Actualizar datos desde Excel

1. Reemplaza `backend/data/libros.xlsx` con tu archivo real (mismos nombres de columna).
2. Llama al endpoint:
   ```bash
   curl -X POST http://127.0.0.1:5000/api/reload
   ```
   Esto regenerará `backend/data/libros.json` y actualizará la búsqueda.

## Notas

- Si `pandas/openpyxl` no están disponibles en tu entorno al ejecutar este ZIP, el backend podrá arrancar con `libros.json`. Instala dependencias para usar `libros.xlsx`.
- La búsqueda ignora acentos y no distingue mayúsculas/minúsculas.
- El frontend es responsivo y accesible (roles ARIA básicos, mensajes `aria-live`, enfoque claro).

¡Listo! 🎉
