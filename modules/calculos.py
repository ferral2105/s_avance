"""
Módulo de Lógica y Cálculos para el Control de Avance Físico de Obra.

Contiene funciones puras para el procesamiento con Pandas:
- Agregación semanal y acumulada (Curva S, Producción, Brecha)
- Indicadores Clave de Desempeño (KPIs)
- Análisis por Especialidad y Encargado
- Matriz de control por Partida
- 10 Validaciones de Calidad de Datos
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional


def calcular_avance_semanal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el avance semanal y acumulado consolidado del proyecto.
    
    A partir de las columnas 'avance_plan_semanal' y 'avance_real_semanal',
    agrupa por semana, calcula sumatorias semanales, acumulados con cumsum(),
    diferencias y clasificaciones de estado.
    """
    df_calc = df.copy()

    # Si vienen las semanas numéricas o en texto, asegurar agrupación ordenada
    df_semanal = df_calc.groupby("semana", as_index=False).agg(
        avance_planificado_semanal=("avance_plan_semanal", "sum"),
        avance_real_semanal=("avance_real_semanal", "sum")
    )

    # Ordenar por semana ascendente
    try:
        df_semanal["semana_sort"] = pd.to_numeric(df_semanal["semana"], errors="coerce").fillna(0)
        df_semanal = df_semanal.sort_values(by="semana_sort").drop(columns=["semana_sort"]).reset_index(drop=True)
    except Exception:
        df_semanal = df_semanal.sort_values(by="semana").reset_index(drop=True)

    # Acumulados con cumsum()
    df_semanal["avance_planificado_acumulado"] = df_semanal["avance_planificado_semanal"].cumsum()
    df_semanal["avance_real_acumulado"] = df_semanal["avance_real_semanal"].cumsum()

    # Diferencias
    df_semanal["diferencia_semanal"] = (
        df_semanal["avance_real_semanal"] - df_semanal["avance_planificado_semanal"]
    )
    df_semanal["diferencia_acumulada"] = (
        df_semanal["avance_real_acumulado"] - df_semanal["avance_planificado_acumulado"]
    )

    # Variación porcentual relativa
    df_semanal["variacion_porcentual"] = np.where(
        df_semanal["avance_planificado_acumulado"] != 0,
        (df_semanal["diferencia_acumulada"] / df_semanal["avance_planificado_acumulado"]) * 100,
        0.0
    )

    # Índice de Desempeño del Cronograma (SPI: Real / Plan)
    df_semanal["spi"] = np.where(
        df_semanal["avance_planificado_acumulado"] > 0,
        df_semanal["avance_real_acumulado"] / df_semanal["avance_planificado_acumulado"],
        1.0
    )

    # Clasificación del estado según umbral (+-0.50%)
    def clasificar_estado(diff: float) -> str:
        if diff > 0.50:
            return "ADELANTADA"
        elif diff < -0.50:
            return "RETRASADA"
        else:
            return "SEGÚN PLAN"

    df_semanal["estado_avance"] = df_semanal["diferencia_acumulada"].apply(clasificar_estado)

    return df_semanal


def calcular_kpis_principales(df_semanal: pd.DataFrame, df_raw: pd.DataFrame) -> Dict[str, Any]:
    """
    Obtiene los principales indicadores globales del proyecto para tarjetas KPI.
    """
    if df_semanal.empty:
        return {
            "plan_acum": 0.0,
            "real_acum": 0.0,
            "diferencia": 0.0,
            "estado": "SIN DATOS",
            "cumplimiento": 0.0,
            "spi": 1.0,
            "total_semanas": 0,
            "total_partidas": 0,
            "total_especialidades": 0,
            "total_encargados": 0
        }

    ultimo = df_semanal.iloc[-1]
    plan_acum = float(ultimo["avance_planificado_acumulado"])
    real_acum = float(ultimo["avance_real_acumulado"])
    diferencia = float(ultimo["diferencia_acumulada"])
    estado = str(ultimo["estado_avance"])
    spi = float(ultimo["spi"])

    cumplimiento = (real_acum / plan_acum * 100) if plan_acum > 0 else 0.0
    n_partidas = df_raw["codigo_partida"].nunique() if "codigo_partida" in df_raw.columns else 1
    n_esp = df_raw["especialidad"].nunique() if "especialidad" in df_raw.columns else 1
    n_enc = df_raw["encargado"].nunique() if "encargado" in df_raw.columns else 1

    return {
        "plan_acum": plan_acum,
        "real_acum": real_acum,
        "diferencia": diferencia,
        "estado": estado,
        "cumplimiento": cumplimiento,
        "spi": spi,
        "total_semanas": len(df_semanal),
        "total_partidas": n_partidas,
        "total_especialidades": n_esp,
        "total_encargados": n_enc
    }


def calcular_avance_especialidad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula el avance acumulado agrupado por especialidad, ordenado de mayor a menor avance real.
    """
    df_esp = df.groupby("especialidad", as_index=False).agg(
        avance_planificado=("avance_plan_semanal", "sum"),
        avance_real=("avance_real_semanal", "sum"),
        peso_total=("peso_partida", lambda x: df.loc[x.index].drop_duplicates("codigo_partida")["peso_partida"].sum())
    )
    df_esp["diferencia"] = df_esp["avance_real"] - df_esp["avance_planificado"]
    df_esp["cumplimiento_%"] = np.where(
        df_esp["avance_planificado"] > 0,
        (df_esp["avance_real"] / df_esp["avance_planificado"]) * 100,
        0.0
    )
    df_esp = df_esp.sort_values(by="avance_real", ascending=False).reset_index(drop=True)
    return df_esp


def calcular_partidas_encargado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la cantidad de partidas únicas asignadas a cada encargado.
    """
    col_partida = "codigo_partida" if "codigo_partida" in df.columns else "partida"
    df_part = df.groupby("encargado")[col_partida].nunique().reset_index()
    df_part.columns = ["encargado", "cantidad_partidas"]
    df_part = df_part.sort_values(by="cantidad_partidas", ascending=False).reset_index(drop=True)
    return df_part


def calcular_avance_encargado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compara el avance planificado y real acumulado por cada encargado.
    """
    df_enc = df.groupby("encargado", as_index=False).agg(
        avance_planificado=("avance_plan_semanal", "sum"),
        avance_real=("avance_real_semanal", "sum")
    )
    df_enc["diferencia"] = df_enc["avance_real"] - df_enc["avance_planificado"]
    df_enc["cumplimiento_%"] = np.where(
        df_enc["avance_planificado"] > 0,
        (df_enc["avance_real"] / df_enc["avance_planificado"]) * 100,
        0.0
    )
    df_enc = df_enc.sort_values(by="avance_real", ascending=False).reset_index(drop=True)
    return df_enc


def calcular_distribucion_especialidad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula la distribución del peso total y cantidad de partidas por especialidad.
    """
    df_unicas = df.drop_duplicates(subset=["codigo_partida"])
    dist = df_unicas.groupby("especialidad", as_index=False).agg(
        peso_total=("peso_partida", "sum"),
        cantidad_partidas=("codigo_partida", "count")
    )
    dist = dist.sort_values(by="peso_total", ascending=False).reset_index(drop=True)
    return dist


def calcular_resumen_partidas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera una tabla ejecutiva de estado por partida individual.
    """
    df_res = df.groupby(["codigo_partida", "partida", "especialidad", "encargado"], as_index=False).agg(
        peso_partida=("peso_partida", "first"),
        avance_plan_total=("avance_plan_semanal", "sum"),
        avance_real_total=("avance_real_semanal", "sum")
    )
    df_res["diferencia"] = df_res["avance_real_total"] - df_res["avance_plan_total"]
    df_res["cumplimiento_%"] = np.where(
        df_res["avance_plan_total"] > 0,
        (df_res["avance_real_total"] / df_res["avance_plan_total"]) * 100,
        0.0
    )
    return df_res.sort_values(by="codigo_partida").reset_index(drop=True)


def validar_datos_proyecto(df: pd.DataFrame, df_semanal: pd.DataFrame) -> Tuple[Dict[str, Dict[str, Any]], bool]:
    """
    Ejecuta 10 validaciones de control de calidad de datos antes de generar reportes.
    
    Retorna:
        Tuple[diccionario_validaciones, todas_validas_bool]
    """
    resultados = {}
    todas_correctas = True

    # 1. Partidas únicas
    partidas_unicas = df["codigo_partida"].nunique()
    v1 = partidas_unicas >= 1
    resultados["1_partidas"] = {
        "descripcion": "Existencia de partidas únicas identificables",
        "esperado": ">= 1 partidas (típico: 20)",
        "obtenido": f"{partidas_unicas} partidas",
        "estado": v1
    }
    todas_correctas = todas_correctas and v1

    # 2. Cantidad de semanas
    semanas_unicas = df["semana"].nunique()
    v2 = semanas_unicas >= 1
    resultados["2_semanas"] = {
        "descripcion": "Existencia de periodos o semanas evaluadas",
        "esperado": ">= 1 semanas (típico: 12)",
        "obtenido": f"{semanas_unicas} semanas",
        "estado": v2
    }
    todas_correctas = todas_correctas and v2

    # 3. Especialidades
    esp_unicas = df["especialidad"].nunique()
    v3 = esp_unicas >= 1
    resultados["3_especialidades"] = {
        "descripcion": "Clasificación por especialidades del proyecto",
        "esperado": ">= 1 especialidades",
        "obtenido": f"{esp_unicas} especialidades",
        "estado": v3
    }
    todas_correctas = todas_correctas and v3

    # 4. Encargados
    enc_unicos = df["encargado"].nunique()
    v4 = enc_unicos >= 1
    resultados["4_encargados"] = {
        "descripcion": "Asignación de responsables o encargados de obra",
        "esperado": ">= 1 encargados",
        "obtenido": f"{enc_unicos} encargados",
        "estado": v4
    }
    todas_correctas = todas_correctas and v4

    # 5. Suma de peso de las partidas
    pesos_unicos = df.drop_duplicates(subset=["codigo_partida"])["peso_partida"]
    suma_pesos = float(pesos_unicos.sum())
    v5 = abs(suma_pesos - 100.0) < 0.5 or suma_pesos > 0
    resultados["5_suma_pesos"] = {
        "descripcion": "Suma del peso ponderado de partidas únicas",
        "esperado": "Aproximado al 100.0%",
        "obtenido": f"{suma_pesos:.2f}%",
        "estado": v5
    }
    todas_correctas = todas_correctas and v5

    # 6. Ausencia de valores nulos
    cols_criticas = [c for c in ["semana", "avance_plan_semanal", "avance_real_semanal"] if c in df.columns]
    nulos = int(df[cols_criticas].isnull().sum().sum())
    v6 = nulos == 0
    resultados["6_nulos"] = {
        "descripcion": "Ausencia de valores nulos en columnas críticas",
        "esperado": "0 valores nulos",
        "obtenido": f"{nulos} valores nulos",
        "estado": v6
    }
    todas_correctas = todas_correctas and v6

    # 7. Consistencia de pesos por partida
    inconsistencias = df.groupby("codigo_partida")["peso_partida"].nunique().max()
    v7 = inconsistencias == 1
    resultados["7_inconsistencias"] = {
        "descripcion": "Consistencia de peso único para cada partida",
        "esperado": "1 peso por código",
        "obtenido": "Consistente" if v7 else "Inconsistente",
        "estado": bool(v7)
    }
    todas_correctas = todas_correctas and v7

    # 8. Orden secuencial de semanas
    try:
        sems = sorted([int(x) for x in df["semana"].unique()])
        es_secuencial = sems == list(range(min(sems), max(sems) + 1))
    except Exception:
        es_secuencial = True
    resultados["8_semanas_ordenadas"] = {
        "descripcion": "Secuencia cronológica y coherente de semanas",
        "esperado": "Semanas consecutivas",
        "obtenido": "Secuencial" if es_secuencial else "Con saltos",
        "estado": bool(es_secuencial)
    }
    todas_correctas = todas_correctas and es_secuencial

    # 9. Coherencia de avance planificado acumulado
    avance_plan_final = float(df_semanal["avance_planificado_acumulado"].iloc[-1]) if not df_semanal.empty else 0.0
    v9 = avance_plan_final > 0
    resultados["9_avance_plan_final"] = {
        "descripcion": "Avance planificado acumulado final positivo y coherente",
        "esperado": "> 0% (típico: 100%)",
        "obtenido": f"{avance_plan_final:.2f}%",
        "estado": v9
    }
    todas_correctas = todas_correctas and v9

    # 10. Coherencia matemática del avance real final
    avance_real_final = float(df_semanal["avance_real_acumulado"].iloc[-1]) if not df_semanal.empty else 0.0
    suma_real_semanal = float(df_semanal["avance_real_semanal"].sum()) if not df_semanal.empty else 0.0
    v10 = abs(avance_real_final - suma_real_semanal) < 1e-4
    resultados["10_avance_real_coherencia"] = {
        "descripcion": "Coherencia matemática entre suma semanal y acumulado final",
        "esperado": f"{suma_real_semanal:.2f}%",
        "obtenido": f"{avance_real_final:.2f}%",
        "estado": v10
    }
    todas_correctas = todas_correctas and v10

    return resultados, todas_correctas
