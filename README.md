# 🏗️ Aplicativo Web de Análisis del Avance Físico de Obra

Un sistema web profesional interactivo desarrollado en **Python**, **Streamlit**, **Pandas** y **Plotly** para el seguimiento, control, visualización y exportación de indicadores de **Avance Físico de Obra**.

---

## 🎯 Objetivo

Proporcionar a ingenieros residentes, directores de obra y gerentes de proyecto una herramienta intuitiva y automatizada que permita:
1. Cargar archivos de control de avance de obra en formatos **CSV** o Excel (**XLSX**).
2. Calcular automáticamente avances semanales/periodicos, avances acumulados, brechas (diferencias) y estado del proyecto (**ADELANTADA**, **RETRAZADA**, **SEGÚN LO PREVISTO**).
3. Generar gráficos dinámicos interactivos (incluyendo la **Curva S**, producción semanal, brecha de avance, costos y avance real acumulado).
4. Exportar reportes tabulares y ejecutivos en Excel multi-hoja, CSV e imágenes PNG.

---

## 📁 Estructura del Proyecto

```
/app_avance_obra
│
├── app.py                      # Interfaz principal de la aplicación Streamlit
├── requirements.txt            # Dependencias del proyecto
├── README.md                   # Documentación técnica y guía de uso
│
├── modules/                    # Módulos de lógica desacoplada
│   ├── __init__.py
│   ├── carga_datos.py          # Detección, lectura y validación de archivos CSV/XLSX
│   ├── calculos.py             # Motor de cálculo con Pandas para KPIs y tablas
│   ├── graficos.py             # Generación de gráficos interactivos con Plotly
│   └── exportacion.py          # Generación de reportes Excel multihoja, CSV y PNG
│
├── data/                       # Archivos de datos sintéticos de muestra
│   ├── datos_avance_sinteticos.csv
│   └── datos_avance_con_especialidad.csv
│
└── outputs/                    # Archivos generados automáticamente
    ├── graficos/               # Exportación de imágenes PNG (ej. avance_real_acumulado.png)
    └── exportaciones/          # Descargas locales de reportes
```

---

## 🛠️ Instalación

1. **Clonar o ubicarse en el directorio del proyecto:**
   ```bash
   cd app_avance_obra
   ```

2. **(Opcional) Crear y activar un entorno virtual:**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/macOS:
   source venv/bin/activate
   ```

3. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 📚 Librerías Utilizadas

| Librería | Propósito |
| :--- | :--- |
| **Streamlit** | Framework para la interfaz web interactiva |
| **Pandas** | Procesamiento de datos y fórmulas acumuladas |
| **Plotly** | Visualizaciones gráficas interactivas |
| **OpenPyXL / XlsxWriter** | Creación y formato de hojas Excel multi-tabulares |
| **Kaleido** | Exportación estática de gráficos Plotly a imágenes PNG |

---

## 🚀 Ejecución del Aplicativo

Para iniciar la aplicación web en su navegador local, ejecute:

```bash
streamlit run app.py
```

El navegador abrirá automáticamente la aplicación en `http://localhost:8501`.

---

## 📄 Formato de Datos Requerido

El archivo de entrada (CSV o XLSX) debe contar como **mínimo** con las siguientes 4 columnas obligatorias:

| Columna Obligatoria | Tipo | Descripción |
| :--- | :--- | :--- |
| `Periodo` | Texto | Identificador del periodo (ej. "Semana 01", "Semana 02") |
| `Fecha` | Fecha/Texto | Fecha del periodo en formato `YYYY-MM-DD` |
| `Avance_Planificado_Periodo_%` | Numérico | Porcentaje planificado para dicho periodo (ej. 5.0) |
| `Avance_Real_Periodo_%` | Numérico | Porcentaje real ejecutado en el periodo (ej. 6.5) |

### Columnas Opcionales Adicionales

- **Costos:** `Costo_Planificado_USD`, `Costo_Real_USD`
- **Especialidad y Encargados:** `Especialidad`, `Encargado`, `Partida` (o `codigo_partida`).

---

## 🧮 Descripción de los Cálculos

Las funciones puras en `modules/calculos.py` realizan las siguientes operaciones:

1. **Avance planificado semanal:** Valor directo de la columna `Avance_Planificado_Periodo_%`.
2. **Avance real semanal:** Valor directo de la columna `Avance_Real_Periodo_%`.
3. **Avance planificado acumulado:** Suma acumulada (`cumsum()`) de los avances planificados.
4. **Avance real acumulado:** Suma acumulada (`cumsum()`) de los avances reales.
5. **Diferencia:** `Avance_Real_Acumulado - Avance_Planificado_Acumulado`.
6. **Variación Porcentual:** `(Diferencia / Avance_Planificado_Acumulado) * 100`.
7. **Estado de la Obra:**
   - `Diferencia > 0`: **"OBRA ADELANTADA"**
   - `Diferencia == 0`: **"OBRA SEGÚN LO PREVISTO"**
   - `Diferencia < 0`: **"OBRA RETRASADA"**

---

## 📊 Descripción de los Gráficos

Todos los gráficos se construyen con Plotly para una interactividad total:

1. **Curva S — Avance Planificado vs Avance Real:** Gráfico de líneas con marcadores comparando la trayectoria del avance acumulado planificado frente al real.
2. **Producción Semanal:** Gráfico de barras agrupadas comparando la producción individual por periodo.
3. **Diferencia entre Avance Real y Planificado:** Gráfico de barras con código de colores (verde para adelantado, rojo para retrasado).
4. **Costo Planificado vs Costo Real:** Gráfico de barras comparativo de costos en USD (habilitado si existen las columnas de costo).
5. **Análisis por Especialidad y Encargado:** Desglose por áreas de especialidad y profesionales responsables (habilitado dinámicamente si existen las columnas).
6. **Avance Real Acumulado de Obra:** Gráfico de área rellena mostrado como **gráfico final** de la aplicación.

---

## 📥 Exportaciones

El sistema permite descargar directamente:
- **Tabla a Excel (`.xlsx`):** Descarga limpia de la tabla `CONTROL DE AVANCE FÍSICO`.
- **Tabla a CSV (`.csv`):** Archivo plano codificado en UTF-8-BOM.
- **Gráfico PNG (`.png`):** Exportación en alta resolución del gráfico final.
- **Reporte Completo Excel Multi-Hoja:** Contiene las pestañas `"Resumen"`, `"Datos procesados"` e `"Indicadores"`.

---

## ⚠️ Limitaciones Actuales respecto a Especialidad y Encargado

El archivo de prueba básico (`datos_avance_sinteticos.csv`) no incluye las columnas `Especialidad`, `Encargado` ni `Partida`.

- **Comportamiento ante ausencia de columnas:** La aplicación despliega un aviso amarillo claro: *"Los análisis por especialidad y encargado requieren que el archivo contenga las columnas Especialidad y Encargado."*
- **Soporte Dinámico:** El código de la aplicación y sus módulos están 100% preparados para procesar automáticamente dichos gráficos cuando el usuario cargue un archivo que contenga esas columnas (como `datos_avance_con_especialidad.csv`).
