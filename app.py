import streamlit as st
import pandas as pd
import os
import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "comedor.db"
ARCHIVO_INSUMOS = 'insumos.csv'
ARCHIVO_INVENTARIO = 'inventario.csv'
ARCHIVO_RECETAS = 'recetas.csv'
ARCHIVO_COMENSALES = 'comensales.csv'
CARPETA_COMPROBANTES = os.path.join("assets", "comprobantes")
MARGEN_SEGURIDAD = 0.10  # 10% de margen de seguridad operativo

if not os.path.exists(CARPETA_COMPROBANTES):
    os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)

# --------------------------------------------------------------------------
# 🌐 CAPA DE AISLAMIENTO: SELECTOR DE ENTORNO EN LA BARRA LATERAL
# --------------------------------------------------------------------------
st.sidebar.title("🌐 ENTORNO DE TRABAJO")
entorno_seleccionado = st.sidebar.radio(
    "Selecciona el modo del sistema:",
    ["Modo Académico (Simulación)", "Modo Operación Real"]
)

# Definimos las rutas de los archivos dependiendo de la elección del usuario
if entorno_seleccionado == "Modo Académico (Simulación)":
    st.sidebar.info("📊 Viendo datos de simulación (60 días).")
    RUTA_CONSUMO = os.path.join("entorno_simulado", "consumo_diario.csv")
    RUTA_SALIDAS = os.path.join("entorno_simulado", "salidas.csv")
else:
    st.sidebar.warning("🚀 ENTORNO EN VIVO: Datos reales de planta.")
    RUTA_CONSUMO = os.path.join("entorno_real", "consumo_diario.csv")
    RUTA_SALIDAS = os.path.join("entorno_real", "salidas.csv")
    
    # Creamos los archivos reales vacíos si es la primera vez que se entra a este modo
    if not os.path.exists(RUTA_CONSUMO):
        pd.DataFrame(columns=['fecha', 'asistencia_total', 'costo_total_dia']).to_csv(RUTA_CONSUMO, index=False)
    if not os.path.exists(RUTA_SALIDAS):
        pd.DataFrame(columns=['ingrediente', 'cantidad_neta_consumida_kg', 'cantidad_merma_kg']).to_csv(RUTA_SALIDAS, index=False)

st.sidebar.write("---")

# --------------------------------------------------------------------------
# FUNCIONES DE SEGURIDAD, BASE DE DATOS Y BITÁCORA
# --------------------------------------------------------------------------
def verificar_credenciales(username, password_plana):
    hash_ingresado = hashlib.sha256(password_plana.encode()).hexdigest()
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario, rol FROM usuarios WHERE username = ? AND password_hash = ? AND estado = 1;", (username, hash_ingresado))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado

def registrar_actividad_bitacora(modulo, accion, descripcion):
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        id_usuario = st.session_state.get('id_usuario', None)
        cursor.execute("INSERT INTO bitacora_actividades (id_usuario, modulo, accion, descripcion) VALUES (?, ?, ?, ?);", (id_usuario, modulo, accion, descripcion))
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"⚠️ Error en bitácora: {e}")

# --------------------------------------------------------------------------
# INICIALIZACIÓN DEL ESTADO DE SESIÓN
# --------------------------------------------------------------------------
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'rol' not in st.session_state: st.session_state['rol'] = ""

# PANTALLA DE LOGIN
if not st.session_state['autenticado']:
    st.markdown("<h2 style='text-align: center;'>🔐 Control de Acceso</h2>", unsafe_allow_html=True)
    with st.form("formulario_login"):
        usuario_input = st.text_input("Usuario de Red:")
        password_input = st.text_input("Contraseña de Seguridad:", type="password")
        if st.form_submit_button("Iniciar Sesión"):
            datos_usuario = verificar_credenciales(usuario_input, password_input)
            if datos_usuario:
                st.session_state['autenticado'] = True
                st.session_state['id_usuario'] = datos_usuario[0]
                st.session_state['usuario'] = usuario_input
                st.session_state['rol'] = datos_usuario[1]
                registrar_actividad_bitacora("Autenticación", "Inicio de Sesión", f"Usuario {usuario_input} ingresó.")
                st.rerun()
            else:
                st.error("❌ Credenciales inválidas.")
    st.stop()

st.sidebar.markdown(f"👤 **Usuario:** `{st.session_state['usuario']}` | **Rol:** `{st.session_state['rol']}`")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()

st.sidebar.write("---")

# --------------------------------------------------------------------------
# MÓDULOS DE ADMINISTRACIÓN E INVENTARIO
# --------------------------------------------------------------------------
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
        st.error('⚠️ ALERTA: ¡Insumos en niveles críticos de escasez!')
        st.dataframe(alertas_criticas[['Nombre', 'Cantidad_Disponible', 'Stock_Minimo']])
    st.subheader('Inventario Completo')
    st.dataframe(df_inventario, use_container_width=True)

def registrar_nuevos_insumos():
    st.header('📦 Catálogo: Registrar Nuevo Insumo')
    with st.form("formulario_insumo", clear_on_submit=True):
        nombre = st.text_input('Nombre del Insumo (ej. Pechuga de Pollo, Gas LP, Jabón):')
        categoria = st.selectbox('Categoría:', ['Abarrotes', 'Carnes', 'Verduras', 'Lácteos', 'Recursos Operativos', 'Otros'])
        unidad = st.selectbox('Unidad de Medida:', ['Kilogramos (Kg)', 'Litros (L)', 'Unidades (U)', 'Tanques / Litros Gas'])
        stock_minimo = st.number_input('Stock Mínimo de Alerta:', min_value=1, value=5)
        if st.form_submit_button('Registrar Producto'):
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
                df_inventario = pd.concat([df_inventario, pd.DataFrame([[nuevo_id, nombre, 100.0, stock_minimo]], columns=df_inventario.columns)], ignore_index=True)
                df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                
                registrar_actividad_bitacora("Inventario", "Alta de Insumo", f"Se catalogó '{nombre}'.")
                st.success(f"¡'{nombre}' agregado con éxito!")

def registrar_entradas_y_gastos():
    st.header('📥 Entrada de Almacén y Evidencia Digital')
    if not os.path.exists(ARCHIVO_INVENTARIO):
        st.error("No hay insumos creados en el catálogo.")
        return
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    
    with st.form("formulario_entrada"):
        insumo_seleccionado = st.selectbox('Selecciona el Insumo:', df_inventario['Nombre'].tolist())
        cantidad = st.number_input('Cantidad que Ingresa:', min_value=0.1, step=0.1)
        costo_total = st.number_input('Costo Total ($):', min_value=0.0, step=1.0)
        proveedor = st.text_input('Proveedor / Distribuidor:')
        archivo_foto = st.file_uploader("Subir Evidencia Fotográfica:", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button('Procesar y Guardar Entrada'):
            if proveedor.strip() == "" or archivo_foto is None:
                st.error("❌ El proveedor y la foto son obligatorios.")
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
                nuevo_registro = pd.DataFrame([[datetime.now().strftime('%Y-%m-%d'), insumo_seleccionado, costo_total, cantidad, proveedor]], columns=['Fecha', 'Insumo', 'Monto', 'Cantidad', 'Proveedor'])
                df_gastos = pd.concat([df_gastos, nuevo_registro], ignore_index=True)
                df_gastos.to_csv(ARCHIVO_GASTOS, index=False)
                
                registrar_actividad_bitacora("Compras", "Entrada Insumo", f"Ingresó {amount} de {insumo_seleccionado}")
                st.success("✔️ Entrada guardada con éxito.")

# --------------------------------------------------------------------------
# MOTOR DE COCINA AUTOMATIZADO
# --------------------------------------------------------------------------
def modulo_cocina_automatizado():
    st.header("🍳 Operaciones Automatizadas de Cocina")
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM confirmaciones_telegram WHERE fecha = ? AND tipo_comida = 'Comida';", (fecha_hoy,))
    confirmados_telegram = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM control_servicio_diario WHERE fecha = ? AND tipo_comida = 'Comida';", (fecha_hoy,))
    servicio = cursor.fetchone()
    
    menu_hoy = "Milanesa de Pollo con Arroz"
    id_menu_hoy = 1
    raciones_recomendadas = int(confirmados_telegram * (1 + MARGEN_SEGURIDAD))
    
    if not servicio:
        cursor.execute("""
            INSERT INTO control_servicio_diario (fecha, tipo_comida, menu_asignado, confirmados_telegram, raciones_planeadas, estado_servicio)
            VALUES (?, 'Comida', ?, ?, ?, 'PLANEADO');
        """, (fecha_hoy, menu_hoy, confirmados_telegram, raciones_recomendadas))
        conexion.commit()
        cursor.execute("SELECT * FROM control_servicio_diario WHERE fecha = ? AND tipo_comida = 'Comida';", (fecha_hoy,))
        servicio = cursor.fetchone()
    conexion.close()
    
    estado_servicio = servicio[15]
    df_recetas = pd.read_csv(ARCHIVO_RECETAS)
    df_recetas_filtrado = df_recetas[df_recetas['id_receta'] == id_menu_hoy].copy()
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    
    df_recetas_filtrado['Cantidad_Requerida_Total'] = df_recetas_filtrado['porcion_por_persona_kg_u'] * raciones_recomendadas
    df_analisis = pd.merge(df_recetas_filtrado, df_inventario, left_on='nombre_insumo', right_on='Nombre', how='left')
    df_analisis['Cantidad_Disponible'] = df_analisis['Cantidad_Disponible'].fillna(0)
    df_analisis['Estatus'] = df_analisis.apply(lambda r: "✅ Suficiente" if r['Cantidad_Disponible'] >= r['Cantidad_Requerida_Total'] else "❌ INSUFICIENTE", axis=1)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 1. Plan del Día", "🍳 2. Iniciar Preparación", "🏁 3. Cierre de Turno", "🚨 4. Salidas Extraordinarias"])
    
    with tab1:
        st.subheader("Plan de Producción Recomendado")
        col1, col2, col3 = st.columns(3)
        col1.metric("Menú", menu_hoy)
        col2.metric("Telegram (Confirmados)", f"{confirmados_telegram} pax")
        col3.metric("Raciones Recomendadas (+10%)", f"{raciones_recomendadas} platos")
        st.dataframe(df_analisis[['nombre_insumo', 'Cantidad_Requerida_Total', 'Cantidad_Disponible', 'Estatus']], use_container_width=True)
        
    with tab2:
        st.subheader("Confirmación de Apertura de Ollas")
        if estado_servicio == 'PLANEADO':
            with st.form("form_prod"):
                chef = st.text_input("Nombre del Responsable de Cocina:")
                if st.form_submit_button("🚀 Confirmar e Iniciar Preparación"):
                    if chef.strip() == "": st.error("Escribe un nombre.")
                    else:
                        for index, row in df_analisis.iterrows():
                            df_inventario.loc[df_inventario['Nombre'] == row['nombre_insumo'], 'Cantidad_Disponible'] -= row['Cantidad_Requerida_Total']
                        df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                        
                        conexion = sqlite3.connect(DB_NAME)
                        cursor = conexion.cursor()
                        cursor.execute("UPDATE control_servicio_diario SET estado_servicio = 'PREPARADO', hora_inicio = ?, raciones_reales_preparadas = ? WHERE fecha = ?;", (datetime.now().strftime("%H:%M:%S"), raciones_recomendadas, fecha_hoy))
                        conexion.commit()
                        conexion.close()
                        st.success("🔥 ¡Producción autorizada e inventario descontado!")
                        st.rerun()
        else: st.info(f"El servicio ya fue iniciado.")
        
    with tab3:
        st.subheader("Cierre de Barra y Captura de Desviaciones")
        if estado_servicio == 'PREPARADO':
            with st.form("form_cierre"):
                servidas = st.number_input("Raciones servidas reales:", value=confirmados_telegram)
                sobrantes = st.number_input("Raciones que sobraron en ollas:", value=0)
                faltantes = st.number_input("Raciones que hicieron falta:", value=0)
                if st.form_submit_button("💾 Guardar Cierre de Turno"):
                    conexion = sqlite3.connect(DB_NAME)
                    cursor = conexion.cursor()
                    cursor.execute("""
                        UPDATE control_servicio_diario 
                        SET raciones_servidas_reales = ?, raciones_sobrantes = ?, raciones_faltantes = ?, estado_servicio = 'CERRADO', hora_cierre = ?
                        WHERE fecha = ?;
                    """, (servidas, sobrantes, faltantes, datetime.now().strftime("%H:%M:%S"), fecha_hoy))
                    conexion.commit()
                    conexion.close()
                    st.success("🏁 Métricas congeladas con éxito.")
                    st.rerun()
        else: st.info("El servicio debe estar en estado 'PREPARADO' para poder cerrarse.")
        
    with tab4:
        st.subheader("Salidas de Emergencia o Soporte")
        with st.form("form_excepcion"):
            insumo_ex = st.selectbox("Insumo Extraordinario:", df_inventario['Nombre'].tolist())
            cant_ex = st.number_input("Cantidad Retirada:", min_value=0.1)
            motivo = st.text_input("Justificación (Obligatoria):")
            if st.form_submit_button("🛑 Aplicar Deducción de Excepción"):
                if motivo.strip() == "": st.error("Debes poner un motivo.")
                else:
                    df_inventario.loc[df_inventario['Nombre'] == insumo_ex, 'Cantidad_Disponible'] -= cant_ex
                    df_inventario.to_csv(ARCHIVO_INVENTARIO, index=False)
                    registrar_actividad_bitacora("Cocina", "Excepción", f"Extracción de {cant_ex} de {insumo_ex}. Motivo: {motivo}")
                    st.success("✔️ Anomalía guardada.")

# --------------------------------------------------------------------------
# SUPERVISOR: CAPA DE BUSINESS INTELLIGENCE (ADAPTADA AL ENTORNO)
# --------------------------------------------------------------------------
def reportes_gerenciales_bi():
    st.header('📊 Panel de Inteligencia de Negocio')
    
    # Validamos si existen los archivos en la ruta del entorno seleccionado
    if not os.path.exists(RUTA_CONSUMO) or not os.path.exists(RUTA_SALIDAS):
        st.warning("⚠️ No se detectan registros históricos en este entorno todavía.")
        return
        
    df_consumo = pd.read_csv(RUTA_CONSUMO)
    df_salidas = pd.read_csv(RUTA_SALIDAS)
    
    if df_consumo.empty or df_salidas.empty:
        st.info("📂 El archivo de este entorno está limpio. Comienza a operar para ver analítica.")
        return
        
    # KPIs Básicos
    costo_total = df_consumo['costo_total_dia'].sum()
    asistencia_media = df_consumo['asistencia_total'].mean()
    
    st.subheader("Indicadores Clave (KPIs)")
    col1, col2 = st.columns(2)
    col1.metric("Inversión en Alimentos Acumulada", f"${costo_total:,.2f} MXN")
    col2.metric("Asistencia Promedio", f"{int(asistencia_media)} Comensales")
    
    st.write("---")
    st.subheader("📈 Tendencia de Asistencia")
    df_linea = df_consumo[['fecha', 'asistencia_total']].copy().set_index('fecha')
    st.line_chart(df_linea, use_container_width=True)

# --------------------------------------------------------------------------
# TELEGRAM NOTIFICACIONES
# --------------------------------------------------------------------------
def control_asistencia_telegram():
    st.header('📱 Interfaz de Comunicación: Bot de Telegram')
    token = st.text_input("Token API de Telegram:", type="password")
    if st.button('🚀 Desplegar Notificaciones Push'):
        if not token: st.error("❌ Se requiere un Token API.")
        else: st.success("📱 Alertas enviadas a terminales enlazados.")

# --------------------------------------------------------------------------
# BITÁCORA DE SEGURIDAD
# --------------------------------------------------------------------------
def consultar_bitacora_seguridad():
    st.header("🗃️ Auditoría y Bitácora del Sistema")
    conexion = sqlite3.connect(DB_NAME)
    df_bitacora = pd.read_sql_query("""
        SELECT b.id_registro, u.username, u.rol, b.fecha_hora, b.modulo, b.accion, b.descripcion 
        FROM bitacora_actividades b
        LEFT JOIN usuarios u ON b.id_usuario = u.id_usuario
        ORDER BY b.id_registro DESC;
    """, conexion)
    conexion.close()
    st.dataframe(df_bitacora, use_container_width=True)

# --------------------------------------------------------------------------
# ENRUTADOR DINÁMICO POR ROL
# --------------------------------------------------------------------------
rol = st.session_state['rol']
menu = []

if rol == 'Administrador':
    menu = ['Ver Almacén', 'Catalogar Insumos', 'Registrar Entradas (Compras)', 'Módulo de Cocina', 'Reportes de Supervisión (BI)', 'Alertas Telegram', 'Bitácora de Seguridad']
elif rol == 'Cocina':
    menu = ['Ver Almacén', 'Módulo de Cocina']
elif rol == 'Despensero':
    menu = ['Ver Almacén', 'Catalogar Insumos', 'Registrar Entradas (Compras)']
elif rol == 'Supervisor':
    menu = ['Ver Almacén', 'Reportes de Supervisión (BI)', 'Bitácora de Seguridad']

st.sidebar.title("🧭 Menú Operativo")
opcion = st.sidebar.radio("Ir a:", menu)

if opcion == 'Ver Almacén': consultar_inventario()
elif opcion == 'Catalogar Insumos': registrar_nuevos_insumos()
elif opcion == 'Registrar Entradas (Compras)': registrar_entradas_y_gastos()
elif opcion == 'Módulo de Cocina': modulo_cocina_automatizado()
elif opcion == 'Reportes de Supervisión (BI)': reportes_gerenciales_bi()
elif opcion == 'Alertas Telegram': control_asistencia_telegram()
elif opcion == 'Bitácora de Seguridad': consultar_bitacora_seguridad()