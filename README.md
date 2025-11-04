# Proyecto Biblioteca (catálogo + mapa)

Este proyecto implementa una aplicación web que permite **buscar libros**, **ver su disponibilidad** y **consultar su ubicación en un mapa** interactivo de la biblioteca.

## Estructura de carpets

proyecto_biblioteca/ (carpeta raíz)
├── frontend/
│ ├── assets/
│ │ ├── css/
│ │ │ ├── main.css
│ │ │ └── mapa.css
│ │ ├── js/
│ │ │ ├── main.js
│ │ │ └── mapa.js
│ │ └── img/
│ │ ├── plano_biblioteca.svg
│ │ └── portada_libro_1.jpg
│ ├── index.html
│ └── detalle_libro.html
├── backend/
│ ├── api/
│ │ ├── **init**.py
│ │ └── search.py
│ ├── data/
│ │ ├── libros.json
│ │ └── libros.xlsx
│ ├── app.py
│ └── requirements.txt
└── README.md
