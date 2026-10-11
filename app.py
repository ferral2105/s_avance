"""
==============================================================================
SISTEMA DE CONTROL Y SEGUIMIENTO DE AVANCE FÍSICO DE OBRA
Aplicación Web Interactiva con Streamlit, Matplotlib y Pandas.
==============================================================================
"""

import os
import io
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

import importlib
import modules.carga_datos
import modules.calculos
import modules.graficos
import modules.exportacion

importlib.reload(modules.carga_datos)
importlib.reload(modules.calculos)
importlib.reload(modules.graficos)
importlib.reload(modules.exportacion)

# Importación de módulos desacoplados
from modules.carga_datos import cargar_datos_desde_fuente
from modules.calculos import (
    calcular_avance_semanal,
    calcular_kpis_principales,
    calcular_avance_especialidad,
    calcular_partidas_encargado,
    calcular_avance_encargado,
    calcular_distribucion_especialidad,
    calcular_resumen_partidas,
    validar_datos_proyecto
)
from modules.graficos import (
    figura_curva_s,
    figura_produccion_semanal,
    figura_diferencia_avance,
    figura_avance_real_acumulado,
    figura_avance_especialidad,
    figura_partidas_encargado,
    figura_avance_encargado,
    figura_distribucion_especialidad,
    convertir_figura_a_bytes
)
from modules.exportacion import (
    generar_excel_completo,
    generar_csv_tabla,
    generar_zip_graficos
)

# ------------------------------------------------------------------------------
# CONFIGURACIÓN INICIAL DE STREAMLIT
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Control de Avance Físico de Obra",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para una diagramación limpia y moderna
st.markdown("""
<style>
    /* Estilos para métricas KPI */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: #1F4E78 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
    }
    /* Tarjeta de estado de obra */
    .status-card {
        padding: 12px 18px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        margin-top: 5px;
        margin-bottom: 12px;
    }
    .status-adelantada {
        background-color: #D4EDDA;
        color: #155724;
        border: 1px solid #C3E6CB;
    }
    .status-plan {
        background-color: #FFF3CD;
        color: #856404;
        border: 1px solid #FFEEBA;
    }
    .status-retrasada {
        background-color: #F8D7DA;
        color: #721C24;
        border: 1px solid #F5C6CB;
    }
    /* Estilos para títulos de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        font-weight: 600;
        border-radius: 6px 6px 0 0;
    }
</style>
""", unsafe_allow_html=True)


def obtener_rutas_archivos_proyecto():
    """Busca archivos CSV y Excel disponibles en el proyecto."""
    archivos = []
    # Buscar en la raíz y en la carpeta data
    rutas_buscar = [
        ".",
        "data",
        os.path.join(".."),
        os.path.join(".", "app_avance_obra", "data")
    ]
    nombres_vistos = set()
    for dir_ruta in rutas_buscar:
        if os.path.exists(dir_ruta):
            for f in os.listdir(dir_ruta):
                if f.lower().endswith((".csv", ".xlsx")) and not f.startswith("~"):
                    ruta_completa = os.path.join(dir_ruta, f)
                    if f not in nombres_vistos and os.path.isfile(ruta_completa):
                        archivos.append((f, ruta_completa))
                        nombres_vistos.add(f)
    return archivos


def main():
    # --------------------------------------------------------------------------
    # BARRA LATERAL (SIDEBAR)
    # --------------------------------------------------------------------------
    st.sidebar.title("🏗️ Control de Avance")
    st.sidebar.caption("Sistema de Monitoreo y Análisis de Obras")
    st.sidebar.divider()

    st.sidebar.header("📁 1. Carga de Datos")
    metodo_carga = st.sidebar.radio(
        "Origen del archivo:",
        ["Seleccionar archivo del proyecto", "Cargar archivo propio (CSV / XLSX)"],
        index=0,
        key="radio_origen_datos"
    )

    df_raw = None
    error_carga = None
    nombre_fuente = ""

    if metodo_carga == "Seleccionar archivo del proyecto":
        archivos_disponibles = obtener_rutas_archivos_proyecto()
        if archivos_disponibles:
            opciones_dict = {f"{nom} ({os.path.basename(os.path.dirname(r) or 'raíz')})": r for nom, r in archivos_disponibles}
            # Priorizar base_datos_avance_obra_12_semanas.csv si existe
            idx_default = 0
            for idx, (label, path) in enumerate(opciones_dict.items()):
                if "base_datos_avance_obra_12_semanas.csv" in label:
                    idx_default = idx
                    break

            archivo_elegido_label = st.sidebar.selectbox(
                "Seleccione archivo:",
                list(opciones_dict.keys()),
                index=idx_default,
                key="select_archivo_proyecto"
            )
            ruta_elegida = opciones_dict[archivo_elegido_label]
            nombre_fuente = os.path.basename(ruta_elegida)
            df_raw, error_carga = cargar_datos_desde_fuente(ruta_elegida)
            st.sidebar.success(f"Archivo cargado: `{nombre_fuente}`")
        else:
            st.sidebar.warning("No se encontraron archivos CSV/Excel en el directorio.")
    else:
        archivo_subido = st.sidebar.file_uploader(
            "Subir archivo de avance:",
            type=["csv", "xlsx", "xls"],
            help="Soporta CSV con separador por coma o punto y coma, y hojas de cálculo Excel.",
            key="file_uploader_avance"
        )
        if archivo_subido is not None:
            nombre_fuente = archivo_subido.name
            df_raw, error_carga = cargar_datos_desde_fuente(archivo_subido)
        else:
            st.sidebar.info("💡 Por favor, suba un archivo CSV o arrástrelo a este panel.")

    # Detener ejecución si ocurrió un error de lectura
    if error_carga:
        st.error(f"❌ **Error al procesar el archivo:**\n\n{error_carga}")
        return

    if df_raw is None:
        st.info("👆 Seleccione o cargue un archivo CSV desde la barra lateral para comenzar.")
        return

    # --------------------------------------------------------------------------
    # FILTROS DINÁMICOS EN SIDEBAR
    # --------------------------------------------------------------------------
    st.sidebar.divider()
    st.sidebar.header("🎯 2. Filtros de Análisis")

    # Filtro por rango de semanas
    semanas_disponibles = sorted(list(df_raw["semana"].unique()))
    try:
        semanas_numericas = [int(s) for s in semanas_disponibles]
        min_sem, max_sem = min(semanas_numericas), max(semanas_numericas)
        rango_semanas = st.sidebar.slider(
            "Rango de Semanas a evaluar:",
            min_value=min_sem,
            max_value=max_sem,
            value=(min_sem, max_sem),
            step=1
        )
        filtro_semanas = list(range(rango_semanas[0], rango_semanas[1] + 1))
    except Exception:
        filtro_semanas = st.sidebar.multiselect(
            "Seleccionar Semanas:",
            options=semanas_disponibles,
            default=semanas_disponibles
        )

    # Filtro por Especialidad
    especialidades_disponibles = sorted(list(df_raw["especialidad"].dropna().unique()))
    especialidad_sel = st.sidebar.multiselect(
        "Filtrar por Especialidad:",
        options=especialidades_disponibles,
        default=especialidades_disponibles
    )

    # Filtro por Encargado
    encargados_disponibles = sorted(list(df_raw["encargado"].dropna().unique()))
    encargado_sel = st.sidebar.multiselect(
        "Filtrar por Encargado:",
        options=encargados_disponibles,
        default=encargados_disponibles
    )

    # Aplicar filtros al DataFrame
    df_filtrado = df_raw.copy()
    if filtro_semanas:
        df_filtrado = df_filtrado[df_filtrado["semana"].isin(filtro_semanas)]
    if especialidad_sel:
        df_filtrado = df_filtrado[df_filtrado["especialidad"].isin(especialidad_sel)]
    if encargado_sel:
        df_filtrado = df_filtrado[df_filtrado["encargado"].isin(encargado_sel)]

    if df_filtrado.empty:
        st.warning("⚠️ No hay registros que coincidan con los filtros seleccionados.")
        return

    # --------------------------------------------------------------------------
    # CÁLCULOS PRINCIPALES (Módulo calculos.py)
    # --------------------------------------------------------------------------
    df_semanal = calcular_avance_semanal(df_filtrado)
    kpis = calcular_kpis_principales(df_semanal, df_filtrado)
    df_especialidad = calcular_avance_especialidad(df_filtrado)
    df_partidas_encargado = calcular_partidas_encargado(df_filtrado)
    df_avance_encargado = calcular_avance_encargado(df_filtrado)
    df_distribucion_esp = calcular_distribucion_especialidad(df_filtrado)
    df_resumen_partidas = calcular_resumen_partidas(df_filtrado)
    validaciones_dict, todas_validas = validar_datos_proyecto(df_raw, df_semanal)

    # Resumen rápido en Sidebar
    st.sidebar.divider()
    st.sidebar.header("📊 Resumen Rápido")
    st.sidebar.write(f"**Periodo:** {df_semanal['semana'].min()} al {df_semanal['semana'].max()}")
    st.sidebar.write(f"**Partidas activas:** {kpis['total_partidas']}")
    st.sidebar.write(f"**Avance Real:** `{kpis['real_acum']:.2f}%`")
    st.sidebar.write(f"**Estado:** `{kpis['estado']}`")

    # --------------------------------------------------------------------------
    # ENCABEZADO PRINCIPAL DE LA PÁGINA
    # --------------------------------------------------------------------------
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.title("🏗️ SISTEMA DE CONTROL DE AVANCE FÍSICO DE OBRA")
        st.markdown(
            f"**Fuente:** `{nombre_fuente}` &nbsp;|&nbsp; "
            f"**Periodos:** {kpis['total_semanas']} semanas evaluadas &nbsp;|&nbsp; "
            f"**Partidas:** {kpis['total_partidas']} partidas monitoreadas"
        )
    with col_t2:
        # Estado de obra visual
        clase_estado = "status-plan"
        if "ADELANTADA" in kpis["estado"]:
            clase_estado = "status-adelantada"
        elif "RETRASADA" in kpis["estado"]:
            clase_estado = "status-retrasada"

        st.markdown(
            f"""
            <div class="status-card {clase_estado}">
                <div style="font-size: 0.8rem; text-transform: uppercase;">Estado General de Obra</div>
                <div style="font-size: 1.25rem;">{kpis['estado']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # --------------------------------------------------------------------------
    # TARJETAS DE INDICADORES CLAVE (KPIs)
    # --------------------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            label="Avance Planificado Acumulado",
            value=f"{kpis['plan_acum']:.2f}%",
            help="Suma porcentual programada al corte de la última semana evaluada."
        )

    with c2:
        st.metric(
            label="Avance Real Acumulado",
            value=f"{kpis['real_acum']:.2f}%",
            help="Suma porcentual realmente ejecutada al corte."
        )

    with c3:
        delta_val = f"{kpis['diferencia']:+.2f}%"
        st.metric(
            label="Diferencia / Brecha",
            value=delta_val,
            delta=delta_val,
            help="Avance Real Acumulado menos Avance Planificado Acumulado."
        )

    with c4:
        st.metric(
            label="Índice de Desempeño (SPI)",
            value=f"{kpis['spi']:.3f}",
            delta=f"{(kpis['spi'] - 1.0):+.3f}",
            help="SPI = Real Acumulado / Planificado Acumulado. > 1.0 indica avance superior a lo previsto."
        )

    with c5:
        st.metric(
            label="Cumplimiento Global",
            value=f"{kpis['cumplimiento']:.2f}%",
            help="Porcentaje alcanzado de la meta acumulada actual."
        )

    st.divider()

    # --------------------------------------------------------------------------
    # DIAGRAMACIÓN EN PESTAÑAS (TABS)
    # --------------------------------------------------------------------------
    tab_curva, tab_actores, tab_tablas, tab_calidad, tab_descargas = st.tabs([
        "📈 Curva S & Producción",
        "👥 Especialidad & Encargado",
        "📋 Tablas de Control",
        "✅ Calidad de Datos",
        "📥 Reportes & Descargas"
    ])

    # Diccionario para almacenar los bytes de todas las figuras para descarga masiva
    figuras_dict_descarga = {}

    # --------------------------------------------------------------------------
    # PESTAÑA 1: CURVA S & PRODUCCIÓN SEMANAL (MATPLOTLIB)
    # --------------------------------------------------------------------------
    with tab_curva:
        st.subheader("1. Curva S — Avance Planificado vs Avance Real Acumulado")
        st.caption("Gráfico generado con Matplotlib que compara el avance físico acumulado, destacando zonas de adelanto (verde) o retraso (rojo).")

        fig_s = figura_curva_s(df_semanal)
        st.pyplot(fig_s, use_container_width=True)
        bytes_s = convertir_figura_a_bytes(fig_s)
        figuras_dict_descarga["01_curva_S.png"] = bytes_s
        plt.close(fig_s)

        col_btn1, _ = st.columns([2, 5])
        with col_btn1:
            st.download_button(
                label="📥 Descargar Curva S (PNG)",
                data=bytes_s,
                file_name="01_curva_S.png",
                mime="image/png",
                key="btn_descarga_curva_s"
            )

        st.divider()

        # Fila de dos columnas para Producción Semanal y Diferencia
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("2. Producción Semanal")
            st.caption("Avance planificado vs real por cada semana de control.")
            fig_prod = figura_produccion_semanal(df_semanal)
            st.pyplot(fig_prod, use_container_width=True)
            bytes_prod = convertir_figura_a_bytes(fig_prod)
            figuras_dict_descarga["02_produccion_semanal.png"] = bytes_prod
            plt.close(fig_prod)
            st.download_button(
                label="📥 Descargar Producción Semanal (PNG)",
                data=bytes_prod,
                file_name="02_produccion_semanal.png",
                mime="image/png",
                key="btn_descarga_prod"
            )

        with col_g2:
            st.subheader("3. Desviación y Brecha de Avance")
            st.caption("Brecha acumulada y semanal (Verde: Adelanto | Rojo: Retraso).")
            fig_dif = figura_diferencia_avance(df_semanal)
            st.pyplot(fig_dif, use_container_width=True)
            bytes_dif = convertir_figura_a_bytes(fig_dif)
            figuras_dict_descarga["03_diferencia_avance.png"] = bytes_dif
            plt.close(fig_dif)
            st.download_button(
                label="📥 Descargar Brecha de Avance (PNG)",
                data=bytes_dif,
                file_name="03_diferencia_avance.png",
                mime="image/png",
                key="btn_descarga_dif"
            )

        st.divider()

        st.subheader("4. Avance Real Acumulado de la Obra")
        st.caption("Evolución del porcentaje consolidado de avance real ejecutado.")
        fig_real = figura_avance_real_acumulado(df_semanal)
        st.pyplot(fig_real, use_container_width=True)
        bytes_real = convertir_figura_a_bytes(fig_real)
        figuras_dict_descarga["04_avance_real_acumulado.png"] = bytes_real
        plt.close(fig_real)
        st.download_button(
            label="📥 Descargar Avance Real Acumulado (PNG)",
            data=bytes_real,
            file_name="04_avance_real_acumulado.png",
            mime="image/png",
            key="btn_descarga_real"
        )

    # --------------------------------------------------------------------------
    # PESTAÑA 2: ESPECIALIDAD & ENCARGADO (MATPLOTLIB)
    # --------------------------------------------------------------------------
    with tab_actores:
        st.subheader("Análisis por Especialidades y Responsables de Obra")
        st.caption("Evaluación de la distribución del proyecto por disciplina y desempeño por encargado.")

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            st.subheader("5. Avance Acumulado por Especialidad")
            fig_esp = figura_avance_especialidad(df_especialidad)
            st.pyplot(fig_esp, use_container_width=True)
            bytes_esp = convertir_figura_a_bytes(fig_esp)
            figuras_dict_descarga["05_avance_especialidad.png"] = bytes_esp
            plt.close(fig_esp)
            st.download_button(
                label="📥 Descargar Avance Especialidad (PNG)",
                data=bytes_esp,
                file_name="05_avance_especialidad.png",
                mime="image/png",
                key="btn_descarga_esp"
            )

        with col_e2:
            st.subheader("6. Distribución de Peso por Especialidad")
            fig_dist = figura_distribucion_especialidad(df_distribucion_esp)
            st.pyplot(fig_dist, use_container_width=True)
            bytes_dist = convertir_figura_a_bytes(fig_dist)
            figuras_dict_descarga["06_distribucion_especialidad.png"] = bytes_dist
            plt.close(fig_dist)
            st.download_button(
                label="📥 Descargar Distribución Especialidad (PNG)",
                data=bytes_dist,
                file_name="06_distribucion_especialidad.png",
                mime="image/png",
                key="btn_descarga_dist"
            )

        st.divider()

        col_enc1, col_enc2 = st.columns(2)

        with col_enc1:
            st.subheader("7. Cantidad de Partidas por Encargado")
            fig_pe = figura_partidas_encargado(df_partidas_encargado)
            st.pyplot(fig_pe, use_container_width=True)
            bytes_pe = convertir_figura_a_bytes(fig_pe)
            figuras_dict_descarga["07_partidas_encargado.png"] = bytes_pe
            plt.close(fig_pe)
            st.download_button(
                label="📥 Descargar Partidas por Encargado (PNG)",
                data=bytes_pe,
                file_name="07_partidas_encargado.png",
                mime="image/png",
                key="btn_descarga_pe"
            )

        with col_enc2:
            st.subheader("8. Avance Planificado vs Real por Encargado")
            fig_ae = figura_avance_encargado(df_avance_encargado)
            st.pyplot(fig_ae, use_container_width=True)
            bytes_ae = convertir_figura_a_bytes(fig_ae)
            figuras_dict_descarga["08_avance_encargado.png"] = bytes_ae
            plt.close(fig_ae)
            st.download_button(
                label="📥 Descargar Avance por Encargado (PNG)",
                data=bytes_ae,
                file_name="08_avance_encargado.png",
                mime="image/png",
                key="btn_descarga_ae"
            )

    # --------------------------------------------------------------------------
    # PESTAÑA 3: TABLAS DE CONTROL DE AVANCE
    # --------------------------------------------------------------------------
    with tab_tablas:
        st.subheader("📋 Tabla de Control de Avance Físico Semanal")
        st.caption("Matriz consolidada periodo a periodo con porcentajes y estados de avance.")

        # Formatear tabla para presentación
        df_display_sem = df_semanal.copy()
        cols_pct = [
            "avance_planificado_semanal",
            "avance_real_semanal",
            "avance_planificado_acumulado",
            "avance_real_acumulado",
            "diferencia_semanal",
            "diferencia_acumulada"
        ]
        for col in cols_pct:
            if col in df_display_sem.columns:
                df_display_sem[col] = df_display_sem[col].apply(lambda x: f"{x:.2f}%")

        if "spi" in df_display_sem.columns:
            df_display_sem["spi"] = df_display_sem["spi"].apply(lambda x: f"{x:.3f}")

        nombres_columnas_es = {
            "semana": "Semana",
            "avance_planificado_semanal": "Plan Semanal (%)",
            "avance_real_semanal": "Real Semanal (%)",
            "avance_planificado_acumulado": "Plan Acumulado (%)",
            "avance_real_acumulado": "Real Acumulado (%)",
            "diferencia_semanal": "Brecha Semanal (%)",
            "diferencia_acumulada": "Brecha Acumulada (%)",
            "spi": "SPI",
            "estado_avance": "Estado de Avance"
        }
        df_display_sem = df_display_sem.rename(columns=nombres_columnas_es)

        st.dataframe(
            df_display_sem[[
                "Semana", "Plan Semanal (%)", "Real Semanal (%)",
                "Plan Acumulado (%)", "Real Acumulado (%)",
                "Brecha Acumulada (%)", "SPI", "Estado de Avance"
            ]],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("📋 Matriz Detallada por Partida")
        st.caption("Seguimiento individual de cada partida de obra con su peso y avance acumulado.")

        df_display_part = df_resumen_partidas.copy()
        df_display_part["peso_partida"] = df_display_part["peso_partida"].apply(lambda x: f"{x:.2f}%")
        df_display_part["avance_plan_total"] = df_display_part["avance_plan_total"].apply(lambda x: f"{x:.2f}%")
        df_display_part["avance_real_total"] = df_display_part["avance_real_total"].apply(lambda x: f"{x:.2f}%")
        df_display_part["diferencia"] = df_display_part["diferencia"].apply(lambda x: f"{x:+.2f}%")
        df_display_part["cumplimiento_%"] = df_display_part["cumplimiento_%"].apply(lambda x: f"{x:.1f}%")

        nombres_part_es = {
            "codigo_partida": "Código",
            "partida": "Partida",
            "especialidad": "Especialidad",
            "encargado": "Encargado",
            "peso_partida": "Peso (%)",
            "avance_plan_total": "Plan Total (%)",
            "avance_real_total": "Real Total (%)",
            "diferencia": "Brecha (%)",
            "cumplimiento_%": "Cumplimiento (%)"
        }
        df_display_part = df_display_part.rename(columns=nombres_part_es)

        st.dataframe(
            df_display_part,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------------------------
    # PESTAÑA 4: CALIDAD Y VALIDACIÓN DE DATOS (10 PUNTOS CLAVE)
    # --------------------------------------------------------------------------
    with tab_calidad:
        st.subheader("✅ Reporte de Calidad de Datos (10 Validaciones de Control)")
        st.caption("Verificación automática de consistencia matemática y estructura lógica del archivo cargado.")

        if todas_validas:
            st.success("🎉 **TODAS LAS VALIDACIONES PASARON CON ÉXITO.** La base de datos es consistente y confiable.")
        else:
            st.error("⚠️ **SE DETECTARON ADVERTENCIAS EN LOS DATOS.** Revise el detalle a continuación.")

        val_cols1, val_cols2 = st.columns(2)

        items_vals = list(validaciones_dict.items())
        mitad = len(items_vals) // 2

        with val_cols1:
            for key, vdata in items_vals[:mitad]:
                icono = "✅" if vdata["estado"] else "❌"
                color = "green" if vdata["estado"] else "red"
                with st.expander(f"{icono} {vdata['descripcion']}", expanded=True):
                    st.write(f"**Esperado:** `{vdata['esperado']}`")
                    st.write(f"**Obtenido:** `{vdata['obtenido']}`")
                    st.markdown(f"**Resultado:** :{color}[{'PASÓ' if vdata['estado'] else 'FALLÓ'}]")

        with val_cols2:
            for key, vdata in items_vals[mitad:]:
                icono = "✅" if vdata["estado"] else "❌"
                color = "green" if vdata["estado"] else "red"
                with st.expander(f"{icono} {vdata['descripcion']}", expanded=True):
                    st.write(f"**Esperado:** `{vdata['esperado']}`")
                    st.write(f"**Obtenido:** `{vdata['obtenido']}`")
                    st.markdown(f"**Resultado:** :{color}[{'PASÓ' if vdata['estado'] else 'FALLÓ'}]")

    # --------------------------------------------------------------------------
    # PESTAÑA 5: REPORTES & DESCARGAS
    # --------------------------------------------------------------------------
    with tab_descargas:
        st.subheader("📥 Centro de Descargas y Exportación de Reportes")
        st.caption("Descargue el libro de Excel oficial estructurado en 5 hojas, tablas en CSV y el paquete completo de gráficos.")

        col_d1, col_d2, col_d3 = st.columns(3)

        # 1. Reporte Excel Completo
        with col_d1:
            st.markdown("##### 📊 Reporte Oficial Excel (.xlsx)")
            st.write("Libro de cálculo multihoja corporativo con formato:")
            st.markdown("""
            - 📑 **Avance_Semanal**
            - 📑 **Avance_Especialidad**
            - 📑 **Partidas_Encargado**
            - 📑 **Avance_Encargado**
            - 📑 **Validaciones**
            """)
            bytes_excel = generar_excel_completo(
                df_semanal, df_especialidad, df_partidas_encargado,
                df_avance_encargado, validaciones_dict
            )
            st.download_button(
                label="📄 Descargar Reporte Excel Completo",
                data=bytes_excel,
                file_name="Reporte_Avance_Fisico_Obra.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_descarga_excel_oficial"
            )

        # 2. Tabla Semanal en CSV
        with col_d2:
            st.markdown("##### 📝 Datos Semanales en CSV")
            st.write("Exportación de la tabla de avance físico semanal en formato CSV delimitado por punto y coma con codificación UTF-8.")
            st.write("")
            st.write("")
            bytes_csv = generar_csv_tabla(df_semanal)
            st.download_button(
                label="📄 Descargar Tabla Semanal (CSV)",
                data=bytes_csv,
                file_name="Control_Avance_Semanal.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_descarga_csv_oficial"
            )

        # 3. Paquete ZIP con todos los gráficos Matplotlib
        with col_d3:
            st.markdown("##### 🖼️ Paquete de Gráficos (ZIP)")
            st.write("Descarga masiva de los 8 gráficos generados en alta resolución (PNG a 150 DPI) listos para informes o presentaciones.")
            st.write("")
            st.write("")
            bytes_zip = generar_zip_graficos(figuras_dict_descarga)
            st.download_button(
                label="📦 Descargar Todos los Gráficos (.ZIP)",
                data=bytes_zip,
                file_name="Graficos_Avance_Obra_PNG.zip",
                mime="application/zip",
                use_container_width=True,
                key="btn_descarga_zip_graficos"
            )

    # --------------------------------------------------------------------------
    # PIE DE PÁGINA
    # --------------------------------------------------------------------------
    st.divider()
    col_foot1, col_foot2 = st.columns([2, 1])
    with col_foot1:
        st.caption("🏗️ Sistema de Control de Avance Físico de Obra | Desarrollado con Streamlit, Matplotlib, Pandas y OpenPyXL.")
    with col_foot2:
        st.caption("© 2026 Dashboard de Ingeniería y Gestión de Proyectos.")


if __name__ == "__main__":
    main()
