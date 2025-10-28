# backend/api/search.py
from __future__ import annotations
import unicodedata
from typing import Iterable, Tuple

def _norm(s: str) -> str:
    if s is None: return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.strip().lower()

def build_index(df):
    """Agrega una columna 'search_text' para búsqueda rápida."""
    cols = ["titulo","autor","isbn","categoria"]
    def row_text(row):
        parts = []
        for c in cols:
            val = row.get(c, "")
            parts.append(_norm(val))
        return " | ".join(parts)
    df = df.copy()
    df["search_text"] = df.apply(row_text, axis=1)
    return df

def apply_filters(df, q: str="", categoria: str="", estante: str=""):
    dd = df
    if q:
        nq = _norm(q)
        dd = dd[dd["search_text"].str.contains(nq, na=False)]
    if categoria:
        dd = dd[dd["categoria"].fillna("").str.lower() == categoria.strip().lower()]
    if estante:
        dd = dd[dd["estante"].fillna("").str.lower() == estante.strip().lower()]
    return dd

def page(df, limit: int=24, offset: int=0):
    total = int(df.shape[0])
    if limit is None or limit < 0:
        return total, df
    start = max(int(offset or 0), 0)
    end = start + int(limit or 0)
    return total, df.iloc[start:end]

def to_public(row) -> dict:
    """Convierte una fila a un dict serializable para el API."""
    d = dict(row)
    # asegurar claves
    for k in ["id","titulo","autor","isbn","categoria","anio","paginas","descripcion","portada_url","sala","estante","pos_x","pos_y"]:
        d.setdefault(k, None)
    # convertir tipos simples
    if d["id"] is not None: d["id"] = str(d["id"])
    if d.get("pos_x") is not None:
        try: d["pos_x"] = float(d["pos_x"])
        except: d["pos_x"] = None
    if d.get("pos_y") is not None:
        try: d["pos_y"] = float(d["pos_y"])
        except: d["pos_y"] = None
    return d

def categories(df):
    vals = sorted([v for v in df["categoria"].dropna().unique().tolist() if str(v).strip()])
    return vals
