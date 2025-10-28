# backend/app.py
from __future__ import annotations
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import pandas as pd
from pathlib import Path
import json
import datetime as dt

from api.search import build_index, apply_filters, page, to_public, categories

BASE_DIR = Path(__file__).resolve().parent.parent  # proyecto_biblioteca/
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
DATA_DIR = BASE_DIR / "backend" / "data"
XLSX_FILE = DATA_DIR / "libros.xlsx"
JSON_FILE = DATA_DIR / "libros.json"

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

_df_cache = None  # dataframe indexado

def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_dataframe():
    """Carga el DataFrame desde XLSX si existe; si no, desde JSON."""
    global _df_cache
    _ensure_data_dir()
    if XLSX_FILE.exists():
        df = pd.read_excel(XLSX_FILE)
    elif JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            df = pd.DataFrame(json.load(f))
    else:
        # Dataset vacío
        df = pd.DataFrame(columns=[
            "id","titulo","autor","isbn","categoria","anio","paginas","descripcion",
            "portada_url","sala","estante","pos_x","pos_y"
        ])
    # Asegurar ID
    if "id" not in df.columns or df["id"].isna().any():
        df = df.reset_index(drop=True)
        df["id"] = df.index.astype(str)
    df_indexed = build_index(df)
    _df_cache = df_indexed
    # Guardar JSON derivado
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.warning(f"No se pudo escribir libros.json: {e}")
    return _df_cache

def get_df():
    global _df_cache
    if _df_cache is None:
        return load_dataframe()
    return _df_cache

@app.route("/api/health")
def health():
    return jsonify({"status":"ok","time":dt.datetime.utcnow().isoformat()+"Z"})

@app.route("/api/categories")
def api_categories():
    df = get_df()
    return jsonify(categories(df))

@app.route("/api/books")
def api_books():
    df = get_df()
    q = request.args.get("q","")
    categoria = request.args.get("categoria","")
    estante = request.args.get("estante","")
    limit = int(request.args.get("limit","24") or 24)
    offset = int(request.args.get("offset","0") or 0)
    dd = apply_filters(df, q=q, categoria=categoria, estante=estante)
    total, window = page(dd, limit=limit, offset=offset)
    return jsonify({
        "total": int(total),
        "limit": int(limit),
        "offset": int(offset),
        "results": [to_public(r) for _, r in window.iterrows()]
    })

@app.route("/api/books/<id_>")
def api_book_detail(id_):
    df = get_df()
    row = df[df["id"].astype(str) == str(id_)]
    if row.empty:
        abort(404)
    data = to_public(row.iloc[0].to_dict())
    return jsonify(data)

@app.route("/api/map")
def api_map():
    # Metadatos del mapa (coinciden con el SVG de 600x400)
    meta = {
        "viewBox": [600, 400],
        "sections": [
            {"id":"A","name":"Sección A (Novela)","x":30,"y":40,"w":160,"h":120},
            {"id":"B","name":"Sección B (Clásicos/Misterio)","x":220,"y":40,"w":160,"h":120},
            {"id":"C","name":"Sección C (Ciencia/Tecnología)","x":30,"y":200,"w":160,"h":120},
            {"id":"D","name":"Sección D (Historia/Divulgación)","x":220,"y":200,"w":160,"h":120},
        ]
    }
    return jsonify(meta)

@app.route("/api/reload", methods=["POST"])
def api_reload():
    load_dataframe()
    return jsonify({"reloaded": True})

# --- Servir frontend estático ---
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/detalle_libro.html")
def detalle():
    return send_from_directory(FRONTEND_DIR, "detalle_libro.html")

@app.route("/assets/<path:path>")
def assets(path):
    return send_from_directory(ASSETS_DIR, path)

if __name__ == "__main__":
    # Cargar datos al iniciar
    load_dataframe()
    app.run(host="127.0.0.1", port=5000, debug=True)
