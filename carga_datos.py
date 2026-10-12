"""
Módulo de Carga y Normalización de Datos para Avance Físico de Obra.

Soporta archivos CSV con separadores automáticos (coma ',', punto y coma ';', tabulación)
y archivos Excel (.xlsx, .xls), con manejo seguro de codificaciones (UTF-8, Latin-1).
"""

import os
import io
import csv
import pandas as pd
from typing import Tuple, Optional, Union

# Mapeo de alias para columnas estándar
MAPEO_ALIAS = {
    "semana": "semana",
    "semanas": "semana",
    "periodo": "semana",
    "periodos": "semana",
    "codigo_partida": "codigo_partida",
    "cod_partida": "codigo_partida",
    "codigo": "codigo_partida",
    "item": "codigo_partida",
    "partida": "partida",
    "descripcion": "partida",
    "tarea": "partida",
    "especialidad": "especialidad",
    "disciplina": "especialidad",
    "encargado": "encargado",
    "responsable": "encargado",
    "peso_partida": "peso_partida",
    "peso": "peso_partida",
    "ponderacion": "peso_partida",
    "peso_%": "peso_partida",
    "avance_plan_semanal": "avance_plan_semanal",
    "avance_planificado_semanal": "avance_plan_semanal",
    "avance_plan_periodo": "avance_plan_semanal",
    "avance_planificado": "avance_plan_semanal",
    "avance_plan": "avance_plan_semanal",
    "avance_planificado_periodo_%": "avance_plan_semanal",
    "avance_planificado_periodo": "avance_plan_semanal",
    "avance_real_semanal": "avance_real_semanal",
    "avance_real_periodo": "avance_real_semanal",
    "avance_real": "avance_real_semanal",
    "avance_real_periodo_%": "avance_real_semanal",
    "fecha": "fecha",
    "fechas": "fecha"
}


def detectar_formato(file_input: Union[str, io.BytesIO, object]) -> str:
    """Detecta si el archivo es CSV o Excel por su nombre."""
    filename = ""
    if isinstance(file_input, str):
        filename = file_input
    elif hasattr(file_input, "name"):
        filename = file_input.name

    filename_lower = filename.lower()
    if filename_lower.endswith((".xlsx", ".xls")):
        return "excel"
    return "csv"


def detectar_delimitador(sample_bytes: bytes) -> str:
    """Detecta inteligentemente si el delimitador es ',', ';' o '\t'."""
    try:
        sample_text = sample_bytes.decode("utf-8", errors="ignore")
    except Exception:
        sample_text = str(sample_bytes)

    lineas = [line for line in sample_text.splitlines() if line.strip()][:5]
    if not lineas:
        return ","

    primer_linea = lineas[0]
    # Contar ocurrencias en la cabecera
    conteos = {
        ";": primer_linea.count(";"),
        ",": primer_linea.count(","),
        "\t": primer_linea.count("\t")
    }
    # Obtener el delimitador con mayor presencia
    delimitador = max(conteos, key=conteos.get)
    if conteos[delimitador] > 0:
        return delimitador

    return ","


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas eliminando espacios, tildes y mapeando alias."""
    column_mapping = {}
    for col in df.columns:
        col_clean = str(col).strip()
        col_key = col_clean.lower().replace(" ", "_").replace("%", "").strip("_")
        
        target = MAPEO_ALIAS.get(col_key, MAPEO_ALIAS.get(col_clean.lower(), col_clean))
        column_mapping[col] = target

    df = df.rename(columns=column_mapping)
    # Deduplicar si se generaron nombres repetidos
    df = df.loc[:, ~df.columns.duplicated()].copy()
    return df


def cargar_datos_desde_fuente(file_input: Union[str, io.BytesIO, object]) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Carga y valida un archivo CSV o Excel de avance de obra.
    
    Retorna:
        Tuple[DataFrame procesado o None, mensaje_de_error o None]
    """
    if file_input is None:
        return None, "No se ha proporcionado ningún archivo."

    formato = detectar_formato(file_input)

    # Si es un buffer subido (UploadedFile), reiniciar puntero
    if hasattr(file_input, "seek"):
        try:
            file_input.seek(0)
        except Exception:
            pass

    try:
        if formato == "excel":
            df = pd.read_excel(file_input)
        else:
            # Es CSV: leer muestra para detectar delimitador y codificación
            if isinstance(file_input, str):
                with open(file_input, "rb") as f:
                    sample = f.read(4096)
                delim = detectar_delimitador(sample)
                try:
                    df = pd.read_csv(file_input, sep=delim, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(file_input, sep=delim, encoding="latin-1")
            else:
                sample = file_input.read(4096)
                file_input.seek(0)
                delim = detectar_delimitador(sample)
                try:
                    df = pd.read_csv(file_input, sep=delim, encoding="utf-8")
                except UnicodeDecodeError:
                    file_input.seek(0)
                    df = pd.read_csv(file_input, sep=delim, encoding="latin-1")

    except Exception as e:
        return None, f"Error al leer el archivo ({formato.upper()}): {str(e)}"

    # Normalizar nombres de columnas
    df = normalizar_columnas(df)

    # Limpiar strings en todas las columnas de texto
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    # Validar columnas mínimas indispensables
    columnas_requeridas = ["semana", "avance_plan_semanal", "avance_real_semanal"]
    faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if faltantes:
        return None, (
            f"El archivo cargado carece de las siguientes columnas mínimas: {', '.join(faltantes)}.\n"
            f"Columnas detectadas: {', '.join(df.columns.tolist())}"
        )

    # Asegurar tipos numéricos para las columnas de avance
    for col in ["avance_plan_semanal", "avance_real_semanal"]:
        if col in df.columns:
            # Reemplazar comas por puntos en strings numéricos si es necesario
            if df[col].dtype == "object":
                df[col] = df[col].str.replace(",", ".", regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Si existe peso_partida, asegurar que sea numérico
    if "peso_partida" in df.columns:
        if df["peso_partida"].dtype == "object":
            df["peso_partida"] = df["peso_partida"].str.replace(",", ".", regex=False)
        df["peso_partida"] = pd.to_numeric(df["peso_partida"], errors="coerce").fillna(0.0)
    else:
        # Si no existe peso_partida, asignamos peso proporcional según partidas
        if "codigo_partida" in df.columns:
            n_partidas = df["codigo_partida"].nunique()
            df["peso_partida"] = 100.0 / max(n_partidas, 1)
        else:
            df["peso_partida"] = 100.0

    # Asegurar que semana sea numérica u ordenable
    if "semana" in df.columns:
        if df["semana"].dtype == "object":
            # Extraer números si dice por ejemplo "Semana 1"
            df["semana_num"] = df["semana"].str.extract(r"(\d+)")[0]
            df["semana"] = pd.to_numeric(df["semana_num"], errors="coerce").fillna(df["semana"])
            if "semana_num" in df.columns:
                df = df.drop(columns=["semana_num"])
        try:
            df["semana"] = pd.to_numeric(df["semana"], errors="ignore")
        except Exception:
            pass

    # Si no existen partida, especialidad o encargado, proveer valores por defecto limpios
    if "codigo_partida" not in df.columns:
        df["codigo_partida"] = "P001"
    if "partida" not in df.columns:
        df["partida"] = df["codigo_partida"]
    if "especialidad" not in df.columns:
        df["especialidad"] = "General"
    if "encargado" not in df.columns:
        df["encargado"] = "Responsable de Obra"

    return df, None
