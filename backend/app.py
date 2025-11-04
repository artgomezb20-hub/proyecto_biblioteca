from __future__ import annotations
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import pandas as pd
from pathlib import Path
import json
import datetime as dt

from api.search import build_index, apply_filters, page, to_public, categories
from api.locator import load_rangos, locate_signatura, grid_to_world

# === RUTAS BASE ===
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
ASSETS_DIR = FRONTEND_DIR / "assets"
DATA_DIR = BASE_DIR / "backend" / "data"

# === ARCHIVOS DE DATOS ===
XLSX_FILE = DATA_DIR / "libros.xlsx"
JSON_FILE = DATA_DIR / "libros.json"
RANGOS_FILE = DATA_DIR / "Rangos_por_fila_generados.xlsx"   # ✅ actualizado
MAPA_FILE = DATA_DIR / "mapa_biblioteca.csv"  # opcional si lo agregas más adelante

# === APP FLASK ===
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

_df_cache = None
_df_rangos = None
_df_mapa = None


# === UTILIDADES ===
def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# === CARGA DE DATOS (EJEMPLO DE LUGAR DONDE CAMBIAS LA LÍNEA) ===
def load_all_data():
    global _df_cache, _df_rangos, _df_mapa

    # Carga de rangos (línea corregida)
    _df_rangos = load_rangos(str(RANGOS_FILE))

    # Carga de otros datos (si aplica)
    if XLSX_FILE.exists():
        _df_cache = pd.read_excel(XLSX_FILE)
    elif JSON_FILE.exists():
        _df_cache = pd.read_json(JSON_FILE)

    if MAPA_FILE.exists():
        _df_mapa = pd.read_csv(MAPA_FILE)
