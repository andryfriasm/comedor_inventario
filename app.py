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
ARCHIVO_GASTOS = 'gastos.csv'  # Restaurado para evitar errores en compras
CARPETA_COMPROBANTES = os.path.join("assets", "comprobantes")

if not os.path.exists(CARPETA_COMPROBANTES):
    os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)

# --------------------------------------------------------------------------
# 🌐 SELECCIÓN DE ENTORNO ACADÉMICO VS REAL
# --------------------------------------------------------------------------
st.sidebar.title("🌐 ENTORNO DE TRABAJO")
entorno_seleccionado = st.sidebar.radio(
    "Selecciona el modo del sistema:",
    ["Modo Académico (Simulación)", "Modo Operación Real"]
)

if entorno_seleccionado == "Modo Académico (Simulación)":
    st.sidebar.info("📊 Viendo datos de simulación (60 días).")
    RUTA_CONSUMO = os.path.join("entorno_simulado", "consumo_diario.csv")
else:
    st.sidebar.warning("🚀 ENTORNO EN VIVO: Datos reales de planta.")
    RUTA_CONSUMO = os.path.join("entorno_real", "consumo_diario.csv")

st.sidebar.write("---")

# --------------------------------------------------------------------------
# 🧠 ALGORITMO: CÁLCULO DEL MARGEN DE SEGURIDAD DINÁMICO
# --------------------------------------------------------------------------
def calcular_margen_seguridad_dinamico(tipo_comida):
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT porcentaje_desviacion FROM historico_desviaciones 
        WHERE tipo_comida = ? 
        ORDER BY fecha DESC LIMIT 3;
    """, (tipo_comida,))
    resultados = cursor.fetchall()
    conexion.close()
    
    if len(resultados) == 0:
        return 0.10  # 10% base por defecto
    
    suma_desviaciones = sum([r[0] for r in resultados])
    promedio = (suma_desviaciones / len(resultados)) / 100.0
    return promedio

# --------------------------------------------------------------------------
# FUNCIONES DE SEGURIDAD Y BITÁCORA
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

# Estado de la sesión
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
if 'usuario' not in st.session_state: st.session_state['usuario'] = ""
if 'rol' not in st.session_state: st.session_state['rol'] = ""

if not st.session_state['autenticado']:
    st.markdown("<h2 style='text-align: center;'>🔐 Control de Acceso</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Usuario:")
        p = st.text_input("Contraseña:", type="password")
        if st.form_submit_button("Ingresar"):
            res = verificar_credenciales(u, p)
            if res:
                st.session_state['autenticado'] = True
                st.session_state['id_usuario'] = res[0]
                st.session_state['usuario'] = u
                st.session_state['rol'] = res[1]
                st.rerun()
            else: st.error("Credenciales incorrectas.")
    st.stop()

st.sidebar.markdown(f"👤 **Usuario:** `{st.session_state['usuario']}` | **Rol:** `{st.session_state['rol']}`")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state['autenticado'] = False
    st.rerun()

st.sidebar.write("---")

# --------------------------------------------------------------------------
# 📦 RESTAURADO: MÓDULOS DE ADMINISTRACIÓN E INVENTARIO
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
        nombre = st.text_input('Nombre del Insumo (ej. Pechuga de Pollo, Gas LP):')
        categoria = st.selectbox('Categoría:', ['Abarrotes', 'Carnes', 'Verduras', 'Lácteos', 'Recursos Operativos', 'Otros'])
        unidad = st.selectbox('Unidad de Medida:', ['Kilogramos (Kg)', 'Litros (L)', 'Unidades (U)'])
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
                
                registrar_actividad_bitacora("Compras", "Entrada Insumo", f"Ingresó {cantidad} de {insumo_seleccionado}")
                st.success("✔️ Entrada guardada con éxito.")

# --------------------------------------------------------------------------
# 📱 INTERFAZ OPERATIVA: VENTANAS DE HORARIOS DE TELEGRAM
# --------------------------------------------------------------------------
def modulo_simulador_bot_telegram():
    st.header("📱 Panel Operativo del Bot de Telegram")
    st.write("Configuración de ventanas de tiempo rígidas para la confirmación automatizada.")
    
    esquema_datos = [
        {"Servicio": "Desayuno", "Envío Automático": "17:00 (Día anterior)", "Límite Confirmación": "18:00 (Día anterior)", "Botones rápidos": "Sí / No"},
        {"Servicio": "Comida", "Envío Automático": "08:00 (Mismo día)", "Límite Confirmación": "09:00 (Mismo día)", "Botones rápidos": "Sí / No"},
        {"Servicio": "Cena", "Envío Automático": "14:00 (Mismo día)", "Límite Confirmación": "15:00 (Mismo día)", "Botones rápidos": "Sí / No"}
    ]
    st.table(pd.DataFrame(esquema_datos))
    
    st.subheader("Simulador de Mensaje Push con Botones Inline")
    tipo_turno = st.selectbox("Selecciona el turno a disparar hoy:", ["Desayuno", "Comida", "Cena"])
    
    with st.container(border=True):
        st.markdown(f"**🤖 Bot Comedor Industrial dice:**")
        st.markdown(f"¡Hola! Te recordamos confirmar tu asistencia para el servicio de **{tipo_turno}** de hoy.")
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("👍 Sí asistiré"):
            st.success("🤖 Bot: Tu respuesta 'SÍ' ha sido guardada inalterablemente.")
        if col_btn2.button("👎 No asistiré"):
            st.warning("🤖 Bot: Tu respuesta 'NO' ha sido guardada.")

# --------------------------------------------------------------------------
# 📥 INTERFAZ OPERATIVA: CHECK-IN EN BARRA
# --------------------------------------------------------------------------
def modulo_check_in_barra():
    st.header("📥 Registro de Acceso Real (Check-In)")
    st.write("Usa esta pantalla cuando el comensal llegue físicamente a la barra.")
    
    turno_actual = st.selectbox("Turno del Servicio:", ["Desayuno", "Comida", "Cena"])
    
    with st.form("form_checkin", clear_on_submit=True):
        id_empleado = st.text_input("Escanea o escribe el ID del Empleado (ej: EMP_1001):")
        if st.form_submit_button("🟢 Registrar Entrega de Alimento"):
            if id_empleado.strip() == "":
                st.error("Error: El ID del empleado es obligatorio.")
            else:
                fecha_hoy = datetime.now().strftime("%Y-%m-%d")
                hora_ahora = datetime.now().strftime("%H:%M:%S")
                
                conexion = sqlite3.connect(DB_NAME)
                cursor = conexion.cursor()
                cursor.execute("""
                    INSERT INTO registro_asistencia (id_empleado, fecha, hora_llegada, tipo_comida)
                    VALUES (?, ?, ?, ?);
                """, (id_empleado, fecha_hoy, hora_ahora, turno_actual))
                conexion.commit()
                conexion.close()
                
                registrar_actividad_bitacora("Cocina", "Check-In", f"Empleado {id_empleado} ingresó al comedor.")
                st.success(f"✅ Acceso concedido al empleado `{id_empleado}` a las {hora_ahora}.")
                
    st.subheader("📋 Lista de Accesos en este Turno")
    conexion = sqlite3.connect(DB_NAME)
    df_accesos = pd.read_sql_query("""
        SELECT id_empleado, hora_llegada FROM registro_asistencia 
        WHERE fecha = date('now') AND tipo_comida = ?
        ORDER BY id_asistencia DESC;
    """, conexion, params=(turno_actual,))
    conexion.close()
    st.dataframe(df_accesos, use_container_width=True)

# --------------------------------------------------------------------------
# 🍳 MODULO DE COCINA CON MARGEN DINÁMICO INTEGRADO
# --------------------------------------------------------------------------
def modulo_cocina_automatizado():
    st.header("🍳 Operaciones Automatizadas de Cocina")
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    margen_calculado = calcular_margen_seguridad_dinamico("Comida")
    
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM confirmaciones_telegram WHERE fecha = ? AND tipo_comida = 'Comida';", (fecha_hoy,))
    confirmados_telegram = cursor.fetchone()[0]
    
    if confirmados_telegram == 0:
        confirmados_telegram = 100 
        
    raciones_recomendadas = int(confirmados_telegram * (1 + margen_calculado))
    conexion.close()
    
    st.subheader("Plan de Producción Inteligente")
    col1, col2, col3 = st.columns(3)
    col1.metric("Telegram (Confirmados)", f"{confirmados_telegram} pax")
    col2.metric("Margen Dinámico Aprendido", f"+{int(margen_calculado*100)}%")
    col3.metric("Raciones Sugeridas por Algoritmo", f"{raciones_recomendadas} platos")
    st.caption("💡 El margen dinámico se autocalcula usando el promedio de errores de asistencia de los últimos 3 días.")

# --------------------------------------------------------------------------
# 🗃️ RESTAURADO: BITÁCORA DE SEGURIDAD
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
# 🧭 ENRUTADOR DINÁMICO POR ROL 
# --------------------------------------------------------------------------
rol = st.session_state['rol']
menu = []

if rol == 'Administrador':
    menu = ['Ver Almacén', 'Catalogar Insumos', 'Registrar Entradas (Compras)', 'Módulo de Cocina', 'Check-In en Barra', 'Alertas Telegram (Bot)', 'Bitácora de Seguridad']
elif rol == 'Cocina':
    menu = ['Ver Almacén', 'Módulo de Cocina', 'Check-In en Barra']
elif rol == 'Despensero':
    menu = ['Ver Almacén', 'Catalogar Insumos', 'Registrar Entradas (Compras)']
elif rol == 'Supervisor':
    menu = ['Ver Almacén', 'Bitácora de Seguridad']

st.sidebar.title("🧭 Menú Operativo")
opcion = st.sidebar.radio("Ir a:", menu)

if opcion == 'Ver Almacén': consultar_inventario()
elif opcion == 'Catalogar Insumos': registrar_nuevos_insumos()
elif opcion == 'Registrar Entradas (Compras)': registrar_entradas_y_gastos()
elif opcion == 'Módulo de Cocina': modulo_cocina_automatizado()
elif opcion == 'Check-In en Barra': modulo_check_in_barra()
elif opcion == 'Alertas Telegram (Bot)': modulo_simulador_bot_telegram()
elif opcion == 'Bitácora de Seguridad': consultar_bitacora_seguridad()