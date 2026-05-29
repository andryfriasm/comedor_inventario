import pandas as pd
import random
import os
from datetime import datetime, timedelta

print("🚀 Iniciando el motor de simulación para los 7 días de prueba...")

# Carpeta de destino (donde estás ejecutando el proyecto)
RUTA_CARPETA = ""

# ==============================================================================
# CONFIGURACIÓN DE PARÁMETROS BASE
# ==============================================================================
POBLACION_TOTAL = 100
DIAS_SIMULACION = 7
FECHA_INICIO = datetime(2026, 6, 1)
PRESUPUESTO_MAX_DIARIO = 75.0

# ==============================================================================
# 1. CREACIÓN DE ARCHIVOS MAESTROS (DATOS FIJOS)
# ==============================================================================

# A. Crear proveedores.csv
proveedores_data = [
    [1, "Distribuidora Central S.A.", "Arroz", "Bulto", 25.0, 450.0],       # $18 el kg
    [1, "Distribuidora Central S.A.", "Frijol", "Bulto", 25.0, 625.0],      # $25 el kg
    [2, "Frutería El Pollo", "Jitomate", "Caja", 10.0, 220.0],             # $22 el kg
    [2, "Frutería El Pollo", "Cebolla", "Caja", 10.0, 180.0],              # $18 el kg
    [3, "Rastro Local Premium", "Pollo (Pechuga)", "Caja", 15.0, 1200.0],  # $80 el kg
    [3, "Rastro Local Premium", "Res (Bisteck)", "Caja", 15.0, 1800.0],    # $120 el kg
    [4, "Lácteos del Norte", "Queso Oaxaca", "Pieza", 5.0, 600.0],         # $120 el kg
    [4, "Lácteos del Norte", "Jamón de Pavo", "Paquete", 5.0, 400.0],       # $80 el kg
    [1, "Distribuidora Central S.A.", "Tortilla", "Paquete", 10.0, 200.0],  # $20 el kg
    [1, "Distribuidora Central S.A.", "Huevo", "Caja (Cono)", 15.0, 600.0]  # $40 el kg (aprox 240 pzas)
]
df_proveedores = pd.DataFrame(proveedores_data, columns=[
    'id_proveedor', 'nombre_proveedor', 'insumo_suministrado', 
    'unidad_mayoreo', 'cantidad_por_unidad_mayoreo', 'costo_unidad_mayoreo'
])
df_proveedores.to_csv('proveedores.csv', index=False)

# B. Crear comensales.csv (Población concentrada entre 20 y 30 años, IMC 26-28)
nombres = ["Juan", "Pedro", "Ana", "María", "Carlos", "Luis", "Martha", "Sofia", "Jorge", "Elena"]
apellidos = ["Gómez", "Rodríguez", "Mendoza", "Martínez", "Flores", "Sánchez", "Pérez", "Díaz", "Cruz", "Reyes"]

comensales_list = []
random.seed(42) # Para que siempre genere los mismos nombres exactos académicos

for i in range(1, POBLACION_TOTAL + 1):
    nom = f"{random.choice(nombres)} {random.choice(apellidos)} {random.choice(apellidos)}"
    # Distribución para concentrar edades entre 20 y 30 años
    edad = int(random.triangular(18, 45, 25)) 
    # IMC promedio entre 26 y 28
    imc = round(random.uniform(24.5, 29.5), 2)
    comensales_list.append([i, nom, edad, imc])

df_comensales = pd.DataFrame(comensales_list, columns=['id_comensal', 'nombre_completo', 'edad', 'imc'])
df_comensales.to_csv('comensales.csv', index=False)

# C. Crear menus.csv (Costos base e ingredientes principales estandarizados)
# Estructura: id_menu, tiempo_comida, nombre_menu, total_kcal, costo_porcion_mayoreo
menus_data = [
    # DESAYUNOS (Límite ~$20)
    [1, "Desayuno", "Huevo a la Mexicana con Tortillas", 450, 15.50],
    [2, "Desayuno", "Sándwich de Jamón y Queso", 430, 16.00],
    [3, "Desayuno", "Molletes Sencillos con Pico de Gallo", 460, 12.00],
    [4, "Desayuno", "Huevos Estrellados en Salsa", 450, 15.50],
    [5, "Desayuno", "Enfrijoladas con Queso", 480, 14.00],
    [6, "Desayuno", "Omelette de Jamón", 440, 17.00],
    [7, "Desayuno", "Chilaquiles Verdes Sencillos", 490, 13.50],
    [8, "Desayuno", "Burritos de Huevo con Jamón", 470, 16.50],
    [9, "Desayuno", "Quesadillas al Comal", 430, 14.00],
    [10, "Desayuno", "Huevo con Jamón Tradicional", 450, 17.50],
    
    # COMIDAS (Límite ~$35 - Incluyen Arroz y Frijol Obligatorio)
    [11, "Comida", "Bisteck de Res en Salsa Verde", 820, 31.00],
    [12, "Comida", "Pechuga de Pollo entomatada", 780, 28.50],
    [13, "Comida", "Puntas de Res a la Mexicana", 810, 32.00],
    [14, "Comida", "Pollo en Mole Poblano", 850, 30.00],
    [15, "Comida", "Guisado de Res con Papas", 800, 31.50],
    [16, "Comida", "Tinga de Pollo Casera", 770, 27.00],
    [17, "Comida", "Milanesa de Pollo Guisada", 830, 29.00],
    [18, "Comida", "Alóndigas de Res en Chipotle", 820, 32.00],
    [19, "Comida", "Pollo a la Tampiqueña", 790, 29.50],
    [20, "Comida", "Cortadillo de Res", 810, 32.00],
    
    # CENAS (Límite ~$20)
    [21, "Cena", "Sincronizadas Ligeras", 420, 14.50],
    [22, "Cena", "Molletes con Queso Oaxaca", 440, 13.00],
    [23, "Cena", "Tacos Dorados de Papa (Guisado)", 450, 11.00],
    [24, "Cena", "Sopes Sencillos con Frijol", 410, 10.50],
    [25, "Cena", "Ensalada Ligera de Pollo", 390, 16.00],
    [26, "Cena", "Tostadas de Jamón con Crema", 420, 12.50],
    [27, "Cena", "Flautas de Queso", 430, 12.00],
    [28, "Cena", "Sándwich Integración", 400, 15.00],
    [29, "Cena", "Enmoladas Sencillas", 460, 13.00],
    [30, "Cena", "Pan Dulce Tradicional y Leche", 450, 16.00]
]
df_menus = pd.DataFrame(menus_data, columns=['id_menu', 'tiempo_comida', 'nombre_menu', 'total_kcal', 'costo_porcion_mayoreo'])
df_menus.to_csv('menus.csv', index=False)

# D. Crear recetas.csv (Contiene la porción exacta estándar por persona en gramos)
# Para simplificar la base de datos de la simulación académica, nos enfocaremos en los insumos críticos del almacén
recetas_data = [
    # Receta Desayuno 1 (Huevo a la Mexicana): Huevo=100g, Jitomate=30g, Cebolla=10g, Tortilla=50g
    [1, "Huevo", 100.0], [1, "Jitomate", 30.0], [1, "Cebolla", 10.0], [1, "Tortilla", 50.0],
    # Comida 11 (Bisteck Verde): Res=120g, Jitomate=50g, Arroz=50g (OBLIGATORIO), Frijol=50g (OBLIGATORIO)
    [11, "Res (Bisteck)", 120.0], [11, "Jitomate", 50.0], [11, "Arroz", 50.0], [11, "Frijol", 50.0],
    # Cena 21 (Sincronizadas): Tortilla=60g, Jamón de Pavo=40g, Queso Oaxaca=40g
    [21, "Tortilla", 60.0], [21, "Jamón de Pavo", 40.0], [21, "Queso Oaxaca", 40.0]
]
df_recetas = pd.DataFrame(recetas_data, columns=['id_menu', 'ingrediente', 'cantidad_por_persona_g_ml'])
df_recetas.to_csv('recetas.csv', index=False)


# ==============================================================================
# 2. PROCESAMIENTO Y EJECUCIÓN DE LA SIMULACIÓN (7 DÍAS EN HISTÓRICO)
# ==============================================================================

asistencias_list = []
consumo_diario_list = []
salidas_list = []

# Inicializamos un inventario inicial abundante para arrancar la simulación de prueba sin compras el día 1
inventario_inicial = {
    "Huevo": 100.0, "Jitomate": 50.0, "Cebolla": 30.0, "Tortilla": 80.0,
    "Arroz": 120.0, "Frijol": 120.0, "Res (Bisteck)": 100.0, 
    "Jamón de Pavo": 40.0, "Queso Oaxaca": 40.0
}

# Ejecución ciclo de 7 días
for dia in range(DIAS_SIMULACION):
    fecha_actual = FECHA_INICIO + timedelta(days=dia)
    fecha_str = fecha_actual.strftime('%Y-%m-%d')
    
    # REGLA 1: Asistencia Aleatoria entre 75% y 90%
    asistencia_hoy = random.randint(75, 90)
    
    # Seleccionar comensales específicos que asistieron hoy
    asistentes_ids = random.sample(range(1, POBLACION_TOTAL + 1), asistencia_hoy)
    for c_id in range(1, POBLACION_TOTAL + 1):
        estatus = 1 if c_id in asistentes_ids else 0
        asistencias_list.append([fecha_str, c_id, estatus])
        
    # REGLA 2: Rotación de menús matemática (Para esta prueba usaremos Menú 1, Comida 11 y Cena 21 fijos)
    id_des = 1
    id_com = 11
    id_cen = 21
    
    # Conseguir costos base
    c_des = df_menus.loc[df_menus['id_menu'] == id_des, 'costo_porcion_mayoreo'].values[0]
    c_com = df_menus.loc[df_menus['id_menu'] == id_com, 'costo_porcion_mayoreo'].values[0]
    c_cen = df_menus.loc[df_menus['id_menu'] == id_cen, 'costo_porcion_mayoreo'].values[0]
    
    costo_teorico_persona = c_des + c_com + c_cen
    costo_total_dia = costo_teorico_persona * asistencia_hoy
    kcal_totales = 1720 # Suma de calorías de los tres menús seleccionados
    
    # Guardar resumen del día
    consumo_diario_list.append([fecha_str, asistencia_hoy, id_des, id_com, id_cen, round(costo_total_dia, 2), kcal_totales])
    
    # REGLA 3 Y 4: Calcular consumo con "Efecto Cucharón (±5%)" y "Merma (2% al 5%)"
    # Buscamos todos los ingredientes requeridos para los tres menús del día
    ingredientes_hoy = df_recetas[df_recetas['id_menu'].isin([id_des, id_com, id_cen])]
    
    for idx, row in ingredientes_hoy.iterrows():
        ing = row['ingrediente']
        gramos_base = row['cantidad_por_persona_g_ml']
        
        # Simular plato por plato (Efecto Cucharón)
        total_consumo_neto_g = 0
        for _ in range(asistencia_hoy):
            variacion_cucharon = random.uniform(0.95, 1.05) # ±5%
            total_consumo_neto_g += (gramos_base * variacion_cucharon)
            
        # Convertir a Kilogramos
        total_consumo_neto_kg = total_consumo_neto_g / 1000.0
        
        # Aplicar Merma Operativa del día (2% al 5%)
        porcentaje_merma = random.uniform(0.02, 0.05)
        cantidad_merma_kg = total_consumo_neto_kg * porcentaje_merma
        total_retirado_almacen_kg = total_consumo_neto_kg + cantidad_merma_kg
        
        # Registrar la salida de almacén
        salidas_list.append([
            fecha_str, ing, 
            round(total_consumo_neto_kg, 2), 
            round(cantidad_merma_kg, 2), 
            round(total_retirado_almacen_kg, 2)
        ])
        
        # Restar del inventario de la simulación
        if ing in inventario_inicial:
            inventario_inicial[ing] -= total_retirado_almacen_kg

# Guardar archivos transaccionales generados
df_asistencia_final = pd.DataFrame(asistencias_list, columns=['fecha', 'id_comensal', 'asistio'])
df_asistencia_final.to_csv('asistencia_historica.csv', index=False)

df_consumo_final = pd.DataFrame(consumo_diario_list, columns=['fecha', 'asistencia_total', 'id_desayuno', 'id_comida', 'id_cena', 'costo_total_dia', 'kcal_totales_dia'])
df_consumo_final.to_csv('consumo_diario.csv', index=False)

df_salidas_final = pd.DataFrame(salidas_list, columns=['fecha', 'ingrediente', 'cantidad_neta_consumida_kg', 'cantidad_merma_kg', 'total_retirado_almacen_kg'])
df_salidas_final.to_csv('salidas.csv', index=False)

# Guardar el inventario final resultante de la semana
inventario_rows = []
for ing, disp in inventario_inicial.items():
    inventario_rows.append([1, ing, round(disp, 2), 15.0]) # 15 kg como stock mínimo general de alerta
df_inventario_final = pd.DataFrame(inventario_rows, columns=['ID', 'Nombre', 'Cantidad_Disponible', 'Stock_Minimo'])
df_inventario_final.to_csv('inventario.csv', index=False)

print("✅ ¡Simulación completada con éxito! Se han generado los archivos CSV para 7 días.")
