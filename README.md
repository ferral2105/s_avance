# 🏗️ Sistema de Control y Seguimiento de Avance Físico de Obra

Aplicación web interactiva desarrollada con **Streamlit**, **Matplotlib**, **Pandas** y **OpenPyXL** para el análisis, visualización y exportación de datos de avance de obras civiles y proyectos de ingeniería.

---

## 📁 Arquitectura Modular del Proyecto

La aplicación se encuentra en la raíz del proyecto dentro del directorio `app_avance_obra/` con una estricta separación de responsabilidades:

```text
trabajo python 2/
├── app_avance_obra/
│   ├── app.py                     # Interfaz web principal con Streamlit (diagramación, tabs, sidebar y KPIs)
│   ├── modules/
│   │   ├── __init__.py            # Inicializador del paquete
│   │   ├── calculos.py            # Lógica matemática, acumulados con Pandas, KPIs y 10 validaciones
│   │   ├── graficos.py            # Generación de gráficos exclusivamente con Matplotlib (alta resolución)
│   │   ├── carga_datos.py         # Detección inteligente de delimitadores (',', ';') y carga de CSV/Excel
│   │   └── exportacion.py         # Reporte corporativo Excel multi-hoja, CSV y descarga de gráficos en ZIP
│   ├── data/                      # Datasets de ejemplo y respaldo
│   │   ├── base_datos_avance_obra_12_semanas.csv
│   │   └── base_datos_avance_obra_12_semanas2222.csv
│   └── requirements.txt           # Dependencias requeridas del proyecto
├── base_datos_avance_obra_12_semanas.csv
└── base_datos_avance_obra_12_semanas2222.csv
```

---

## 🚀 Características Principales

1. **Carga Inteligente de Archivos:**
   - Permite arrastrar y soltar cualquier archivo **CSV** o **Excel (.xlsx)**.
   - Detecta automáticamente delimitadores por coma (`,`) o punto y coma (`;`), y codificaciones UTF-8 / Latin-1.
   - Menú de selección rápida para archivos existentes en el proyecto.

2. **Diagramación Estructurada y Sidebar Lateral:**
   - **Barra Lateral (`st.sidebar`)**: Carga de datos, filtros interactivos por rango de semanas, especialidad y encargado, más resumen rápido de estado.
   - **Indicadores Clave (KPIs)**: Tarjetas con Avance Planificado Acumulado, Avance Real Acumulado, Diferencia / Brecha, Índice de Desempeño (SPI) y Cumplimiento Global.
   - **Badge de Estado**: Notificación visual del estado de la obra (**ADELANTADA**, **SEGÚN PLAN**, **RETRASADA**).

3. **Gráficos Profesionales con Matplotlib:**
   - 📈 **Curva S**: Planificado vs Real con sombreado de desvíos (verde para adelanto, rojo para retraso) y etiquetas de hitos.
   - 📊 **Producción Semanal**: Barras agrupadas por semana con valores porcentuales sobre cada barra.
   - ⚖️ **Brecha y Desviación**: Gráfico de barras divergentes para brecha acumulada y semanal.
   - 🌊 **Avance Real Acumulado**: Gráfico de área que muestra el progreso consolidado.
   - 🏛️ **Avance por Especialidad**: Barras ordenadas comparando plan vs real.
   - 🍩 **Distribución por Especialidad**: Gráfico de dona (Donut chart) con porcentajes de peso ponderado.
   - 👷 **Partidas por Encargado**: Distribución de tareas por profesional.
   - 🎯 **Avance por Encargado**: Comparativa de cumplimiento por responsable.

4. **Centro de Reportes y Exportación:**
   - 📄 Descarga individual de cada gráfico en formato **PNG** (150 DPI).
   - 📦 Descarga en lote de todos los gráficos en un archivo comprimido **.ZIP**.
   - 📊 Reporte oficial completo en **Excel (.xlsx)** estructurado en 5 hojas con estilos corporativos:
     1. `Avance_Semanal`
     2. `Avance_Especialidad`
     3. `Partidas_Encargado`
     4. `Avance_Encargado`
     5. `Validaciones`
   - 📝 Descarga de la tabla consolidada en **CSV** (UTF-8 con BOM).

---

## ⚙️ Cómo Ejecutar la Aplicación

Para iniciar el servidor de Streamlit desde la terminal en la raíz del proyecto:

```bash
streamlit run app_avance_obra\app.py
```

La aplicación abrirá automáticamente una pestaña en su navegador en `http://localhost:8501` (o el puerto disponible).
