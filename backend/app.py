from __future__ import annotations
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import pandas as pd
from pathlib import Path
import json
import datetime as dt

from api.search import build_index, apply_filters, page, to_public, categories
from api.locator import load_rangos, locate_signatura, grid_to_world
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
DATA_DIR = BASE_DIR / "backend" / "data"
XLSX_FILE = DATA_DIR / "libros.xlsx"
JSON_FILE = DATA_DIR / "libros.json"
RANGOS_FILE = DATA_DIR / "Biblioteca_MHC_rangos.xlsx"
MAPA_FILE = DATA_DIR / "Biblioteca_MHC_mapa.csv"
RANGOS_SHEET = "Rangos"
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

_df_cache = None
_df_rangos = None
_df_mapa = None
def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
def load_dataframe():
    """
    Carga el catálogo desde XLSX si existe; si no, desde JSON.
    Si no hay datos, crea un DF vacío con el esquema esperado.
    """
    global _df_cache
    _ensure_data_dir()
    if XLSX_FILE.exists():
        df = pd.read_excel(XLSX_FILE)
    elif JSON_FILE.exists():
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            df = pd.DataFrame(json.load(f))
    else:
        df = pd.DataFrame(columns=[
            "id","titulo","autor","isbn","categoria","anio","paginas","descripcion",
            "portada_url","sala","estante","pos_x","pos_y"
        ])
    if "id" not in df.columns or df["id"].isna().any():
        df = df.reset_index(drop=True)
        df["id"] = df.index.astype(str)
    df_indexed = build_index(df)
    _df_cache = df_indexed

    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
    except Exception as e:
        app.logger.warning(f"No se pudo escribir libros.json: {e}")
    return _df_cache
def _ensure_rangos_df():
    """Carga en memoria el DataFrame de rangos Dewey + Cutter."""
    global _df_rangos
    if _df_rangos is None:
        _df_rangos = load_rangos(str(RANGOS_FILE), RANGOS_SHEET)
def _ensure_mapa_df():
    """Carga el CSV de mapa de estanterías."""
    global _df_mapa
    if _df_mapa is None and MAPA_FILE.exists():
        _df_mapa = pd.read_csv(MAPA_FILE, encoding="utf-8-sig")
    return _df_mapa
def get_df():
    global _df_cache
    if _df_cache is None:
        return load_dataframe()
    return _df_cache
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": dt.datetime.utcnow().isoformat() + "Z"})
@app.route("/api/categories")
def api_categories():
    df = get_df()
    return jsonify(categories(df))
@app.route("/api/books")
def api_books():
    df = get_df()
    q = request.args.get("q", "")
    categoria = request.args.get("categoria", "")
    estante = request.args.get("estante", "")
    limit = int(request.args.get("limit", "24") or 24)
    offset = int(request.args.get("offset", "0") or 0)
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
    meta = {
        "viewBox": [600, 400],
        "sections": [
            {"id": "A", "name": "Sección A (Novela)", "x": 30, "y": 40, "w": 160, "h": 120},
            {"id": "B", "name": "Sección B (Clásicos/Misterio)", "x": 220, "y": 40, "w": 160, "h": 120},
            {"id": "C", "name": "Sección C (Ciencia/Tecnología)", "x": 30, "y": 200, "w": 160, "h": 120},
            {"id": "D", "name": "Sección D (Historia/Divulgación)", "x": 220, "y": 200, "w": 160, "h": 120},
        ]
    }
    return jsonify(meta)
@app.route("/api/mapa")
def api_mapa():
    """Devuelve los datos del archivo Biblioteca_MHC_mapa.csv como JSON."""
    df = _ensure_mapa_df()
    if df is None:
        return jsonify({"error": "Archivo de mapa no encontrado."}), 404
    return jsonify(df.to_dict(orient="records"))
@app.route("/api/locate")
def api_locate():
    """
    Localiza una signatura completa, p.ej.: /api/locate?sig=001.2 M67s
    Usa RANGOS_FILE con columnas Dewey+Cutter (locator.py).
    """
    sig = request.args.get("sig", "").strip()
    if not sig:
        return jsonify({"error": "Parámetro 'sig' requerido (ej.: 001.2 M67s)"}), 400
    _ensure_rangos_df()
    try:
        loc = locate_signatura(sig, _df_rangos)
        world = grid_to_world(loc["grid"], spacing=(1.2, 0.35, 2.0), origin=(0.0, 0.0, 0.0))
        return jsonify({**loc, "world": world})
    except LookupError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Error interno: {e}"}), 500
@app.route("/api/reload", methods=["POST"])
def api_reload():
    load_dataframe()
    return jsonify({"reloaded": True})
@app.route("/api/locate/reload", methods=["POST"])
def api_locate_reload():
    """Recarga el Excel de rangos."""
    global _df_rangos
    _df_rangos = load_rangos(str(RANGOS_FILE), RANGOS_SHEET)
    return jsonify({"reloaded": True, "rows": int(_df_rangos.shape[0])})
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")
@app.route("/detalle_libro.html")
def detalle():
    return send_from_directory(FRONTEND_DIR, "detalle_libro.html")
@app.route("/assets/<path:path>")
def assets(path):
    return send_from_directory(ASSETS_DIR, path)
# === MAIN ===
if __name__ == "__main__":
    load_dataframe()
    _ensure_rangos_df()
    _ensure_mapa_df()
    app.run(host="127.0.0.1", port=5000, debug=True)