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
CARPETA_COMPROBANTES = os.path.join("assets", "comprobantes")

if not os.path.exists(CARPETA_COMPROBANTES):
    os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)

# --------------------------------------------------------------------------
# FUNCIONES DE UTILERÍA: SEGURIDAD, CONEXIÓN A BASE DE DATOS Y BITÁCORA
# --------------------------------------------------------------------------
def verificar_credenciales(username, password_plana):
    hash_ingresado = hashlib.sha256(password_plana.encode()).hexdigest()
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT id_usuario, rol FROM usuarios 
        WHERE username = ? AND password_hash = ? AND estado = 1;
    """, (username, hash_ingresado))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado if resultado else None

def registrar_actividad_bitacora(modulo, accion, descripcion):
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        id_usuario = st.session_state.get('id_usuario', None)
        cursor.execute("""
            INSERT INTO bitacora_actividades (id_usuario, modulo, accion, descripcion)
            VALUES (?, ?, ?, ?);
        """, (id_usuario, modulo, accion, descripcion))
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"⚠️ Error crítico en bitácora: {e}")

# --------------------------------------------------------------------------
# INICIALIZACIÓN DEL ESTADO DE SESIÓN (EL GUARDIÁN DE MEMORIA)
# --------------------------------------------------------------------------
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = ""
if 'id_usuario' not in st.session_state:
    st.session_state['id_usuario'] = None
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
                datos_usuario = verificar_credenciales(usuario_input, password_input)
                if datos_usuario:
                    st.session_state['autenticado'] = True
                    st.session_state['id_usuario'] = datos_usuario[0]
                    st.session_state['usuario'] = usuario_input
                    st.session_state['rol'] = datos_usuario[1]
                    registrar_actividad_bitacora("Autenticación", "Inicio de Sesión", f"El usuario {usuario_input} ingresó con éxito al sistema.")
                    st.success(f"🔓 Acceso autorizado. Bienvenido/a, {usuario_input} ({datos_usuario[1]}).")
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas o cuenta suspendida. Inténtalo de nuevo.")
    st.stop()

st.sidebar.markdown(f"👤 **Usuario:** `{st.session_state['usuario']}`")
st.sidebar.markdown(f"🎖️ **Rol:** `{st.session_state['rol']}`")

if st.sidebar.button("🚪 Cerrar Sesión"):
    registrar_actividad_bitacora("Autenticación", "Cierre de Sesión", f"El usuario {st.session_state['usuario']} cerró su sesión.")
    st.session_state['autenticado'] = False
    st.session_state['usuario'] = ""
    st.session_state['id_usuario'] = None
    st.session_state['rol'] = ""
    st.rerun()

st.sidebar.write("---")

# ==============================================================================
# MÓDULOS OPERATIVOS DEL COMEDOR
# ==============================================================================
def consultar_inventario():
    st.header('🔍 Estado Actual del Almacén')
    if not os.path.exists(ARCHIVO_INVENTARIO):
        st.warning("El almacén está vacío.")
        return
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    if df_inventario.empty:
        st.warning("El almacén está vacío.")
        return
    alertas_criticas = df_inventario[df_inventario['Cantidad_Disponible'] <= df_inventario['Stock_Minimo']]
    if not alertas_criticas.empty:
        st.error('⚠️ ALERTA: ¡Los siguientes insumos están en niveles críticos de escasez!')
        st.dataframe(alertas_criticas[['Nombre', 'Cantidad_Disponible', 'Stock_Minimo']])
    st.subheader('Inventario Completo')
    st.dataframe(df_inventario)

def registrar_nuevos_insumos():
    st.header('📦 Catálogo: Registrar Nuevo Insumo')
    with st.form("formulario_insumo", clear_on_submit=True):
        nombre = st.text_input('Nombre del Insumo (ej. Arroz, Gas, Jabón):')
        categoria = st.selectbox('Categoría:', ['Abarrotes', 'Carnes', 'Verduras', 'Lácteos', 'Recursos Operativos', 'Otros'])
        unidad = st.selectbox('Unidad de Medida:', ['Kilogramos (Kg)', 'Litros (L)', 'Unidades (U)', 'Tanques / Litros Gas'])
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
                registrar_actividad_bitacora("Inventario", "Alta de Insumo", f"Se catalogó el producto nuevo '{nombre}' (ID: {nuevo_id}) en categoría [{categoria}].")
                st.success(f"¡'{nombre}' agregado con éxito!")

def registrar_entradas_y_gastos():
    st.header('📥 Entrada de Almacén y Evidencia Digital')
    if not os.path.exists(ARCHIVO_INVENTARIO):
        st.error("No hay insumos creados en el catálogo.")
        return
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    if df_inventario.empty:
        st.error("No hay insumos creados en el catálogo.")
        return
        
    with st.form("formulario_entrada"):
        insumo_seleccionado = st.selectbox('Selecciona el Insumo:', df_inventario['Nombre'].tolist())
        cantidad = st.number_input('Cantidad que Ingresa:', min_value=0.1, step=0.1)
        costo_total = st.number_input('Costo Total ($):', min_value=0.0, step=1.0)
        proveedor = st.text_input('Proveedor / Distribuidor:')
        comentarios = st.text_area('Observaciones o Aclaraciones de la Nota:')
        archivo_foto = st.file_uploader("Subir Evidencia Fotográfica de la Nota de Compra:", type=['png', 'jpg', 'jpeg'])
        boton_entrada = st.form_submit_button('Procesar y Guardar Entrada')
        
        if boton_entrada:
            if proveedor.strip() == "":
                st.error("❌ Error: Debes especificar el Proveedor para fines fiscales.")
            elif archivo_foto is None:
                st.error("❌ Error Obligatorio: Debes subir la fotografía de la nota o comprobante para autorizar el inventario.")
            else:
                marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = archivo_foto.name.split(".")[-1]
                nombre_archivo_seguro = f"nota_{insumo_seleccionado.replace(' ', '_')}_{marca_tiempo}.{extension}"
                ruta_almacenamiento = os.path.join(CARPETA_COMPROBANTES, nombre_archivo_seguro)
                
                with open(ruta_almacenamiento, "wb") as f:
                    f.write(archivo_foto.getbuffer())
                
                if not os.path.exists(ARCHIVO_GASTOS):
                    pd.DataFrame(columns=['Fecha', 'Insumo', 'Monto', 'Cantidad', 'Proveedor']).to_csv(ARCHIVO_GASTOS, index=False)
                
                df_inventario.loc[df_inventario['Nombre'] == insumo_seleccionado, 'Cantidad_Disponible'] += cantidad
                df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                
                df_gastos = pd.read_csv(ARCHIVO_GASTOS)
                if 'Proveedor' not in df_gastos.columns:
                    df_gastos['Proveedor'] = "No Registrado"
                
                nuevo_registro = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), insumo_seleccionado, costo_total, cantidad, proveedor]], columns=['Fecha', 'Insumo', 'Monto', 'Cantidad', 'Proveedor'])
                df_gastos = pd.concat([df_gastos, nuevo_registro], ignore_index=True)
                df_gastos.to_csv(ARCHIVO_GASTOS, index=False)
                
                detalles_auditoria = (f"Proveedor: {proveedor} | Ingresaron {cantidad} uds. | Costo: ${costo_total} MXN | Ruta: {ruta_almacenamiento}")
                registrar_actividad_bitacora("Compras", "Registro de Entrada + Foto", detalles_auditoria)
                st.success(f"✔️ Entrada registrada con éxito. Fotografía guardada.")

# ==============================================================================
# MODIFICACIÓN AVANZADA: REORGANIZACIÓN INTEGRAL DEL MÓDULO DE COCINA
# ==============================================================================
def registrar_salidas_cocina():
    st.header('📤 Operaciones de Cocina y Control de Consumos')
    if not os.path.exists(ARCHIVO_INVENTARIO):
        st.error("No hay inventario registrado en el sistema.")
        return
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    if df_inventario.empty:
        st.error("No hay inventario registrado en el sistema.")
        return

    # Creamos sub-pestañas visuales de control profesional
    tab1, tab2 = st.tabs(["📋 Despacho Operativo Diario", "🗑️ Cierre de Turno (Mermas / Ajustes)"])

    # PESTAÑA 1: DESPACHO TRADICIONAL
    with tab1:
        st.subheader("Salida Regular de Recursos")
        with st.form("form_salida_regular"):
            insumo_seleccionado = st.selectbox('Selecciona Recurso o Alimento a Extraer:', df_inventario['Nombre'].tolist())
            cantidad_solicitada = st.number_input('Cantidad a Consumir:', min_value=0.1, step=0.1)
            boton_salida = st.form_submit_button('Confirmar Extracción de Almacén')
            
            if boton_salida:
                stock_actual = df_inventario.loc[df_inventario['Nombre'] == insumo_seleccionado, 'Cantidad_Disponible'].values[0]
                if cantidad_solicitada > stock_actual:
                    st.error(f"❌ Error Crítico: Existencias insuficientes. Stock actual de '{insumo_seleccionado}': {stock_actual} unidades.")
                else:
                    df_inventario.loc[df_inventario['Nombre'] == insumo_seleccionado, 'Cantidad_Disponible'] -= cantidad_solicitada
                    df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                    
                    # 🔍 BITÁCORA DE AUDITORÍA
                    registrar_actividad_bitacora("Cocina", "Salida Regular", f"Se consumieron {cantidad_solicitada} unidades de '{insumo_seleccionado}' para la operación de la jornada.")
                    st.success(f"✔️ Existencias actualizadas. Se retiraron {cantidad_solicitada} unidades.")
                    st.rerun()

    # PESTAÑA 2: MERMAS, SOBRANTES Y FALTANTES (REGLA DE NEGOCIO SOLICITADA)
    with tab2:
        st.subheader("Conciliación de Alimentos al Fin del Turno")
        st.caption("Utiliza esta sección para reportar desviaciones estocásticas entre las porciones estimadas y el consumo real.")
        
        with st.form("form_ajustes_turno"):
            insumo_ajuste = st.selectbox('Insumo Afectado:', df_inventario['Nombre'].tolist())
            tipo_ajuste = st.radio("Tipo de Incidencia Encontrada:", ["Merma por Sobra (Comida cocinada que se desperdició)", "Faltante (Requirió elaboración de platillos adicionales de emergencia)"])
            cantidad_ajuste = st.number_input('Cantidad Afectada:', min_value=0.1, step=0.1)
            comentarios_ajuste = st.text_input("Comentarios / Justificación del Ajuste:")
            boton_ajuste = st.form_submit_button('Procesar Ajuste Operativo')
            
            if boton_ajuste:
                stock_actual = df_inventario.loc[df_inventario['Nombre'] == insumo_ajuste, 'Cantidad_Disponible'].values[0]
                
                if tipo_ajuste.startswith("Merma por Sobra"):
                    # La comida ya se había sacado del almacén, reportarla como merma no altera el stock actual del almacén (porque ya salió),
                    # pero genera una estampa imborrable en la bitácora para el análisis del supervisor.
                    registrar_actividad_bitacora("Cocina", "Ajuste: Merma por Sobra", f"MERMA DETECTADA: Se desperdiciaron {cantidad_ajuste} unidades de '{insumo_ajuste}'. Motivo: {comentarios_ajuste}")
                    st.warning(f"⚠️ Merma registrada en la bitácora de auditoría para análisis del Supervisor. El almacén central no sufre mermas directas.")
                else:
                    # Es una producción extra de emergencia: SE DEBEN DESCONTAR los insumos adicionales del almacén.
                    if cantidad_ajuste > stock_actual:
                        st.error(f"❌ Error: No puedes preparar alimento extra porque el almacén no tiene suficiente stock de '{insumo_ajuste}' (Disponible: {stock_actual}).")
                    else:
                        df_inventario.loc[df_inventario['Nombre'] == insumo_ajuste, 'Cantidad_Disponible'] -= cantidad_ajuste
                        df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                        registrar_actividad_bitacora("Cocina", "Ajuste: Elaboración Extra", f"PRODUCCIÓN ADICIONAL: Se extrajeron {cantidad_ajuste} unidades de '{insumo_ajuste}' debido a escasez de porciones. Motivo: {comentarios_ajuste}")
                        st.success(f"🔥 Ajuste de emergencia completado. Se descontaron {cantidad_ajuste} unidades adicionales del almacén.")
                        st.rerun()

def reportes_basicos():
    st.header('📊 Reporte Analítico de la Simulación Macro')
    if not os.path.exists('consumo_diario.csv') or not os.path.exists('salidas.csv'):
        st.warning("No hay datos históricos.")
        return
    df_consumo = pd.read_csv('consumo_diario.csv')
    costo_total_historico = df_consumo['costo_total_dia'].sum()
    asistencia_media = df_consumo['asistencia_total'].mean()
    col1, col2 = st.columns(2)
    col1.metric(label="Inversión Total en Alimentos (Histórico)", value=f"${costo_total_historico:,.2f} MXN")
    col2.metric(label="Promedio de Asistencia Diaria", value=f"{int(asistencia_media)} comensales")
    st.subheader("📈 Fluctuación Estocástica de la Asistencia")
    st.line_chart(df_consumo.set_index('fecha')['asistencia_total'])

def control_asistencia_telegram():
    st.header('📱 Interfaz de Comunicación: Bot de Telegram')
    token_ingresado = st.text_input("Token API de Telegram:", type="password")
    if st.button('🚀 Desplegar Notificaciones Push'):
        if not token_ingresado:
            st.error("❌ Error: Se requiere un Token API.")
        else:
            registrar_actividad_bitacora("Redes", "Envío Push Telegram", "El operador gatilló el envío masivo de raciones matutinas vía bot.")
            st.success("📱 Simulación de petición de red registrada en bitácora.")

def consultar_bitacora_seguridad():
    st.header("🗃️ Auditoría y Bitácora del Sistema")
    conexion = sqlite3.connect(DB_NAME)
    query = """
        SELECT b.id_registro, u.username, u.rol, b.fecha_hora, b.modulo, b.accion, b.descripcion 
        FROM bitacora_actividades b
        LEFT JOIN usuarios u ON b.id_usuario = u.id_usuario
        ORDER BY b.id_registro DESC;
    """
    df_bitacora = pd.read_sql_query(query, conexion)
    conexion.close()
    if df_bitacora.empty:
        st.warning("La bitácora de auditoría se encuentra vacía.")
    else:
        st.dataframe(df_bitacora, use_container_width=True)

# ==============================================================================
# CONTROL DE PERMISOS DINÁMICOS POR ROL (LA MATRIZ DE SEGURIDAD)
# ==============================================================================
rol_actual = st.session_state['rol']
opciones_menu = []

if rol_actual == 'Administrador':
    opciones_menu = [
        'Consultar Inventario y Alertas',
        'Registrar Nuevos Insumos',
        'Registrar Entradas (Compras)',
        'Registrar Salidas (Cocina)',
        'Reportes y Gastos',
        'Control de Asistencia (Bot Telegram)',
        '🗃️ Ver Bitácora de Auditoría'
    ]
elif rol_actual == 'Despensero':
    opciones_menu = ['Consultar Inventario y Alertas', 'Registrar Nuevos Insumos', 'Registrar Entradas (Compras)']
elif rol_actual == 'Cocina':
    opciones_menu = ['Consultar Inventario y Alertas', 'Registrar Salidas (Cocina)']
elif rol_actual == 'Supervisor':
    opciones_menu = ['Consultar Inventario y Alertas', 'Reportes y Gastos', 'Control de Asistencia (Bot Telegram)', '🗃️ Ver Bitácora de Auditoría']

st.sidebar.title('🧭 Menú Operativo')
opcion = st.sidebar.radio('Ir a la sección:', opciones_menu)

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
elif opcion == '🗃️ Ver Bitácora de Auditoría':
    consultar_bitacora_seguridad()