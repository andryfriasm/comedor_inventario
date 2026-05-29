import streamlit as st
import pandas as pd
import os
import requests
import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "comedor.db"
ARCHIVO_INSUMOS = 'insumos.csv'
ARCHIVO_INVENTARIO = 'inventario.csv'
ARCHIVO_GASTOS = 'gastos.csv'
ARCHIVO_COMENSALES = 'comensales.csv'

# --------------------------------------------------------------------------
# FUNCIONES DE UTILERÍA: SEGURIDAD Y CONEXIÓN A BASE DE DATOS
# --------------------------------------------------------------------------
def verificar_credenciales(username, password_plana):
    """Verifica si el usuario existe y si el hash de su contraseña coincide en SQLite."""
    # Encriptamos la contraseña ingresada para compararla con la base de datos
    hash_ingresado = hashlib.sha256(password_plana.encode()).hexdigest()
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT rol FROM usuarios 
        WHERE username = ? AND password_hash = ? AND estado = 1;
    """, (username, hash_ingresado))
    
    resultado = cursor.fetchone()
    conexion.close()
    
    # Si encuentra un registro, regresa el Rol (Administrador, Cocina, etc.), si no, regresa None
    return resultado[0] if resultado else None

# --------------------------------------------------------------------------
# INICIALIZACIÓN DEL ESTADO DE SESIÓN (EL GUARDIÁN DE MEMORIA)
# --------------------------------------------------------------------------
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = ""
if 'rol' not in st.session_state:
    st.session_state['rol'] = ""

# ==============================================================================
# PANTALLA DE LOGIN (CONTROL DE ACCESO FORZOSO)
# ==============================================================================
if not st.session_state['autenticado']:
    st.markdown("<h2 style='text-align: center;'>🔐 Control de Acceso</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Sistema de Gestión e Inventarios - Comedor Laboral</p>", unsafe_allow_html=True)
    
    with st.form("formulario_login", clear_on_submit=False):
        usuario_input = st.text_input("Usuario de Red:")
        password_input = st.text_input("Contraseña de Seguridad:", type="password")
        boton_ingresar = st.form_submit_button("Iniciar Sesión")
        
        if boton_ingresar:
            if usuario_input.strip() == "" or password_input.strip() == "":
                st.error("❌ Por favor, llena todos los campos de credenciales.")
            else:
                # Consultamos al motor de seguridad
                rol_asignado = verificar_credenciales(usuario_input, password_input)
                
                if rol_asignado:
                    # El guardián autoriza el acceso y guarda los datos en memoria
                    st.session_state['autenticado'] = True
                    st.session_state['usuario'] = usuario_input
                    st.session_state['rol'] = rol_asignado
                    st.success(f"🔓 Acceso autorizado. Bienvenido/a, {usuario_input} ({rol_asignado}).")
                    st.rerun() # Recarga la pantalla inmediatamente para mostrar los módulos
                else:
                    st.error("❌ Credenciales inválidas o cuenta suspendida. Inténtalo de nuevo.")
    st.stop() # Detiene la renderización aquí. Nadie puede ver el software sin pasar el formulario.

# ==============================================================================
# SI EL USUARIO PASÓ EL LOGIN, SE EJECUTA EL RESTO DEL SISTEMA...
# ==============================================================================
st.sidebar.markdown(f"👤 **Usuario:** `{st.session_state['usuario']}`")
st.sidebar.markdown(f"🎖️ **Rol:** `{st.session_state['rol']}`")

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""
    st.session_state['rol'] = ""
    st.rerun()

st.sidebar.write("---")

# ==============================================================================
# 1. SECCIÓN: CONSULTAR INVENTARIO Y ALERTAS
# ==============================================================================
def consultar_inventario():
    st.header('🔍 Estado Actual del Almacén')
    if not os.path.exists(ARCHIVO_INVENTARIO):
        st.warning("El almacén está vacío. Ejecuta el simulador para inicializar el inventario.")
        return
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    if df_inventario.empty:
        st.warning("El almacén está vacío. Registra insumos primero.")
        return
    alertas_criticas = df_inventario[df_inventario['Cantidad_Disponible'] <= df_inventario['Stock_Minimo']]
    if not alertas_criticas.empty:
        st.error('⚠️ ALERTA: ¡Los siguientes insumos están en niveles críticos de escasez!')
        st.dataframe(alertas_criticas[['Nombre', 'Cantidad_Disponible', 'Stock_Minimo']])
    st.subheader('Inventario Completo')
    st.dataframe(df_inventario)

# ==============================================================================
# 2. SECCIÓN: REGISTRAR INSUMOS
# ==============================================================================
def registrar_nuevos_insumos():
    st.header('📦 Catálogo: Registrar Nuevo Insumo')
    with st.form("formulario_insumo", clear_on_submit=True):
        nombre = st.text_input('Nombre del Insumo (ej. Arroz, Pollo):')
        categoria = st.selectbox('Categoría:', ['Abarrotes', 'Carnes', 'Verduras', 'Lácteos', 'Otros'])
        unidad = st.selectbox('Unidad de Medida:', ['Kilogramos (Kg)', 'Litros (L)', 'Unidades (U)'])
        stock_minimo = st.number_input('Stock Mínimo de Alerta:', min_value=1, value=5)
        boton_guardar = st.form_submit_button('Registrar Producto')
        if boton_guardar:
            if nombre.strip() == "":
                st.error("Por favor, escribe un nombre.")
            else:
                if not os.path.exists(ARCHIVO_INSUMOS):
                    pd.DataFrame(columns=['ID', 'Nombre', 'Categoria', 'Unidad']).to_csv(ARCHIVO_INSUMOS, index=False)
                if not os.path.exists(ARCHIVO_INVENTARIO):
                    pd.DataFrame(columns=['ID', 'Nombre', 'Cantidad_Disponible', 'Stock_Minimo']).to_csv(ARCHIVO_INVENTARIO, index=False)
                df_insumos = pd.read_csv(ARCHIVO_INSUMOS)
                nuevo_id = len(df_insumos) + 1
                df_insumos = pd.concat([df_insumos, pd.DataFrame([[nuevo_id, nombre, categoria, unidad]], columns=df_insumos.columns)], ignore_index=True)
                df_insumos.to_csv(ARCHIVO_INSUMOS, index=False)
                df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
                df_inventario = pd.concat([df_inventario, pd.DataFrame([[nuevo_id, nombre, 0.0, stock_minimo]], columns=df_inventario.columns)], ignore_index=True)
                df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                st.success(f"¡'{nombre}' agregado con éxito!")

# ==============================================================================
# 3. SECCIÓN: REGISTRAR ENTRADAS (COMPRAS)
# ==============================================================================
def registrar_entradas_y_gastos():
    st.header('📥 Entrada de Almacén y Registro de Gasto')
    if not os.path.exists(ARCHIVO_INVENTARIO):
        st.error("No hay insumos en el sistema.")
        return
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    if df_inventario.empty:
        st.error("No hay insumos en el sistema.")
        return
    with st.form("formulario_entrada"):
        insumo_seleccionado = st.selectbox('Selecciona el Insumo:', df_inventario['Nombre'].tolist())
        cantidad = st.number_input('Cantidad que Ingresa:', min_value=0.1, step=0.1)
        costo_total = st.number_input('Costo Total ($):', min_value=0.0, step=1.0)
        fecha_entrada = st.date_input('Fecha:', datetime.now())
        boton_entrada = st.form_submit_button('Guardar Entrada y Gasto')
        if boton_entrada:
            if not os.path.exists(ARCHIVO_GASTOS):
                pd.DataFrame(columns=['Fecha', 'Insumo', 'Monto', 'Cantidad']).to_csv(ARCHIVO_GASTOS, index=False)
            df_inventario.loc[df_inventario['Nombre'] == insumo_seleccionado, 'Cantidad_Disponible'] += cantidad
            df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
            df_gastos = pd.read_csv(ARCHIVO_GASTOS)
            df_gastos = pd.concat([df_gastos, pd.DataFrame([[fecha_entrada, insumo_seleccionado, costo_total, cantidad]], columns=df_gastos.columns)], ignore_index=True)
            df_gastos.to_csv(ARCHIVO_GASTOS, index=False)
            st.success("Entrada registrada exitosamente.")

# ==============================================================================
# 4. SECCIÓN: REGISTRAR SALIDAS (COCINA)
# ==============================================================================
def registrar_salidas_cocina():
    st.header('📤 Salida de Insumos hacia la Cocina')
    if not os.path.exists(ARCHIVO_INVENTARIO):
        st.error("No hay insumos en el almacén.")
        return
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    if df_inventario.empty:
        st.error("No hay insumos en el almacén.")
        return
    with st.form("formulario_salida"):
        insumo_seleccionado = st.selectbox('Insumo solicitado por Cocina:', df_inventario['Nombre'].tolist())
        cantidad_solicitada = st.number_input('Cantidad a Entregar:', min_value=0.1, step=0.1)
        boton_salida = st.form_submit_button('Confirmar Envío a Cocina')
        if boton_salida:
            stock_actual = df_inventario.loc[df_inventario['Nombre'] == insumo_seleccionado, 'Cantidad_Disponible'].values[0]
            if cantidad_solicitada > stock_actual:
                st.error(f"❌ Error: Solo quedan {stock_actual} unidades disponibles.")
            else:
                df_inventario.loc[df_inventario['Nombre'] == insumo_seleccionado, 'Cantidad_Disponible'] -= cantidad_solicitada
                df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                st.success(f"Entregados {cantidad_solicitada} unidades a la cocina.")

# ==============================================================================
# 5. SECCIÓN: REPORTES ANALÍTICOS DE LA SIMULACIÓN (60 DÍAS)
# ==============================================================================
def reportes_basicos():
    st.header('📊 Reporte Analítico de la Simulación Macro')
    if not os.path.exists('consumo_diario.csv') or not os.path.exists('salidas.csv'):
        st.warning("No hay datos históricos de 60 días generados. Revisa tu carpeta.")
        return
    df_consumo = pd.read_csv('consumo_diario.csv')
    df_salidas = pd.read_csv('salidas.csv')
    costo_total_historico = df_consumo['costo_total_dia'].sum()
    asistencia_media = df_consumo['asistencia_total'].mean()
    col1, col2 = st.columns(2)
    col1.metric(label="Inversión Total en Alimentos (Histórico)", value=f"${costo_total_historico:,.2f} MXN")
    col2.metric(label="Promedio de Asistencia Diaria", value=f"{int(asistencia_media)} comensales")
    st.subheader("📈 Fluctuación Estocástica de la Asistencia")
    st.line_chart(df_consumo.set_index('fecha')['asistencia_total'])
    st.write('---')
    st.subheader("🗑️ Auditoría de Mermas Operativas")
    mermas_agrupadas = df_salidas.groupby('ingrediente')[['cantidad_neta_consumida_kg', 'cantidad_merma_kg']].sum()
    st.bar_chart(mermas_agrupadas)

# ==============================================================================
# 6. SECCIÓN: CONTROL DE ASISTENCIA (INTEGRACIÓN TELEGRAM REAL)
# ==============================================================================
def control_asistencia_telegram():
    st.header('📱 Interfaz de Comunicación: Bot de Telegram')
    st.subheader("🔑 Credenciales de Red Seguras")
    token_ingresado = st.text_input("Token API de Telegram:", type="password")
    
    if st.button('🚀 Desplegar Notificaciones Push'):
        if not token_ingresado:
            st.error("❌ Error: Se requiere un Token API.")
        elif not os.path.exists(ARCHIVO_COMENSALES):
            st.error("❌ Error: No se detectó el archivo maestro comensales.csv.")
        else:
            with st.spinner('Transmitiendo paquetes...'):
                try:
                    df_comensales = pd.read_csv(ARCHIVO_COMENSALES)
                    usuarios_validos = df_comensales[df_comensales['chat_id'] > 0]
                    if usuarios_validos.empty:
                        st.warning("⚠️ Alerta: No se encontraron usuarios enlazados.")
                    else:
                        conteo = 0
                        for idx, comensal in usuarios_validos.iterrows():
                            chat_id = int(comensal['chat_id'])
                            nombre = comensal['nombre_completo']
                            url = f"https://api.telegram.org/bot{token_ingresado}/sendMessage"
                            texto = f"🔔 *ALERTA DE COMEDOR* 🔔\n\nHola *{nombre}*,\nConfirma tu asistencia respondiendo a este chat. 🍳"
                            payload = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"}
                            respuesta = requests.post(url, data=payload).json()
                            if respuesta.get("ok"):
                                conteo += 1
                        if conteo > 0:
                            st.success(f"📱 Transmisión exitosa a {conteo} terminal móvil.")
                except Exception as e:
                    st.error(f"❌ Error de red: {e}")
    if os.path.exists(ARCHIVO_COMENSALES):
        st.dataframe(pd.read_csv(ARCHIVO_COMENSALES))

# ==============================================================================
# CONTROL DE PERMISOS DINÁMICOS POR ROL (LA MATRIZ DE SEGURIDAD)
# ==============================================================================
rol_actual = st.session_state['rol']

# Creamos la lista de opciones del menú según el rol que tenga la sesión
opciones_menu = []

if rol_actual == 'Administrador':
    opciones_menu = [
        'Consultar Inventario y Alertas',
        'Registrar Nuevos Insumos',
        'Registrar Entradas (Compras)',
        'Registrar Salidas (Cocina)',
        'Reportes y Gastos',
        'Control de Asistencia (Bot Telegram)'
    ]
elif rol_actual == 'Despensero':
    # El Despensero solo puede ver inventario e ingresar mercadería
    opciones_menu = [
        'Consultar Inventario y Alertas',
        'Registrar Nuevos Insumos',
        'Registrar Entradas (Compras)'
    ]
elif rol_actual == 'Cocina':
    # El rol cocina solo ve stock y extrae consumos
    opciones_menu = [
        'Consultar Inventario y Alertas',
        'Registrar Salidas (Cocina)'
    ]
elif rol_actual == 'Supervisor':
    # El supervisor monitorea almacén, reportes y el canal de comunicación
    opciones_menu = [
        'Consultar Inventario y Alertas',
        'Reportes y Gastos',
        'Control de Asistencia (Bot Telegram)'
    ]

# Renderizar el menú lateral con las opciones personalizadas de seguridad
st.sidebar.title('🧭 Menú Operativo')
opcion = st.sidebar.radio('Ir a la sección:', opciones_menu)

# Redirección de funciones
if opcion == 'Consultar Inventario y Alertas':
    consultar_inventario()
elif opcion == 'Registrar Nuevos Insumos':
    registrar_nuevos_insumos()
elif opcion == 'Registrar Entradas (Compras)':
    registrar_entradas_y_gastos()
elif opcion == 'Registrar Salidas (Cocina)':
    registrar_salidas_cocina()
elif opcion == 'Reportes y Gastos':
    reportes_basicos()
elif opcion == 'Control de Asistencia (Bot Telegram)':
    control_asistencia_telegram()