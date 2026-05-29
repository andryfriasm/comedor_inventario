import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# CONFIGURACIÓN INICIAL Y ARCHIVOS DATA (CSV Y SQLITE SIMULADO)
# ==============================================================================
ARCHIVO_INSUMOS = 'insumos.csv'
ARCHIVO_INVENTARIO = 'inventario.csv'
ARCHIVO_GASTOS = 'gastos.csv'
ARCHIVO_ASISTENCIA = 'asistencia.csv' # Archivo para el Simulador de WhatsApp

def inicializar_archivos():
    if not os.path.exists(ARCHIVO_INSUMOS):
        df = pd.DataFrame(columns=['ID', 'Nombre', 'Categoria', 'Unidad'])
        df.to_csv(ARCHIVO_INSUMOS, index=False)
        
    if not os.path.exists(ARCHIVO_INVENTARIO):
        df = pd.DataFrame(columns=['ID', 'Nombre', 'Cantidad_Disponible', 'Stock_Minimo'])
        df.to_csv(ARCHIVO_INVENTARIO, index=False)
        
    if not os.path.exists(ARCHIVO_GASTOS):
        df = pd.DataFrame(columns=['Fecha', 'Insumo', 'Monto', 'Cantidad'])
        df.to_csv(ARCHIVO_GASTOS, index=False)

    if not os.path.exists(ARCHIVO_ASISTENCIA):
        # Base de datos simulada de empleados y si asisten hoy (1 = Sí, 0 = No, -1 = Sin responder)
        df = pd.DataFrame([
            ['Carlos Mendoza', -1],
            ['Ana Rodríguez', -1],
            ['Luis Gómez', -1],
            ['Martha Flores', -1],
            ['Jorge Martínez', -1]
        ], columns=['Empleado', 'Asistencia'])
        df.to_csv(ARCHIVO_ASISTENCIA, index=False)

inicializar_archivos()

st.title('🍳 Sistema de Gestión - Comedor Laboral')

# ==============================================================================
# 1. SECCIÓN: CONSULTAR INVENTARIO Y ALERTAS
# ==============================================================================
def consultar_inventario():
    st.header('🔍 Estado Actual del Almacén')
    df_inventario = pd.read_csv(ARCHIVO_INVENTARIO)
    
    if df_inventario.empty:
        st.warning("El almacén está vacío. Registra insumos primero.")
        return

    # Alertas de stock crítico
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
# 5. SECCIÓN: REPORTES, GASTOS Y MERMAS (OPTIMIZADO PARA SIMULACIÓN)
# ==============================================================================
def reportes_basicos():
    st.header('📊 Reporte Analítico de la Simulación (7 Días de Prueba)')
    
    # Comprobar si los archivos de la simulación existen
    if not os.path.exists('consumo_diario.csv') or not os.path.exists('salidas.csv'):
        st.warning("No hay datos históricos generados. Ejecuta primero el simulador.")
        return
        
    df_consumo = pd.read_csv('consumo_diario.csv')
    df_salidas = pd.read_csv('salidas.csv')
    
    # KPI 1: Presupuesto e Inversión
    costo_total_historico = df_consumo['costo_total_dia'].sum()
    asistencia_media = df_consumo['asistencia_total'].mean()
    
    col1, col2 = st.columns(2)
    col1.metric(label="Costo Invertido Total en Alimentos (7 Días)", value=f"${costo_total_historico:,.2f} MXN")
    col2.metric(label="Promedio de Asistencia Diaria", value=f"{int(asistencia_media)} comensales")
    
    # KPI 2: Gráfico de Asistencia por Día
    st.subheader("📈 Fluctuación de Asistencia Diaria (Meta: 75% - 90%)")
    st.line_chart(df_consumo.set_index('fecha')['asistencia_total'])
    
    # KPI 3: Análisis de Desperdicio y Cucharón (Mermas)
    st.write('---')
    st.subheader("🗑️ Auditoría de Mermas y Desperdicios en Cocina")
    st.write("El siguiente gráfico muestra el impacto real de la merma por preparación y la variación en el servicio:")
    
    # Agrupamos por ingrediente para ver cuál genera más desperdicio
    mermas_agrupadas = df_salidas.groupby('ingrediente')[['cantidad_neta_consumida_kg', 'cantidad_merma_kg']].sum()
    st.bar_chart(mermas_agrupadas)
    
    st.write("**Detalle de consumos y mermas por ingrediente (Valores en Kilogramos):**")
    st.dataframe(mermas_agrupadas)

# ==============================================================================
# 6. SECCIÓN: SIMULADOR DE ASISTENCIA (WHATSAPP INNOVACIÓN)
# ==============================================================================
def simulador_whatsapp():
    st.header('📱 Inteligencia de Negocio: Simulador de WhatsApp Confirma')
    st.write('Esta pantalla simula las respuestas que los comensales envían desde sus celulares por WhatsApp.')
    
    df_asistencia = pd.read_csv(ARCHIVO_ASISTENCIA)
    
    # Formulario para simular la respuesta de un empleado
    with st.form("simulador_celular"):
        empleado = st.selectbox("Selecciona el Empleado que responderá el mensaje:", df_asistencia['Empleado'].tolist())
        respuesta = st.radio("Respuesta simulada de WhatsApp:", ["Sí asistiré a comer", "No podré asistir"])
        boton_simular = st.form_submit_button("Enviar respuesta simulada")
        
        if boton_simular:
            valor_asistencia = 1 if respuesta == "Sí asistiré a comer" else 0
            df_asistencia.loc[df_asistencia['Empleado'] == empleado, 'Asistencia'] = valor_asistencia
            df_asistencia.to_csv(ARCHIVO_ASISTENCIA, index=False)
            st.success(f"📱 Notificación recibida: {empleado} respondió '{respuesta}'")
            
    # Panel de control para los Cocineros
    st.write('---')
    st.subheader('🍳 Panel de Control para la Cocina (Cálculo Automático)')
    
    # Recargamos los datos actualizados
    df_actualizado = pd.read_csv(ARCHIVO_ASISTENCIA)
    confirmados = len(df_actualizado[df_actualizado['Asistencia'] == 1])
    cancelados = len(df_actualizado[df_actualizado['Asistencia'] == 0])
    sin_responder = len(df_actualizado[df_actualizado['Asistencia'] == -1])
    
    # Mostrar métricas en tiempo real
    col1, col2, col3 = st.columns(3)
    col1.metric("Raciones a Cocinar (SÍ)", confirmados)
    col2.metric("Cancelados (NO)", cancelados)
    col3.metric("Falta responder", sin_responder)
    
    st.write("**Lista del estado de asistencia de hoy:**")
    # Ponemos etiquetas más entendibles para el usuario final en la tabla visual
    df_visual = df_actualizado.copy()
    df_visual['Asistencia'] = df_visual['Asistencia'].map({1: '✅ Confirmado', 0: '❌ Cancelado', -1: '⏳ Esperando'})
    st.dataframe(df_visual)

# ==============================================================================
# MENÚ LATERAL NAVEGACIÓN
# ==============================================================================
st.sidebar.title('🧭 Panel de Navegación')
opcion = st.sidebar.radio('Ir a la sección:', [
    'Consultar Inventario y Alertas',
    'Registrar Nuevos Insumos',
    'Registrar Entradas (Compras)',
    'Registrar Salidas (Cocina)',
    'Reportes y Gastos',
    'Simulador de Comensal (WhatsApp)'
])

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
elif opcion == 'Simulador de Comensal (WhatsApp)':
    simulador_whatsapp()