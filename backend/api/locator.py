from __future__ import annotations
import re
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import os

# === RUTAS BASE ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPA_PATH = os.path.join(BASE_DIR, "data", "Sheet1 (1).csv")

# === FUNCIONES DE PARSEO ===
def parse_signature_to_number(sig: str) -> Optional[float]:
    if sig is None:
        return None
    s = str(sig).replace(",", ".")
    m = re.search(r"\b(\d{1,3}\.\d{1,6})\b", s)
    if m:
        return float(m.group(1))
    m = re.search(r"\b(\d{3})\b", s)
    if m:
        return float(m.group(1))
    m = re.search(r"\b(\d+(?:\.\d+)?)\b", s)
    if m:
        return float(m.group(1))
    return None


def fix_malformed_dewey(x: float) -> float:
    if x is None:
        return x
    try:
        xi = int(x)
        if abs(x - xi) < 1e-9 and 1000 <= xi <= 9999999:
            s = str(xi)
            return float(s[:3] + "." + s[3:])
    except Exception:
        pass
    return float(x)


def parse_range_text(cell: Any) -> Tuple[Optional[float], Optional[float]]:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)) or (isinstance(cell, str) and cell.strip() == ""):
        return None, None
    s = str(cell).strip().replace(",", ".").replace("–", "-").replace("—", "-")
    parts = [p for p in s.split("-") if p.strip()]
    if len(parts) != 2:
        parts = [p for p in re.split(r"\s+a\s+", s) if p.strip()]
    if len(parts) != 2:
        return None, None

    def to_num(p):
        try:
            return float(p)
        except ValueError:
            return parse_signature_to_number(p)

    a = to_num(parts[0])
    b = to_num(parts[1])
    if a is None or b is None:
        return None, None
    return (float(min(a, b)), float(max(a, b)))


# === CARGA DE MAPA DESDE CSV ===
def load_mapa_ranges(path: str = MAPA_PATH) -> pd.DataFrame:
    df_raw = pd.read_csv(path)
    ana_cols = [c for c in df_raw.columns if str(c).strip().lower().startswith("anaquel")]
    rows = []
    for _, row in df_raw.iterrows():
        fila = row.get("Estantería") or row.get("Fila")
        try:
            fila = int(float(fila)) if pd.notna(fila) else None
        except Exception:
            fila = None
        for c in ana_cols:
            m = re.search(r"(\d+)", str(c))
            anaquel = int(m.group(1)) if m else None
            r_ini, r_fin = parse_range_text(row[c])
            if r_ini is None or r_fin is None:
                continue
            rows.append({"Fila": fila, "Anaquel": anaquel, "RangoInicio": r_ini, "RangoFin": r_fin})
    df = pd.DataFrame(rows)
    return df.sort_values(["Fila", "Anaquel", "RangoInicio"]).reset_index(drop=True)


# === LOCALIZADOR PRINCIPAL ===
def locate_signatura(signatura: str,
                     df_mapa: Optional[pd.DataFrame] = None,
                     eps: float = 1e-6) -> Dict[str, Any]:
    val = parse_signature_to_number(signatura)
    if val is None:
        raise ValueError(f"No se pudo extraer número de '{signatura}'")
    if df_mapa is None:
        df_mapa = load_mapa_ranges(MAPA_PATH)

    c_mapa = df_mapa[(df_mapa["RangoInicio"] - eps <= val) & (val <= df_mapa["RangoFin"] + eps)].copy()
    if not c_mapa.empty:
        c_mapa["ancho"] = c_mapa["RangoFin"] - c_mapa["RangoInicio"]
        mapa_best = c_mapa.sort_values("ancho", ascending=True).iloc[0].to_dict()
    else:
        raise LookupError(f"No hay coincidencias para '{signatura}' (valor {val}).")

    result = {
        "input": signatura,
        "numeric": float(val),
        "fila": int(mapa_best["Fila"]),
        "anaquel": int(mapa_best["Anaquel"]),
        "rango_inicio": float(mapa_best["RangoInicio"]),
        "rango_fin": float(mapa_best["RangoFin"]),
        "grid": {"x": 1, "y": mapa_best["Anaquel"], "z": mapa_best["Fila"]}
    }

    return result
def grid_to_world(grid_xyz: Dict[str, int],
                  spacing=(1.0, 1.0, 1.0),
                  origin=(0.0, 0.0, 0.0)) -> Dict[str, float]:
    x, y, z = grid_xyz.get("x"), grid_xyz.get("y"), grid_xyz.get("z")
    sx, sy, sz = spacing
    ox, oy, oz = origin
    if x is None or y is None or z is None:
        return {"X": None, "Y": None, "Z": None}
    X = ox + (x - 1) * sx
    Y = oy + (y - 1) * sy
    Z = oz + (z - 1) * sz
    return {"X": float(X), "Y": float(Y), "Z": float(Z)}


def add_world_coordinates(result: dict,
                          spacing=(1.2, 0.35, 2.0),
                          origin=(0.0, 0.0, 0.0)) -> dict:
    world_center = grid_to_world(result.get("grid", {}), spacing=spacing, origin=origin)
    result["world_center"] = world_center
    return result


# === COMPATIBILIDAD CON app.py ===
def load_rangos(path: str, sheet: str = "Rangos"):
    try:
        return load_mapa_ranges(path)
    except Exception as e:
        raise RuntimeError(f"No se pudo cargar el archivo de rangos: {e}")