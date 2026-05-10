"""
Sistema de Vigilancia Epidemiológica Digital
Laboratorio Estatal de Salud Pública
Versión 1.0

Desarrollado para captura, análisis y monitoreo de casos epidemiológicos
"""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import json
from typing import List, Dict, Any
import hashlib

# ========================
# CONFIGURACIÓN INICIAL
# ========================

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Vigilancia Epidemiológica",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejor apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a8a;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f9ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #3b82f6;
    }
    .alert-box {
        background-color: #fef2f2;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #f0fdf4;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #22c55e;
        margin: 1rem 0;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ========================
# FUNCIONES DE CONEXIÓN
# ========================

@st.cache_resource
def get_google_sheets_client():
    """
    Establece conexión con Google Sheets usando credenciales de servicio
    """
    try:
        # Cargar credenciales desde Streamlit secrets
        credentials_dict = st.secrets["gcp_service_account"]
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {str(e)}")
        st.info("💡 Verifica que las credenciales estén configuradas en secrets.toml")
        return None

@st.cache_data(ttl=60)
def load_data_from_sheets(_client, spreadsheet_id: str, sheet_name: str = "Hoja 1") -> pd.DataFrame:
    """
    Carga datos desde Google Sheets con caché de 60 segundos
    """
    try:
        spreadsheet = _client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Obtener todos los valores
        data = worksheet.get_all_values()
        
        if len(data) < 1:
            return pd.DataFrame()
        
        # Crear DataFrame con la primera fila como headers
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Convertir fechas si existen columnas de fecha
        date_columns = ['Fecha de emisión', 'Fecha de inicio de síntomas', 'Fecha de recepción']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        return pd.DataFrame()

def get_sheet_columns(_client, spreadsheet_id: str, sheet_name: str = "Hoja 1") -> List[str]:
    """
    Obtiene dinámicamente las columnas del Google Sheet
    """
    try:
        spreadsheet = _client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        headers = worksheet.row_values(1)
        return headers
    except Exception as e:
        st.error(f"❌ Error al obtener columnas: {str(e)}")
        return []

def append_row_to_sheet(_client, spreadsheet_id: str, row_data: List, sheet_name: str = "Hoja 1"):
    """
    Agrega una nueva fila al Google Sheet
    """
    try:
        spreadsheet = _client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar datos: {str(e)}")
        return False

def bulk_append_to_sheet(_client, spreadsheet_id: str, data_rows: List[List], sheet_name: str = "Hoja 1"):
    """
    Agrega múltiples filas al Google Sheet
    """
    try:
        spreadsheet = _client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.append_rows(data_rows)
        return True
    except Exception as e:
        st.error(f"❌ Error al cargar datos masivos: {str(e)}")
        return False

# ========================
# FUNCIONES DE VALIDACIÓN
# ========================

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> tuple:
    """
    Valida que los campos requeridos estén completos
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == "":
            missing_fields.append(field)
    
    is_valid = len(missing_fields) == 0
    return is_valid, missing_fields

def generate_folio_sinave() -> str:
    """
    Genera un folio SINAVE único basado en timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_part = hashlib.md5(timestamp.encode()).hexdigest()[:6].upper()
    return f"SINAVE-{timestamp}-{hash_part}"

# ========================
# PÁGINA: CAPTURA INDIVIDUAL
# ========================

def page_captura_individual():
    st.markdown('<div class="main-header">📝 Captura Individual de Casos</div>', unsafe_allow_html=True)
    
    client = get_google_sheets_client()
    if not client:
        return
    
    # Obtener ID de la hoja desde configuración
    spreadsheet_id = st.secrets.get("spreadsheet_id", "")
    
    if not spreadsheet_id:
        st.warning("⚠️ Configura el ID del Google Spreadsheet en secrets.toml")
        spreadsheet_id = st.text_input("ID del Google Spreadsheet:", key="temp_spreadsheet_id")
    
    if spreadsheet_id:
        # Obtener columnas dinámicamente
        columns = get_sheet_columns(client, spreadsheet_id)
        
        if not columns:
            st.error("❌ No se pudieron cargar las columnas. Verifica el ID de la hoja.")
            return
        
        st.success(f"✅ Conectado a Google Sheets - {len(columns)} columnas detectadas")
        
        # Crear formulario dinámico
        with st.form("formulario_captura"):
            st.subheader("Información del Caso")
            
            form_data = {}
            
            # Crear campos del formulario según las columnas
            col1, col2 = st.columns(2)
            
            for idx, column in enumerate(columns):
                target_col = col1 if idx % 2 == 0 else col2
                
                with target_col:
                    # Campos especiales con validación
                    if 'fecha' in column.lower():
                        form_data[column] = st.date_input(
                            column,
                            value=datetime.now(),
                            key=f"field_{idx}"
                        )
                    elif 'resultado' in column.lower():
                        form_data[column] = st.selectbox(
                            column,
                            options=["", "Positivo", "Negativo", "Pendiente"],
                            key=f"field_{idx}"
                        )
                    elif 'diagnóstico' in column.lower() or 'diagnostico' in column.lower():
                        form_data[column] = st.selectbox(
                            column,
                            options=["", "COVID-19", "Influenza", "Dengue", "VIH", "Tuberculosis", 
                                   "Hepatitis", "Otro"],
                            key=f"field_{idx}"
                        )
                    elif 'municipio' in column.lower():
                        # Lista de municipios de Sonora (ejemplo)
                        municipios = ["", "Hermosillo", "Cajeme", "Nogales", "San Luis Río Colorado",
                                    "Navojoa", "Guaymas", "Agua Prieta", "Caborca", "Empalme",
                                    "Huatabampo", "Cananea", "Etchojoa", "Puerto Peñasco", "Otro"]
                        form_data[column] = st.selectbox(
                            column,
                            options=municipios,
                            key=f"field_{idx}"
                        )
                    elif 'folio sinave' in column.lower():
                        # Opción de generar automáticamente
                        auto_folio = st.checkbox("Generar automáticamente", key=f"auto_{idx}")
                        if auto_folio:
                            form_data[column] = generate_folio_sinave()
                            st.info(f"Folio generado: {form_data[column]}")
                        else:
                            form_data[column] = st.text_input(column, key=f"field_{idx}")
                    else:
                        form_data[column] = st.text_input(column, key=f"field_{idx}")
            
            # Botones de acción
            col_submit, col_clear = st.columns([1, 1])
            
            with col_submit:
                submitted = st.form_submit_button("💾 Guardar Caso", use_container_width=True)
            
            with col_clear:
                clear = st.form_submit_button("🗑️ Limpiar Formulario", use_container_width=True)
            
            if submitted:
                # Validar campos requeridos (ajustar según necesidad)
                required_fields = ["Nombre del paciente", "Diagnóstico", "Resultado"]
                is_valid, missing = validate_required_fields(form_data, required_fields)
                
                if is_valid:
                    # Convertir fechas a string
                    row_data = []
                    for col in columns:
                        value = form_data.get(col, "")
                        if isinstance(value, datetime):
                            value = value.strftime("%Y-%m-%d")
                        row_data.append(str(value))
                    
                    # Guardar en Google Sheets
                    if append_row_to_sheet(client, spreadsheet_id, row_data):
                        st.markdown('<div class="success-box">✅ <b>Caso guardado exitosamente</b></div>', 
                                  unsafe_allow_html=True)
                        st.balloons()
                        
                        # Limpiar caché para refrescar datos
                        st.cache_data.clear()
                else:
                    st.markdown(f'<div class="alert-box">⚠️ <b>Campos faltantes:</b> {", ".join(missing)}</div>', 
                              unsafe_allow_html=True)

# ========================
# PÁGINA: CARGA MASIVA
# ========================

def page_carga_masiva():
    st.markdown('<div class="main-header">📤 Carga Masiva de Datos</div>', unsafe_allow_html=True)
    
    client = get_google_sheets_client()
    if not client:
        return
    
    spreadsheet_id = st.secrets.get("spreadsheet_id", "")
    
    if not spreadsheet_id:
        st.warning("⚠️ Configura el ID del Google Spreadsheet en secrets.toml")
        return
    
    # Obtener columnas del sheet
    sheet_columns = get_sheet_columns(client, spreadsheet_id)
    
    st.info(f"📋 Columnas esperadas en el archivo: **{', '.join(sheet_columns)}**")
    
    # Área de carga de archivo
    uploaded_file = st.file_uploader(
        "Arrastra o selecciona un archivo Excel (.xlsx) o CSV",
        type=['xlsx', 'xls', 'csv'],
        help="El archivo debe contener las mismas columnas que el Google Sheet"
    )
    
    if uploaded_file:
        try:
            # Leer archivo según tipo
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Archivo cargado: **{uploaded_file.name}** - {len(df_upload)} registros")
            
            # Mostrar preview
            st.subheader("Vista Previa de Datos")
            st.dataframe(df_upload.head(10), use_container_width=True)
            
            # Validación de columnas
            st.subheader("Mapeo de Columnas")
            
            file_columns = df_upload.columns.tolist()
            
            # Verificar coincidencia de columnas
            matching_cols = set(file_columns) & set(sheet_columns)
            missing_cols = set(sheet_columns) - set(file_columns)
            extra_cols = set(file_columns) - set(sheet_columns)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Columnas coincidentes", len(matching_cols), delta=None)
            with col2:
                st.metric("Columnas faltantes", len(missing_cols), delta=None)
            with col3:
                st.metric("Columnas extras", len(extra_cols), delta=None)
            
            if missing_cols:
                st.warning(f"⚠️ Columnas faltantes en el archivo: {', '.join(missing_cols)}")
            
            if extra_cols:
                st.info(f"ℹ️ Columnas adicionales (serán ignoradas): {', '.join(extra_cols)}")
            
            # Mapeo manual de columnas
            st.subheader("Configurar Mapeo (Opcional)")
            
            with st.expander("🔧 Ajustar mapeo de columnas"):
                column_mapping = {}
                for sheet_col in sheet_columns:
                    mapped_col = st.selectbox(
                        f"Mapear '{sheet_col}' a:",
                        options=[""] + file_columns,
                        index=file_columns.index(sheet_col) + 1 if sheet_col in file_columns else 0,
                        key=f"map_{sheet_col}"
                    )
                    if mapped_col:
                        column_mapping[sheet_col] = mapped_col
            
            # Botón de carga
            if st.button("📤 Cargar Datos a Google Sheets", type="primary", use_container_width=True):
                with st.spinner("Procesando y cargando datos..."):
                    # Preparar datos para carga
                    rows_to_upload = []
                    
                    for _, row in df_upload.iterrows():
                        new_row = []
                        for sheet_col in sheet_columns:
                            # Usar mapeo si existe, sino usar columna directa
                            source_col = column_mapping.get(sheet_col, sheet_col)
                            
                            if source_col in df_upload.columns:
                                value = row[source_col]
                                # Convertir NaN a string vacío
                                if pd.isna(value):
                                    value = ""
                                # Convertir fechas a string
                                elif isinstance(value, (pd.Timestamp, datetime)):
                                    value = value.strftime("%Y-%m-%d")
                                new_row.append(str(value))
                            else:
                                new_row.append("")
                        
                        rows_to_upload.append(new_row)
                    
                    # Cargar a Google Sheets
                    if bulk_append_to_sheet(client, spreadsheet_id, rows_to_upload):
                        st.markdown(f'<div class="success-box">✅ <b>{len(rows_to_upload)} registros cargados exitosamente</b></div>', 
                                  unsafe_allow_html=True)
                        st.balloons()
                        st.cache_data.clear()
                    else:
                        st.error("❌ Error al cargar los datos")
        
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")

# ========================
# PÁGINA: CONSULTA EXTERNA
# ========================

def page_consulta_externa():
    st.markdown('<div class="main-header">🔍 Consulta de Resultados</div>', unsafe_allow_html=True)
    
    client = get_google_sheets_client()
    if not client:
        return
    
    spreadsheet_id = st.secrets.get("spreadsheet_id", "")
    
    if not spreadsheet_id:
        st.warning("⚠️ Configura el ID del Google Spreadsheet")
        return
    
    # Cargar datos
    df = load_data_from_sheets(client, spreadsheet_id)
    
    if df.empty:
        st.info("📭 No hay datos disponibles")
        return
    
    st.info("🔐 Portal de Consulta para Unidades Médicas")
    
    # Opciones de búsqueda
    search_type = st.radio(
        "Buscar por:",
        options=["Folio SINAVE", "Nombre del Paciente"],
        horizontal=True
    )
    
    if search_type == "Folio SINAVE":
        search_term = st.text_input("Ingrese el Folio SINAVE:", placeholder="SINAVE-20240509-XXXXX")
        search_column = "Folio SINAVE"
    else:
        search_term = st.text_input("Ingrese el Nombre del Paciente:", placeholder="Juan Pérez")
        search_column = "Nombre del paciente"
    
    if search_term:
        # Buscar en el DataFrame
        if search_column in df.columns:
            results = df[df[search_column].str.contains(search_term, case=False, na=False)]
            
            if not results.empty:
                st.success(f"✅ Se encontraron {len(results)} resultado(s)")
                
                for idx, row in results.iterrows():
                    with st.container():
                        st.markdown("---")
                        
                        # Crear tarjeta de resultado
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.subheader(f"👤 {row.get('Nombre del paciente', 'N/A')}")
                            st.write(f"**Folio SINAVE:** {row.get('Folio SINAVE', 'N/A')}")
                            st.write(f"**Diagnóstico:** {row.get('Diagnóstico', 'N/A')}")
                            st.write(f"**Unidad Médica:** {row.get('Unidad médica', 'N/A')}")
                        
                        with col2:
                            resultado = row.get('Resultado', 'Pendiente')
                            
                            if resultado == "Positivo":
                                st.markdown('<div style="background-color: #fee2e2; padding: 1rem; border-radius: 8px; text-align: center;">'
                                          '<h3 style="color: #dc2626; margin: 0;">🔴 POSITIVO</h3></div>', 
                                          unsafe_allow_html=True)
                            elif resultado == "Negativo":
                                st.markdown('<div style="background-color: #dcfce7; padding: 1rem; border-radius: 8px; text-align: center;">'
                                          '<h3 style="color: #16a34a; margin: 0;">🟢 NEGATIVO</h3></div>', 
                                          unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="background-color: #fef3c7; padding: 1rem; border-radius: 8px; text-align: center;">'
                                          '<h3 style="color: #ca8a04; margin: 0;">🟡 PENDIENTE</h3></div>', 
                                          unsafe_allow_html=True)
                        
                        # Información adicional
                        st.write(f"**Fecha de Recepción:** {row.get('Fecha de recepción', 'N/A')}")
                        st.write(f"**Fecha de Emisión:** {row.get('Fecha de emisión', 'N/A')}")
                        st.write(f"**Municipio:** {row.get('Municipio', 'N/A')}")
            else:
                st.warning("⚠️ No se encontraron resultados para la búsqueda")
        else:
            st.error(f"❌ La columna '{search_column}' no existe en los datos")

# ========================
# PÁGINA: DASHBOARD ADMIN
# ========================

def page_dashboard_admin():
    st.markdown('<div class="main-header">📊 Dashboard Epidemiológico</div>', unsafe_allow_html=True)
    
    client = get_google_sheets_client()
    if not client:
        return
    
    spreadsheet_id = st.secrets.get("spreadsheet_id", "")
    
    if not spreadsheet_id:
        st.warning("⚠️ Configura el ID del Google Spreadsheet")
        return
    
    # Cargar datos
    df = load_data_from_sheets(client, spreadsheet_id)
    
    if df.empty:
        st.info("📭 No hay datos para visualizar")
        return
    
    # Métricas principales
    st.subheader("📈 Métricas Generales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_casos = len(df)
    positivos = len(df[df['Resultado'] == 'Positivo']) if 'Resultado' in df.columns else 0
    negativos = len(df[df['Resultado'] == 'Negativo']) if 'Resultado' in df.columns else 0
    pendientes = len(df[df['Resultado'] == 'Pendiente']) if 'Resultado' in df.columns else 0
    
    with col1:
        st.metric("Total de Casos", total_casos)
    with col2:
        st.metric("Positivos", positivos, delta=f"{(positivos/total_casos*100):.1f}%" if total_casos > 0 else "0%")
    with col3:
        st.metric("Negativos", negativos)
    with col4:
        st.metric("Pendientes", pendientes)
    
    # Gráficos
    tab1, tab2, tab3 = st.tabs(["📅 Curva Temporal", "🗺️ Distribución Geográfica", "🦠 Por Diagnóstico"])
    
    with tab1:
        st.subheader("Curva de Positividad Diaria")
        
        if 'Fecha de emisión' in df.columns and 'Resultado' in df.columns:
            # Filtrar solo resultados válidos
            df_temp = df[df['Resultado'].isin(['Positivo', 'Negativo'])].copy()
            
            if not df_temp.empty and df_temp['Fecha de emisión'].notna().any():
                # Agrupar por fecha
                df_temp['Fecha'] = pd.to_datetime(df_temp['Fecha de emisión'])
                daily_data = df_temp.groupby([df_temp['Fecha'].dt.date, 'Resultado']).size().reset_index(name='Casos')
                
                # Crear gráfico
                fig = px.line(
                    daily_data,
                    x='Fecha',
                    y='Casos',
                    color='Resultado',
                    title='Casos por Día y Resultado',
                    color_discrete_map={'Positivo': '#ef4444', 'Negativo': '#22c55e'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay suficientes datos con fechas válidas")
        else:
            st.warning("Columnas de fecha o resultado no disponibles")
    
    with tab2:
        st.subheader("Distribución por Municipio")
        
        if 'Municipio' in df.columns:
            municipio_data = df['Municipio'].value_counts().reset_index()
            municipio_data.columns = ['Municipio', 'Casos']
            
            # Gráfico de barras
            fig = px.bar(
                municipio_data,
                x='Municipio',
                y='Casos',
                title='Casos por Municipio',
                color='Casos',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Mapa de calor (tabla)
            st.subheader("Mapa de Calor por Municipio y Resultado")
            
            if 'Resultado' in df.columns:
                heatmap_data = pd.crosstab(df['Municipio'], df['Resultado'])
                st.dataframe(heatmap_data, use_container_width=True)
        else:
            st.warning("Columna de Municipio no disponible")
    
    with tab3:
        st.subheader("Distribución por Diagnóstico")
        
        if 'Diagnóstico' in df.columns:
            diag_data = df['Diagnóstico'].value_counts().reset_index()
            diag_data.columns = ['Diagnóstico', 'Casos']
            
            # Gráfico de pastel
            fig = px.pie(
                diag_data,
                values='Casos',
                names='Diagnóstico',
                title='Distribución de Diagnósticos'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla detallada
            st.subheader("Resultados por Diagnóstico")
            
            if 'Resultado' in df.columns:
                detailed_data = pd.crosstab(df['Diagnóstico'], df['Resultado'])
                st.dataframe(detailed_data, use_container_width=True)
        else:
            st.warning("Columna de Diagnóstico no disponible")
    
    # Exportar datos
    st.subheader("📥 Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Exportar a CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descargar CSV",
            data=csv,
            file_name=f'vigilancia_epidemiologica_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )
    
    with col2:
        # Exportar a Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Datos')
        
        st.download_button(
            label="📊 Descargar Excel",
            data=buffer.getvalue(),
            file_name=f'vigilancia_epidemiologica_{datetime.now().strftime("%Y%m%d")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

# ========================
# NAVEGACIÓN PRINCIPAL
# ========================

def main():
    # Sidebar con navegación
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/3b82f6/ffffff?text=Logo+Salud", use_container_width=True)
        st.title("🏥 Sistema de Vigilancia")
        st.markdown("---")
        
        # Selector de página
        page = st.radio(
            "Navegación",
            options=[
                "📝 Captura Individual",
                "📤 Carga Masiva",
                "🔍 Consulta Externa",
                "📊 Dashboard Admin"
            ],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption("Versión 1.0")
        st.caption("Laboratorio Estatal de Salud Pública")
    
    # Renderizar página seleccionada
    if page == "📝 Captura Individual":
        page_captura_individual()
    elif page == "📤 Carga Masiva":
        page_carga_masiva()
    elif page == "🔍 Consulta Externa":
        page_consulta_externa()
    elif page == "📊 Dashboard Admin":
        page_dashboard_admin()

if __name__ == "__main__":
    main()
