"""
==============================================================================
AVANCE FÍSICO DE OBRA — Sistema de Seguimiento y Control
Aplicativo Web interactivo en Streamlit.
==============================================================================
"""

import os
import streamlit as st
import pandas as pd

# Importar módulos de lógica separada según arquitectura requerida
from modules.carga_datos import cargar_datos_desde_fuente
from modules.calculos import (
    procesar_avance_obra,
    obtener_kpis,
    generar_tabla_control_avance,
    tiene_columnas_especialidad_encargado,
    calcular_avance_por_especialidad,
    calcular_partidas_por_encargado,
    calcular_avance_por_encargado
)
from modules.graficos import (
    crear_grafico_curva_s,
    crear_grafico_produccion_semanal,
    crear_grafico_diferencia,
    crear_grafico_costos,
    crear_grafico_avance_real_acumulado,
    crear_graficos_especialidad_encargado,
    guardar_grafico_png
)
from modules.exportacion import (
    generar_excel_multihoja,
    generar_excel_tabla_simple,
    generar_csv_tabla_simple
)

# ------------------------------------------------------------------------------
# Configuración inicial de la página en Streamlit
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Control de Avance Físico de Obra",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    # --------------------------------------------------------------------------
    # ENCABEZADO DE LA APLICACIÓN
    # --------------------------------------------------------------------------
    st.title("🏗️ AVANCE FÍSICO DE OBRA")
    st.caption("Sistema de Seguimiento, Control y Análisis Gráfico")
    st.divider()

    # --------------------------------------------------------------------------
    # BARRA LATERAL: CARGA DE DATOS
    # --------------------------------------------------------------------------
    st.sidebar.header("📁 Carga de Datos")
    
    opcion_fuente = st.sidebar.radio(
        "Seleccione la fuente de datos:",
        ["Cargar archivo (CSV / XLSX)", "Usar archivo de ejemplo (datos_avance_sinteticos.csv)"],
        key="radio_fuente_datos"
    )

    df_raw = None
    mensaje_error = None
    ruta_ejemplo = os.path.join("data", "datos_avance_sinteticos.csv")

    if opcion_fuente == "Cargar archivo (CSV / XLSX)":
        archivo_subido = st.sidebar.file_uploader(
            "Cargar archivo CSV o Excel XLSX",
            type=["csv", "xlsx", "xls"],
            help="Suba su archivo con las columnas obligatorias: Periodo, Fecha, Avance_Planificado_Periodo_%, Avance_Real_Periodo_%",
            key="uploader_archivo_avance"
        )
        if archivo_subido is not None:
            df_raw, mensaje_error = cargar_datos_desde_fuente(archivo_subido)
        else:
            st.sidebar.info("Por favor, suba un archivo CSV/XLSX o seleccione la opción de datos sintéticos de ejemplo.")
    else:
        # Cargar archivo de prueba por defecto
        if os.path.exists(ruta_ejemplo):
            df_raw, mensaje_error = cargar_datos_desde_fuente(ruta_ejemplo)
            st.sidebar.success(f"Cargado exitosamente: `{os.path.basename(ruta_ejemplo)}`")
        else:
            st.sidebar.error(f"No se encontró el archivo de ejemplo en: `{ruta_ejemplo}`")

    # Si hay un error al validar columnas o datos
    if mensaje_error:
        st.error(f"❌ **Error en la carga de datos:**\n\n{mensaje_error}")
    elif df_raw is None:
        st.info("💡 **Instrucción:** Cargue un archivo CSV o Excel desde el menú lateral para iniciar el análisis de la obra.")
    else:
        # --------------------------------------------------------------------------
        # CÁLCULOS CON PANDAS (Usando módulo calculos.py)
        # --------------------------------------------------------------------------
        df_procesado = procesar_avance_obra(df_raw)
        kpis = obtener_kpis(df_procesado)
        df_tabla = generar_tabla_control_avance(df_procesado)

        # Exportación automática del último gráfico en PNG como requiere el requerimiento 13
        fig_ultimo_auto = crear_grafico_avance_real_acumulado(df_procesado)
        ruta_png_auto = os.path.join("outputs", "graficos", "avance_real_acumulado.png")
        try:
            guardar_grafico_png(fig_ultimo_auto, ruta_png_auto)
        except Exception:
            pass

        # --------------------------------------------------------------------------
        # SECCIÓN 1: INDICADORES PRINCIPALES (TARJETAS KPI)
        # --------------------------------------------------------------------------
        st.subheader("📌 Indicadores Principales (KPIs)")

        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

        with kpi_col1:
            st.metric(
                label="Avance Planificado Acumulado",
                value=f"{kpis['avance_planificado_acumulado']:.2f} %"
            )

        with kpi_col2:
            st.metric(
                label="Avance Real Acumulado",
                value=f"{kpis['avance_real_acumulado']:.2f} %"
            )

        with kpi_col3:
            st.metric(
                label="Diferencia",
                value=f"{kpis['diferencia']:+.2f} %",
                delta=f"{kpis['diferencia']:.2f} %"
            )

        with kpi_col4:
            st.metric(
                label="Estado de la Obra",
                value=kpis['estado']
            )

        st.divider()

        # --------------------------------------------------------------------------
        # SECCIÓN 2: TABLA DE RESULTADOS "CONTROL DE AVANCE FÍSICO"
        # --------------------------------------------------------------------------
        st.subheader("📋 CONTROL DE AVANCE FÍSICO")
        
        # Formatear la vista en Streamlit con porcentajes a 2 decimales
        df_tabla_display = df_tabla.copy()
        columnas_porcentaje = [
            "Avance planificado semanal",
            "Avance real semanal",
            "Avance planificado acumulado",
            "Avance real acumulado",
            "Diferencia"
        ]
        
        for col in columnas_porcentaje:
            df_tabla_display[col] = df_tabla_display[col].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            df_tabla_display,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        # --------------------------------------------------------------------------
        # SECCIÓN 3: GRÁFICOS INTERACTIVOS CON PLOTLY
        # --------------------------------------------------------------------------
        st.subheader("📊 Gráficos del Proyecto")

        # GRÁFICO 1 — CURVA S
        st.markdown("##### 1. Curva S — Avance Planificado vs Avance Real")
        fig_curva_s = crear_grafico_curva_s(df_procesado)
        st.plotly_chart(fig_curva_s, use_container_width=True)

        # GRÁFICO 2 — PRODUCCIÓN SEMANAL
        st.markdown("##### 2. Producción Semanal")
        fig_prod = crear_grafico_produccion_semanal(df_procesado)
        st.plotly_chart(fig_prod, use_container_width=True)

        # GRÁFICO 3 — DIFERENCIA DE AVANCE
        st.markdown("##### 3. Diferencia entre Avance Real y Planificado")
        fig_dif = crear_grafico_diferencia(df_procesado)
        st.plotly_chart(fig_dif, use_container_width=True)

        # GRÁFICO 4 — COSTO PLANIFICADO VS COSTO REAL (Si aplica)
        fig_costos = crear_grafico_costos(df_procesado)
        if fig_costos is not None:
            st.markdown("##### 4. Costo Planificado vs Costo Real")
            st.plotly_chart(fig_costos, use_container_width=True)

        # SECCIÓN DE ESPECIALIDAD Y ENCARGADO
        st.markdown("##### 5. Análisis por Especialidad y Encargado")
        if not tiene_columnas_especialidad_encargado(df_raw):
            st.warning("Los análisis por especialidad y encargado requieren que el archivo contenga las columnas Especialidad y Encargado.")
        else:
            graficos_esp_enc = crear_graficos_especialidad_encargado(df_raw)
            col_g1, col_g2 = st.columns(2)
            if "especialidad" in graficos_esp_enc:
                with col_g1:
                    st.plotly_chart(graficos_esp_enc["especialidad"], use_container_width=True)
            if "partidas_encargado" in graficos_esp_enc:
                with col_g2:
                    st.plotly_chart(graficos_esp_enc["partidas_encargado"], use_container_width=True)
            if "plan_vs_real_encargado" in graficos_esp_enc:
                st.plotly_chart(graficos_esp_enc["plan_vs_real_encargado"], use_container_width=True)

        # GRÁFICO 5 — AVANCE REAL ACUMULADO DE OBRA
        # (DEBE SER EL ÚLTIMO GRÁFICO MOSTRADO EN LA PÁGINA SEGÚN REQUERIMIENTO)
        st.markdown("##### 6. Avance Real Acumulado de Obra (Gráfico Final)")
        fig_avance_real_acum = crear_grafico_avance_real_acumulado(df_procesado)
        st.plotly_chart(fig_avance_real_acum, use_container_width=True)

        st.divider()

        # --------------------------------------------------------------------------
        # SECCIÓN 4: BOTONES DE EXPORTACIÓN
        # --------------------------------------------------------------------------
        st.subheader("📥 Exportación de Resultados")

        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)

        # A. Exportar Tabla a Excel
        excel_tabla = generar_excel_tabla_simple(df_tabla)
        with col_exp1:
            st.download_button(
                label="📄 Exportar Tabla a Excel",
                data=excel_tabla,
                file_name="Control_Avance_Fisico_Tabla.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # B. Exportar Tabla a CSV
        csv_tabla = generar_csv_tabla_simple(df_tabla)
        with col_exp2:
            st.download_button(
                label="📝 Exportar Tabla a CSV",
                data=csv_tabla,
                file_name="Control_Avance_Fisico_Tabla.csv",
                mime="text/csv",
                use_container_width=True
            )

        # C. Exportar Gráfico Final a PNG
        with col_exp3:
            try:
                img_bytes = fig_avance_real_acum.to_image(format="png", scale=2)
                st.download_button(
                    label="🖼️ Exportar Gráfico PNG",
                    data=img_bytes,
                    file_name="avance_real_acumulado.png",
                    mime="image/png",
                    use_container_width=True
                )
            except Exception:
                st.button("🖼️ Exportar Gráfico PNG", disabled=True, help="Instale kaleido para exportar PNG")

        # D. Exportar Resultados Completos a Excel (Multi-hoja)
        excel_multi = generar_excel_multihoja(df_procesado, df_tabla, kpis)
        with col_exp4:
            st.download_button(
                label="📊 Reporte Completo Excel",
                data=excel_multi,
                file_name="Reporte_Completo_Avance_Obra.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    # Pie de página
    st.divider()
    st.caption("Desarrollado para el Análisis del Avance Físico de Obra con Python, Pandas, Plotly y Streamlit.")


if __name__ == "__main__":
    main()
