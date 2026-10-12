"""
Módulo de Generación de Gráficos con Matplotlib para Avance Físico de Obra.

Todos los gráficos se generan exclusivamente con Matplotlib, aplicando una diagramación
y estética profesional de nivel corporativo:
- Paleta cromática armónica y accesible
- Tipografía limpia y jerarquizada
- Cuadrículas suaves y bordes limpios
- Etiquetas y anotaciones numéricas legibles
- Funciones que retornan objetos Figure independientes
- Conversión a PNG en alta resolución para descarga
"""

import io
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from typing import Optional

# Configuración de paleta cromática profesional
COLOR_AZUL_PRINCIPAL = "#1F4E78"    # Azul corporativo profundo
COLOR_AZUL_SECUNDARIO = "#4A90E2"   # Azul cielo vibrante
COLOR_VERDE_REAL = "#008080"        # Teal / Verde azulado
COLOR_VERDE_ADELANTO = "#2E8B57"    # Verde bosque
COLOR_VERDE_FONDO = "#C6EFCE"       # Verde pastel suave para áreas de adelanto
COLOR_ROJO_RETRASO = "#D9534F"      # Rojo salmón advertencia
COLOR_ROJO_FONDO = "#FFC7CE"        # Rojo pastel suave para áreas de retraso
COLOR_AMARILLO_ALERTA = "#F0AD4E"   # Amarillo advertencia
COLOR_GRIS_GRID = "#E2E8F0"         # Gris suave para cuadrículas
COLOR_TEXTO = "#1E293B"             # Texto oscuro pizarra

# Configurar parámetros globales de estilo para Matplotlib
plt.rcParams.update({
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"],
    "font.family": "sans-serif",
    "axes.edgecolor": "#CBD5E1",
    "axes.linewidth": 1.0,
    "figure.autolayout": False,
    "figure.facecolor": "#FFFFFF",
    "axes.facecolor": "#FFFFFF",
    "text.color": COLOR_TEXTO,
    "axes.labelcolor": COLOR_TEXTO,
    "xtick.color": COLOR_TEXTO,
    "ytick.color": COLOR_TEXTO
})


def _limpiar_ejes(ax: plt.Axes, grid_y: bool = True, grid_x: bool = False):
    """Elimina bordes superior y derecho y añade cuadrícula sutil."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")
    
    if grid_y:
        ax.grid(True, axis="y", linestyle="--", alpha=0.6, color=COLOR_GRIS_GRID, zorder=0)
    if grid_x:
        ax.grid(True, axis="x", linestyle="--", alpha=0.6, color=COLOR_GRIS_GRID, zorder=0)


def figura_curva_s(df_semanal: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 1 — CURVA S DE AVANCE ACUMULADO (MATPLOTLIB)
    Curva S comparando Avance Planificado Acumulado vs Avance Real Acumulado.
    Incluye sombreado entre curvas para evidenciar visualmente adelantos o retrasos.
    """
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=150)
    
    x = df_semanal["semana"]
    y_plan = df_semanal["avance_planificado_acumulado"]
    y_real = df_semanal["avance_real_acumulado"]

    # Línea Planificada
    ax.plot(
        x, y_plan,
        marker="o", markersize=6, linewidth=2.8, linestyle="--",
        color=COLOR_AZUL_PRINCIPAL, label="Planificado Acumulado", zorder=4
    )

    # Línea Real
    ax.plot(
        x, y_real,
        marker="s", markersize=6.5, linewidth=3.0,
        color=COLOR_VERDE_REAL, label="Real Acumulado", zorder=5
    )

    # Sombreado dinámico entre curvas (Adelanto / Retraso)
    ax.fill_between(
        x, y_plan, y_real,
        where=(y_real >= y_plan),
        interpolate=True, color=COLOR_VERDE_FONDO, alpha=0.5, label="Adelanto", zorder=2
    )
    ax.fill_between(
        x, y_plan, y_real,
        where=(y_real < y_plan),
        interpolate=True, color=COLOR_ROJO_FONDO, alpha=0.5, label="Retraso", zorder=2
    )

    # Anotaciones numéricas en puntos representativos (primera semana, mitad y final)
    n_total = len(df_semanal)
    indices_mostrar = {0, n_total // 2, n_total - 1} if n_total >= 3 else set(range(n_total))

    for idx in indices_mostrar:
        row = df_semanal.iloc[idx]
        sem = row["semana"]
        ax.annotate(
            f"{row['avance_planificado_acumulado']:.1f}%",
            (sem, row["avance_planificado_acumulado"]),
            textcoords="offset points", xytext=(0, 10), ha="center",
            fontsize=8.5, fontweight="bold", color=COLOR_AZUL_PRINCIPAL
        )
        ax.annotate(
            f"{row['avance_real_acumulado']:.1f}%",
            (sem, row["avance_real_acumulado"]),
            textcoords="offset points", xytext=(0, -16), ha="center",
            fontsize=8.5, fontweight="bold", color=COLOR_VERDE_REAL
        )

    ax.set_title("Curva S — Avance Planificado vs Avance Real Acumulado", fontsize=13, fontweight="bold", pad=16, color=COLOR_AZUL_PRINCIPAL)
    ax.set_xlabel("Semana de Control", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_ylabel("Avance Acumulado (%)", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_ylim(-2, max(max(y_plan.max(), y_real.max()) * 1.12, 105))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100.0, decimals=0))
    
    _limpiar_ejes(ax, grid_y=True)
    ax.legend(loc="upper left", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.5)
    fig.tight_layout()
    return fig


def figura_produccion_semanal(df_semanal: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 2 — PRODUCCIÓN SEMANAL (MATPLOTLIB)
    Barras agrupadas comparando el avance semanal planificado vs real en cada periodo.
    """
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    
    indices = np.arange(len(df_semanal))
    ancho = 0.36
    
    bar_plan = ax.bar(
        indices - ancho / 2, df_semanal["avance_planificado_semanal"], ancho,
        label="Planificado Semanal", color=COLOR_AZUL_SECUNDARIO, edgecolor=COLOR_AZUL_PRINCIPAL,
        linewidth=0.8, alpha=0.9, zorder=3
    )
    bar_real = ax.bar(
        indices + ancho / 2, df_semanal["avance_real_semanal"], ancho,
        label="Real Semanal", color=COLOR_VERDE_REAL, edgecolor="#004D40",
        linewidth=0.8, alpha=0.9, zorder=3
    )

    # Anotar valores sobre las barras
    for bar in bar_plan:
        alt = bar.get_height()
        if alt > 0.05:
            ax.annotate(
                f"{alt:.1f}%",
                (bar.get_x() + bar.get_width() / 2, alt),
                textcoords="offset points", xytext=(0, 3), ha="center", va="bottom",
                fontsize=7.5, color=COLOR_AZUL_PRINCIPAL, fontweight="bold"
            )

    for bar in bar_real:
        alt = bar.get_height()
        if alt > 0.05:
            ax.annotate(
                f"{alt:.1f}%",
                (bar.get_x() + bar.get_width() / 2, alt),
                textcoords="offset points", xytext=(0, 3), ha="center", va="bottom",
                fontsize=7.5, color=COLOR_VERDE_REAL, fontweight="bold"
            )

    ax.set_title("Producción Semanal — Avance Planificado vs Real", fontsize=13, fontweight="bold", pad=16, color=COLOR_AZUL_PRINCIPAL)
    ax.set_xlabel("Semana de Control", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_ylabel("Avance del Periodo (%)", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_xticks(indices)
    ax.set_xticklabels(df_semanal["semana"])
    
    max_val = max(df_semanal["avance_planificado_semanal"].max(), df_semanal["avance_real_semanal"].max())
    ax.set_ylim(0, max_val * 1.18 if max_val > 0 else 10)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100.0, decimals=0))

    _limpiar_ejes(ax, grid_y=True)
    ax.legend(loc="upper right", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.5)
    fig.tight_layout()
    return fig


def figura_diferencia_avance(df_semanal: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 3 — DIFERENCIA Y BRECHA DE AVANCE (MATPLOTLIB)
    Barras divergentes para la diferencia acumulada y semanal.
    Verde = Adelanto (Diferencia >= 0), Rojo = Retraso (Diferencia < 0).
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.8), dpi=150, sharex=True)

    x = np.arange(len(df_semanal))
    ancho = 0.55

    # 1. Diferencia Acumulada
    colores_acum = [COLOR_VERDE_ADELANTO if d >= 0 else COLOR_ROJO_RETRASO for d in df_semanal["diferencia_acumulada"]]
    bar_acum = ax1.bar(
        x, df_semanal["diferencia_acumulada"], ancho,
        color=colores_acum, edgecolor="#334155", linewidth=0.7, zorder=3
    )
    ax1.axhline(0, color="#475569", linestyle="-", linewidth=1.1, zorder=4)
    ax1.set_title("Brecha Acumulada (% Real Acumulado - % Planificado Acumulado)", fontsize=11.5, fontweight="bold", pad=10, color=COLOR_AZUL_PRINCIPAL)
    ax1.set_ylabel("Diferencia (%)", fontsize=10, fontweight="bold")
    _limpiar_ejes(ax1, grid_y=True)

    for bar in bar_acum:
        h = bar.get_height()
        va_align = "bottom" if h >= 0 else "top"
        offset = 3 if h >= 0 else -10
        ax1.annotate(
            f"{h:+.2f}%",
            (bar.get_x() + bar.get_width() / 2, h),
            textcoords="offset points", xytext=(0, offset), ha="center", va=va_align,
            fontsize=8, fontweight="bold",
            color=COLOR_VERDE_ADELANTO if h >= 0 else COLOR_ROJO_RETRASO
        )

    # 2. Diferencia Semanal
    colores_sem = [COLOR_VERDE_ADELANTO if d >= 0 else COLOR_ROJO_RETRASO for d in df_semanal["diferencia_semanal"]]
    bar_sem = ax2.bar(
        x, df_semanal["diferencia_semanal"], ancho,
        color=colores_sem, edgecolor="#334155", linewidth=0.7, zorder=3
    )
    ax2.axhline(0, color="#475569", linestyle="-", linewidth=1.1, zorder=4)
    ax2.set_title("Brecha Semanal (% Real Semanal - % Planificado Semanal)", fontsize=11.5, fontweight="bold", pad=10, color=COLOR_AZUL_PRINCIPAL)
    ax2.set_xlabel("Semana de Control", fontsize=10.5, labelpad=8, fontweight="bold")
    ax2.set_ylabel("Diferencia (%)", fontsize=10, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(df_semanal["semana"])
    _limpiar_ejes(ax2, grid_y=True)

    for bar in bar_sem:
        h = bar.get_height()
        va_align = "bottom" if h >= 0 else "top"
        offset = 3 if h >= 0 else -10
        ax2.annotate(
            f"{h:+.2f}%",
            (bar.get_x() + bar.get_width() / 2, h),
            textcoords="offset points", xytext=(0, offset), ha="center", va=va_align,
            fontsize=8, fontweight="bold",
            color=COLOR_VERDE_ADELANTO if h >= 0 else COLOR_ROJO_RETRASO
        )

    fig.tight_layout()
    return fig


def figura_avance_real_acumulado(df_semanal: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 4 — AVANCE REAL ACUMULADO DE OBRA (MATPLOTLIB)
    Gráfico de área rellena destacando el progreso total ejecutado del proyecto.
    """
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)

    x = df_semanal["semana"]
    y_real = df_semanal["avance_real_acumulado"]

    ax.fill_between(x, y_real, color=COLOR_VERDE_REAL, alpha=0.25, zorder=2)
    ax.plot(x, y_real, marker="o", markersize=6.5, linewidth=3.0, color=COLOR_VERDE_REAL, zorder=4)

    # Anotación del avance final alcanzado
    if not df_semanal.empty:
        ultimo_sem = df_semanal["semana"].iloc[-1]
        ultimo_val = y_real.iloc[-1]
        ax.annotate(
            f"Avance Final: {ultimo_val:.2f}%",
            (ultimo_sem, ultimo_val),
            textcoords="offset points", xytext=(-20, 14), ha="center",
            fontsize=10, fontweight="bold", color="#004D40",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#E6FFFA", edgecolor="#008080", alpha=0.9)
        )

    ax.set_title("Avance Real Acumulado de la Obra (Progreso Consolidado)", fontsize=13, fontweight="bold", pad=16, color=COLOR_AZUL_PRINCIPAL)
    ax.set_xlabel("Semana de Control", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_ylabel("Avance Acumulado (%)", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_ylim(0, max(y_real.max() * 1.15, 105))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100.0, decimals=0))

    _limpiar_ejes(ax, grid_y=True)
    fig.tight_layout()
    return fig


def figura_avance_especialidad(df_especialidad: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 5 — AVANCE POR ESPECIALIDAD (MATPLOTLIB)
    Barras horizontales comparando avance planificado vs avance real por especialidad.
    """
    fig, ax = plt.subplots(figsize=(9, 5.0), dpi=150)

    # Ordenar de menor a mayor para que la más alta aparezca arriba
    df_sorted = df_especialidad.sort_values(by="avance_real", ascending=True).reset_index(drop=True)
    y_pos = np.arange(len(df_sorted))
    alto = 0.38

    bars_plan = ax.barh(
        y_pos + alto / 2, df_sorted["avance_planificado"], alto,
        label="Planificado Total", color=COLOR_AZUL_SECUNDARIO, edgecolor=COLOR_AZUL_PRINCIPAL,
        alpha=0.85, zorder=3
    )
    bars_real = ax.barh(
        y_pos - alto / 2, df_sorted["avance_real"], alto,
        label="Real Total", color=COLOR_VERDE_REAL, edgecolor="#004D40",
        alpha=0.9, zorder=3
    )

    # Etiquetas de valor en las barras
    for bar in bars_real:
        w = bar.get_width()
        ax.text(
            w + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{w:.1f}%", va="center", ha="left",
            fontsize=8.5, fontweight="bold", color=COLOR_VERDE_REAL
        )

    ax.set_title("Avance Acumulado por Especialidad (Plan vs Real)", fontsize=12.5, fontweight="bold", pad=15, color=COLOR_AZUL_PRINCIPAL)
    ax.set_xlabel("Avance Total (%)", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_sorted["especialidad"], fontsize=9.5, fontweight="bold")
    ax.set_xlim(0, max(df_sorted["avance_planificado"].max(), df_sorted["avance_real"].max()) * 1.25)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(100.0, decimals=0))

    _limpiar_ejes(ax, grid_x=True, grid_y=False)
    ax.legend(loc="lower right", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9)
    fig.tight_layout()
    return fig


def figura_partidas_encargado(df_partidas_encargado: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 6 — CANTIDAD DE PARTIDAS POR ENCARGADO (MATPLOTLIB)
    Barras verticales con la cantidad de partidas asignadas por responsable.
    """
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)

    x = np.arange(len(df_partidas_encargado))
    ancho = 0.5

    bars = ax.bar(
        x, df_partidas_encargado["cantidad_partidas"], ancho,
        color=COLOR_AZUL_PRINCIPAL, edgecolor="#0F172A", alpha=0.9, zorder=3
    )

    for bar in bars:
        h = bar.get_height()
        ax.annotate(
            f"{int(h)} partidas",
            (bar.get_x() + bar.get_width() / 2, h),
            textcoords="offset points", xytext=(0, 4), ha="center", va="bottom",
            fontsize=9.5, fontweight="bold", color=COLOR_AZUL_PRINCIPAL
        )

    ax.set_title("Cantidad de Partidas Asignadas por Encargado", fontsize=12.5, fontweight="bold", pad=15, color=COLOR_AZUL_PRINCIPAL)
    ax.set_xlabel("Encargado de Obra", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_ylabel("N° de Partidas", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df_partidas_encargado["encargado"], fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, df_partidas_encargado["cantidad_partidas"].max() + 1.8)

    _limpiar_ejes(ax, grid_y=True)
    fig.tight_layout()
    return fig


def figura_avance_encargado(df_avance_encargado: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 7 — COMPARATIVA PLAN VS REAL POR ENCARGADO (MATPLOTLIB)
    Barras agrupadas de avance planificado vs real por cada profesional.
    """
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=150)

    x = np.arange(len(df_avance_encargado))
    ancho = 0.35

    bar_plan = ax.bar(
        x - ancho / 2, df_avance_encargado["avance_planificado"], ancho,
        label="Planificado Total", color=COLOR_AZUL_SECUNDARIO, edgecolor=COLOR_AZUL_PRINCIPAL,
        alpha=0.85, zorder=3
    )
    bar_real = ax.bar(
        x + ancho / 2, df_avance_encargado["avance_real"], ancho,
        label="Real Total", color=COLOR_VERDE_ADELANTO, edgecolor="#1B5E20",
        alpha=0.9, zorder=3
    )

    for bar in bar_plan:
        h = bar.get_height()
        ax.annotate(
            f"{h:.1f}%",
            (bar.get_x() + bar.get_width() / 2, h),
            textcoords="offset points", xytext=(0, 3), ha="center", va="bottom",
            fontsize=8, fontweight="bold", color=COLOR_AZUL_PRINCIPAL
        )

    for bar in bar_real:
        h = bar.get_height()
        ax.annotate(
            f"{h:.1f}%",
            (bar.get_x() + bar.get_width() / 2, h),
            textcoords="offset points", xytext=(0, 3), ha="center", va="bottom",
            fontsize=8, fontweight="bold", color=COLOR_VERDE_ADELANTO
        )

    ax.set_title("Avance Planificado vs Real por Encargado", fontsize=12.5, fontweight="bold", pad=15, color=COLOR_AZUL_PRINCIPAL)
    ax.set_xlabel("Encargado de Obra", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_ylabel("Avance (%)", fontsize=10.5, labelpad=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(df_avance_encargado["encargado"], fontsize=9.5, fontweight="bold")
    
    max_h = max(df_avance_encargado["avance_planificado"].max(), df_avance_encargado["avance_real"].max())
    ax.set_ylim(0, max_h * 1.20)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(100.0, decimals=0))

    _limpiar_ejes(ax, grid_y=True)
    ax.legend(loc="upper right", frameon=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.5)
    fig.tight_layout()
    return fig


def figura_distribucion_especialidad(df_distribucion: pd.DataFrame) -> plt.Figure:
    """
    GRÁFICO 8 — DISTRIBUCIÓN DE PESO POR ESPECIALIDAD (MATPLOTLIB)
    Gráfico de dona (Donut chart) con proporciones porcentuales.
    """
    fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=150)

    colores = ["#1F4E78", "#008080", "#4A90E2", "#F0AD4E", "#2E8B57", "#9333EA", "#EA580C"]
    colores = colores[:len(df_distribucion)]

    wedges, texts, autotexts = ax.pie(
        df_distribucion["peso_total"],
        labels=df_distribucion["especialidad"],
        autopct="%1.1f%%",
        startangle=140,
        colors=colores,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
        pctdistance=0.75
    )

    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
        at.set_fontsize(9)

    ax.set_title("Distribución de Peso Ponderado por Especialidad", fontsize=12.5, fontweight="bold", pad=14, color=COLOR_AZUL_PRINCIPAL)
    fig.tight_layout()
    return fig


def convertir_figura_a_bytes(fig: plt.Figure, dpi: int = 150) -> bytes:
    """
    Convierte una figura de Matplotlib en bytes PNG para descarga en Streamlit.
    """
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    buffer.seek(0)
    return buffer.getvalue()
