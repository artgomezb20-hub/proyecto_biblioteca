from __future__ import annotations
import re
from typing import Any, Dict, Optional, Tuple
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPA_PATH = os.path.join(BASE_DIR, "data", "Biblioteca_MHC_mapa.xlsx")
COORDS_PATH = os.path.join(BASE_DIR, "data", "Biblioteca_MHC_3D.xlsx")
COORDS_SHEET = "Mapa_3D"

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
    a = to_num(parts[0]); b = to_num(parts[1])
    if a is None or b is None:
        return None, None
    return (float(min(a,b)), float(max(a,b)))

def load_mapa_ranges(path: str = MAPA_PATH) -> pd.DataFrame:
    df_raw = pd.read_excel(path, sheet_name=0)
    ana_cols = [c for c in df_raw.columns if str(c).strip().lower().startswith("anaquel")]
    rows = []
    for _, row in df_raw.iterrows():
        fila = row.get("Estantería")
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

def load_coords(path: str = COORDS_PATH, sheet: str = COORDS_SHEET) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet)
    rename_map = {}
    for c in df.columns:
        lc = c.strip().lower()
        if lc.startswith("rangoini"):
            rename_map[c] = "RangoInicio"
        elif lc.startswith("rangofin"):
            rename_map[c] = "RangoFin"
        elif lc in ("estanteria", "estantería"):
            rename_map[c] = "Estantería"
    if rename_map:
        df = df.rename(columns=rename_map)
    for col in ["Fila", "Estantería", "Anaquel"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ["RangoInicio", "RangoFin"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").map(fix_malformed_dewey)
    return df

def locate_signatura(signatura: str,
                     df_mapa: Optional[pd.DataFrame] = None,
                     df_coords: Optional[pd.DataFrame] = None,
                     eps: float = 1e-6) -> Dict[str, Any]:
    val = parse_signature_to_number(signatura)
    if val is None:
        raise ValueError(f"No se pudo extraer número de '{signatura}'")
    if df_mapa is None:
        df_mapa = load_mapa_ranges(MAPA_PATH)
    if df_coords is None:
        df_coords = load_coords(COORDS_PATH, COORDS_SHEET)
    c_mapa = df_mapa[(df_mapa["RangoInicio"] - eps <= val) & (val <= df_mapa["RangoFin"] + eps)].copy()
    if not c_mapa.empty:
        c_mapa["ancho"] = c_mapa["RangoFin"] - c_mapa["RangoInicio"]
        mapa_best = c_mapa.sort_values("ancho", ascending=True).iloc[0].to_dict()
    else:
        mapa_best = None
    c3d = df_coords[(df_coords["RangoInicio"] - eps <= val) & (val <= df_coords["RangoFin"] + eps)].copy()
    if not c3d.empty:
        c3d["ancho"] = c3d["RangoFin"] - c3d["RangoInicio"]
        coords_best = c3d.sort_values("ancho", ascending=True).iloc[0].to_dict()
    else:
        coords_best = None
    if coords_best is None and mapa_best is None:
        raise LookupError(f"No hay coincidencias para '{signatura}' (valor {val}).")
    chosen = coords_best or mapa_best
    fuente = "3d" if coords_best is not None else "mapa"
    fila = int(chosen.get("Fila")) if pd.notna(chosen.get("Fila")) else (int(mapa_best["Fila"]) if mapa_best else None)
    anaquel = int(chosen.get("Anaquel")) if pd.notna(chosen.get("Anaquel")) else (int(mapa_best["Anaquel"]) if mapa_best else None)
    estanteria = int(chosen.get("Estantería")) if "Estantería" in chosen and pd.notna(chosen.get("Estantería")) else 1
    result = {
        "input": signatura,
        "numeric": float(val),
        "fuente": fuente,
        "fila": fila,
        "estanteria": estanteria,
        "anaquel": anaquel,
        "rango_inicio": float(chosen["RangoInicio"]),
        "rango_fin": float(chosen["RangoFin"]),
        "grid": {"x": estanteria, "y": anaquel, "z": fila},
        "diagnostico": {}
    }
    if mapa_best is not None:
        result["diagnostico"]["mapa"] = {
            "fila": int(mapa_best["Fila"]) if pd.notna(mapa_best["Fila"]) else None,
            "anaquel": int(mapa_best["Anaquel"]) if pd.notna(mapa_best["Anaquel"]) else None,
            "rango_inicio": float(mapa_best["RangoInicio"]),
            "rango_fin": float(mapa_best["RangoFin"]),
        }
    if coords_best is not None:
        result["diagnostico"]["coords"] = {
            "fila": int(coords_best.get("Fila")) if pd.notna(coords_best.get("Fila")) else None,
            "estanteria": int(coords_best.get("Estantería")) if pd.notna(coords_best.get("Estantería")) else None,
            "anaquel": int(coords_best.get("Anaquel")) if pd.notna(coords_best.get("Anaquel")) else None,
            "rango_inicio": float(coords_best["RangoInicio"]),
            "rango_fin": float(coords_best["RangoFin"]),
            "texto": coords_best.get("TextoOriginal"),
            "estante_original": coords_best.get("EstanteOriginal"),
        }
    return result

def grid_to_world(grid_xyz: Dict[str,int],
                  spacing=(1.0, 1.0, 1.0),
                  origin=(0.0, 0.0, 0.0),
                  invert_axes=(False, False, False)) -> Dict[str, float]:
    x, y, z = grid_xyz.get("x"), grid_xyz.get("y"), grid_xyz.get("z")
    sx, sy, sz = spacing
    ox, oy, oz = origin
    if x is None or y is None or z is None:
        return {"X": None, "Y": None, "Z": None}
    X = ox + ((-x if invert_axes[0] else x) - 1) * sx
    Y = oy + ((-y if invert_axes[1] else y) - 1) * sy
    Z = oz + ((-z if invert_axes[2] else z) - 1) * sz
    return {"X": float(X), "Y": float(Y), "Z": float(Z)}

def add_world_coordinates(result: dict,
                          spacing=(1.2, 0.35, 2.0),
                          origin=(0.0, 0.0, 0.0),
                          shelf_width=1.0,
                          use_precise_within_shelf=True) -> dict:
    world_center = grid_to_world(result.get("grid", {}), spacing=spacing, origin=origin)
    result["world_center"] = world_center
    if use_precise_within_shelf and all(k in result for k in ["numeric","rango_inicio","rango_fin"]):
        a = float(result["rango_inicio"]); b = float(result["rango_fin"]); x = float(result["numeric"])
        if b > a:
            u = max(0.0, min(1.0, (x - a) / (b - a)))
        else:
            u = 0.5
        Xp = world_center["X"] + (u - 0.5) * shelf_width
        result["intra_shelf"] = {"u": u, "shelf_width": shelf_width}
        result["world_precise"] = {"X": Xp, "Y": world_center["Y"], "Z": world_center["Z"]}
    else:
        result["intra_shelf"] = None
        result["world_precise"] = world_center
    return result