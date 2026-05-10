# 🏥 Sistema de Vigilancia Epidemiológica Digital
## Manual de Implementación Completo

---

## 📋 Tabla de Contenidos

1. [Descripción General](#descripción-general)
2. [Requisitos Previos](#requisitos-previos)
3. [Configuración de Google Sheets](#configuración-de-google-sheets)
4. [Configuración de Google Cloud Platform](#configuración-de-google-cloud-platform)
5. [Configuración del Sistema de Alertas](#configuración-del-sistema-de-alertas)
6. [Instalación de la Aplicación Streamlit](#instalación-de-la-aplicación-streamlit)
7. [Despliegue en Streamlit Cloud (GRATIS)](#despliegue-en-streamlit-cloud)
8. [Uso del Sistema](#uso-del-sistema)
9. [Solución de Problemas](#solución-de-problemas)
10. [Mantenimiento](#mantenimiento)

---

## 📖 Descripción General

Este sistema proporciona una solución completa para la vigilancia epidemiológica con:

- ✅ **Captura individual** con validación de datos
- ✅ **Carga masiva** de archivos Excel/CSV
- ✅ **Alertas automáticas** por correo electrónico
- ✅ **Dashboard** con gráficos epidemiológicos
- ✅ **Consulta externa** para unidades médicas
- ✅ **Flexibilidad total** en columnas dinámicas

### Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                   USUARIOS                               │
│  (Laboratorio, Unidades Médicas, Autoridades)           │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           APLICACIÓN WEB (Streamlit)                     │
│  • Captura Individual  • Carga Masiva                    │
│  • Consulta Externa    • Dashboard Admin                │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              GOOGLE SHEETS (Base de Datos)               │
│  • Almacenamiento dinámico de casos                      │
│  • Columnas flexibles                                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         GOOGLE APPS SCRIPT (Automatización)              │
│  • Detección automática de casos positivos              │
│  • Envío de alertas por email                            │
│  • Reportes semanales programados                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Requisitos Previos

### Cuentas Necesarias

1. **Cuenta de Google** (Gmail/Google Workspace)
2. **Cuenta de GitHub** (para despliegue gratuito)
3. **Navegador web moderno** (Chrome, Firefox, Edge)

### Conocimientos Recomendados

- ✅ Uso básico de Google Sheets
- ✅ Navegación por interfaces web
- ⚠️ NO se requiere programación (todo está automatizado)

---

## 📊 PASO 1: Configuración de Google Sheets

### 1.1 Crear la Hoja de Cálculo

1. Ve a [Google Sheets](https://sheets.google.com)
2. Clic en **+ Blank** (Nueva hoja en blanco)
3. Nombra la hoja: `Vigilancia Epidemiológica`

### 1.2 Configurar las Columnas

En la **primera fila** (fila de encabezados), escribe exactamente estas columnas:

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Nombre del paciente | Clave de laboratorio | Folio SINAVE | Diagnóstico | Resultado | Fecha de emisión | Fecha de inicio de síntomas | Municipio | Unidad médica | Fecha de recepción |

**⚠️ IMPORTANTE:** Respeta mayúsculas, minúsculas y acentos exactamente como aparecen arriba.

### 1.3 Formato Recomendado

- Fila 1: **Negrita** y con **color de fondo** (azul claro)
- Columnas de fecha: Formato → Fecha
- Columna Resultado: Validación de datos (Positivo, Negativo, Pendiente)

### 1.4 Obtener el ID de la Hoja

1. En la URL de tu hoja, copia la parte que dice `d/XXXXXXXXXXXXXXX/`
2. Ejemplo: `https://docs.google.com/spreadsheets/d/1A2B3C4D5E6F7G8H9I0/edit`
3. El ID es: `1A2B3C4D5E6F7G8H9I0`
4. **Guarda este ID** (lo necesitarás más tarde)

---

## ☁️ PASO 2: Configuración de Google Cloud Platform

### 2.1 Crear un Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Clic en **Select a project** → **New Project**
3. Nombre del proyecto: `Vigilancia Epidemiológica`
4. Clic en **CREATE**

### 2.2 Habilitar las APIs Necesarias

1. En el menú lateral, ve a **APIs & Services** → **Library**
2. Busca y habilita las siguientes APIs:
   - ✅ **Google Sheets API**
   - ✅ **Google Drive API**

**Cómo habilitar cada API:**
- Busca el nombre en la barra de búsqueda
- Clic en la API
- Clic en **ENABLE**
- Espera unos segundos

### 2.3 Crear Credenciales de Cuenta de Servicio

1. Ve a **APIs & Services** → **Credentials**
2. Clic en **+ CREATE CREDENTIALS** → **Service Account**
3. Configura así:
   - **Service account name:** `vigilancia-app`
   - **Service account ID:** `vigilancia-app` (se autocompletará)
   - Clic en **CREATE AND CONTINUE**
4. En **Grant this service account access**:
   - Role: **Editor**
   - Clic en **CONTINUE**
5. Clic en **DONE**

### 2.4 Descargar el Archivo de Credenciales JSON

1. En la lista de Service Accounts, busca `vigilancia-app@...`
2. Clic en los **3 puntos** → **Manage keys**
3. Clic en **ADD KEY** → **Create new key**
4. Tipo: **JSON**
5. Clic en **CREATE**
6. Se descargará un archivo `.json` → **GUÁRDALO EN LUGAR SEGURO**

### 2.5 Compartir la Hoja con la Cuenta de Servicio

1. Abre el archivo JSON que descargaste
2. Busca el campo `"client_email"` (algo como `vigilancia-app@proyecto.iam.gserviceaccount.com`)
3. **COPIA ese correo**
4. Ve a tu Google Sheet
5. Clic en **Share** (Compartir)
6. Pega el correo de la cuenta de servicio
7. Rol: **Editor**
8. **IMPORTANTE:** Desmarca "Notify people" (no enviar notificación)
9. Clic en **Share**

---

## 📧 PASO 3: Configuración del Sistema de Alertas

### 3.1 Abrir el Editor de Scripts

1. En tu Google Sheet, ve a **Extensions** (Extensiones) → **Apps Script**
2. Se abrirá una nueva pestaña con el editor

### 3.2 Pegar el Código de Alertas

1. Borra todo el código que aparece por defecto (`function myFunction() { ... }`)
2. Abre el archivo `google_apps_script.js` que te proporcioné
3. **Copia TODO el contenido**
4. **Pega** en el editor de Apps Script

### 3.3 Configurar los Correos Destinatarios

En la sección `CONFIG` del script (líneas 18-39), modifica:

```javascript
emailDestinatarios: [
  'tu-correo@salud.gob.mx',           // ← Cambia esto
  'epidemiologia@salud.gob.mx',       // ← Cambia esto
  'director@salud.gob.mx'             // ← Cambia esto
],
```

### 3.4 Ajustar Índices de Columnas (IMPORTANTE)

Si tus columnas están en orden diferente, actualiza los números:

```javascript
columnas: {
  nombrePaciente: 1,    // A = 1
  claveLaboratorio: 2,  // B = 2
  folioSINAVE: 3,       // C = 3
  diagnostico: 4,       // D = 4
  resultado: 5,         // E = 5
  // etc...
}
```

**Regla:** A=1, B=2, C=3, D=4, E=5, F=6, G=7, H=8, I=9, J=10

### 3.5 Guardar el Script

1. Clic en **💾 Save** (Guardar)
2. Nombre del proyecto: `Alertas Epidemiológicas`
3. Clic en **OK**

### 3.6 Autorizar el Script

1. Clic en **▶️ Run** (Ejecutar) → Selecciona `probarAlerta`
2. Aparecerá: "Authorization required"
3. Clic en **Review permissions**
4. Selecciona tu cuenta de Google
5. Aparecerá "This app isn't verified"
   - Clic en **Advanced**
   - Clic en **Go to Alertas Epidemiológicas (unsafe)**
6. Clic en **Allow**

### 3.7 Crear el Activador Automático

1. En el editor de Apps Script, clic en el **⏰ ícono de reloj** (Triggers/Activadores)
2. Clic en **+ Add Trigger**
3. Configura así:
   - Choose which function to run: **onEdit**
   - Choose which deployment: **Head**
   - Select event source: **From spreadsheet**
   - Select event type: **On edit**
4. Clic en **Save**

### 3.8 Probar el Sistema de Alertas

1. Ve a tu Google Sheet
2. En la fila 2, ingresa datos de prueba
3. En la columna **Resultado**, escribe `Positivo`
4. **Presiona Enter**
5. En 1-2 minutos, deberías recibir un correo de alerta
6. ✅ Si llega el correo, el sistema funciona correctamente

---

## 💻 PASO 4: Instalación de la Aplicación Streamlit

### 4.1 Preparar los Archivos

Descarga estos 3 archivos que te proporcioné:
1. `vigilancia_epidemiologica.py`
2. `requirements.txt`
3. `README.md` (este documento)

### 4.2 Crear la Estructura de Archivos

Crea una carpeta en tu computadora llamada `vigilancia-app` y coloca los archivos así:

```
vigilancia-app/
├── vigilancia_epidemiologica.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml
```

### 4.3 Crear el Archivo secrets.toml

1. Dentro de `vigilancia-app`, crea una carpeta llamada `.streamlit`
2. Dentro de `.streamlit`, crea un archivo llamado `secrets.toml`
3. Abre el archivo JSON de credenciales que descargaste en el Paso 2.4
4. Copia su contenido
5. En `secrets.toml`, escribe:

```toml
spreadsheet_id = "TU_ID_DE_GOOGLE_SHEET_AQUI"

[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto-id"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nXXXXX..."
client_email = "vigilancia-app@tu-proyecto.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

**⚠️ IMPORTANTE:** 
- Reemplaza `spreadsheet_id` con el ID que obtuviste en el Paso 1.4
- Copia EXACTAMENTE todos los campos del JSON a `gcp_service_account`
- El archivo `private_key` debe mantener los saltos de línea `\n`

### 4.4 Probar Localmente (Opcional)

Si tienes Python instalado:

```bash
cd vigilancia-app
pip install -r requirements.txt
streamlit run vigilancia_epidemiologica.py
```

---

## 🚀 PASO 5: Despliegue en Streamlit Cloud (GRATIS)

### 5.1 Crear una Cuenta en GitHub

1. Ve a [github.com](https://github.com)
2. Clic en **Sign up**
3. Completa el registro

### 5.2 Crear un Repositorio

1. Clic en **+** → **New repository**
2. Repository name: `vigilancia-epidemiologica`
3. **Public** (debe ser público para plan gratuito)
4. Clic en **Create repository**

### 5.3 Subir los Archivos

**Opción A: Interfaz web (más fácil)**

1. Clic en **uploading an existing file**
2. Arrastra estos archivos:
   - `vigilancia_epidemiologica.py`
   - `requirements.txt`
   - `README.md`
3. Clic en **Commit changes**

**⚠️ NO SUBAS** el archivo `secrets.toml` (contiene credenciales sensibles)

### 5.4 Configurar Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Clic en **Sign in with GitHub**
3. Autoriza Streamlit
4. Clic en **New app**
5. Configura:
   - **Repository:** `tu-usuario/vigilancia-epidemiologica`
   - **Branch:** `main`
   - **Main file path:** `vigilancia_epidemiologica.py`
6. Clic en **Advanced settings**
7. En **Secrets**, pega el contenido de tu `secrets.toml` LOCAL
8. Clic en **Deploy!**

### 5.5 Esperar el Despliegue

- Tarda 3-5 minutos
- Verás logs en tiempo real
- Cuando termine, aparecerá tu app funcionando

### 5.6 Obtener la URL

Tu app estará en:
```
https://tu-usuario-vigilancia-epidemiologica-xxx.streamlit.app
```

**🎉 ¡LISTO! Tu sistema está desplegado y funcionando.**

---

## 📖 Uso del Sistema

### Para el Personal del Laboratorio

#### Captura Individual
1. Selecciona **📝 Captura Individual**
2. Llena el formulario
3. Clic en **💾 Guardar Caso**
4. Los datos se guardan automáticamente en Google Sheets

#### Carga Masiva
1. Selecciona **📤 Carga Masiva**
2. Arrastra un archivo Excel/CSV
3. Verifica el mapeo de columnas
4. Clic en **📤 Cargar Datos**

### Para Unidades Médicas

1. Selecciona **🔍 Consulta Externa**
2. Busca por Folio SINAVE o Nombre
3. Ve el estado del resultado

### Para Administradores

1. Selecciona **📊 Dashboard Admin**
2. Visualiza:
   - Métricas generales
   - Curva de positividad
   - Distribución geográfica
   - Casos por diagnóstico
3. Exporta datos en CSV o Excel

---

## 🔧 Solución de Problemas

### Error: "No se puede conectar con Google Sheets"

**Solución:**
1. Verifica que el `spreadsheet_id` en `secrets.toml` sea correcto
2. Confirma que compartiste la hoja con el correo de la cuenta de servicio
3. Verifica que las APIs estén habilitadas en Google Cloud

### Las alertas no se envían

**Solución:**
1. Ve al Apps Script → View → Executions
2. Busca errores
3. Verifica que el trigger esté creado correctamente
4. Confirma que los correos en `CONFIG` sean válidos

### Columnas no aparecen en la interfaz

**Solución:**
1. Verifica que los nombres de las columnas en Google Sheets sean exactos
2. Borra el caché: Settings → Clear cache en Streamlit Cloud
3. Reinicia la app

### Error al cargar archivo Excel

**Solución:**
1. Asegúrate de que el archivo sea .xlsx o .csv
2. Verifica que las columnas coincidan con las del Google Sheet
3. Revisa que no haya celdas combinadas en el Excel

---

## 🛠️ Mantenimiento

### Agregar Nuevas Columnas

1. En Google Sheets, agrega la columna en la fila 1
2. La interfaz la detectará automáticamente en el próximo refresh
3. **NO necesitas modificar código**

### Actualizar Municipios o Diagnósticos

Edita el archivo `vigilancia_epidemiologica.py`:

```python
# Línea ~230 (aproximadamente)
municipios = ["", "Hermosillo", "Cajeme", "TU_NUEVO_MUNICIPIO", ...]

# Línea ~220 (aproximadamente)
options=["", "COVID-19", "Influenza", "TU_NUEVO_DIAGNOSTICO", ...]
```

### Cambiar Correos de Alerta

En Google Apps Script, edita el `CONFIG`:

```javascript
emailDestinatarios: [
  'nuevo-correo@salud.gob.mx'
],
```

### Backup de Datos

**Automático:** Google Sheets tiene historial de versiones

**Manual:**
1. Ve al Dashboard Admin
2. Clic en **📥 Descargar Excel**
3. Guarda el archivo en tu computadora

---

## 📞 Soporte

### Recursos Adicionales

- [Documentación de Streamlit](https://docs.streamlit.io)
- [Documentación de Google Sheets API](https://developers.google.com/sheets/api)
- [Apps Script Reference](https://developers.google.com/apps-script/reference)

### Modificaciones Futuras

El sistema está diseñado para ser flexible. Puedes:
- Agregar más visualizaciones en el dashboard
- Crear reportes personalizados
- Integrar con otros sistemas
- Agregar autenticación de usuarios

---

## 📄 Licencia y Créditos

Sistema desarrollado para Laboratorios Estatales de Salud Pública

**Versión:** 1.0
**Fecha:** Mayo 2024

---

## ✅ Checklist de Implementación

Usa esta lista para verificar que completaste todos los pasos:

- [ ] Google Sheet creado con columnas correctas
- [ ] ID del Google Sheet obtenido
- [ ] Proyecto en Google Cloud creado
- [ ] Google Sheets API habilitada
- [ ] Google Drive API habilitada
- [ ] Cuenta de servicio creada
- [ ] Archivo JSON de credenciales descargado
- [ ] Google Sheet compartido con cuenta de servicio
- [ ] Google Apps Script pegado y configurado
- [ ] Correos de alerta configurados
- [ ] Trigger de Apps Script creado
- [ ] Alerta de prueba recibida exitosamente
- [ ] Repositorio GitHub creado
- [ ] Archivos subidos a GitHub (sin secrets.toml)
- [ ] App desplegada en Streamlit Cloud
- [ ] Secrets configurados en Streamlit Cloud
- [ ] App funcionando correctamente
- [ ] Prueba de captura individual exitosa
- [ ] Prueba de carga masiva exitosa
- [ ] Dashboard mostrando datos correctamente

---

**¡Felicidades! Tu Sistema de Vigilancia Epidemiológica Digital está listo para usarse. 🎉**
