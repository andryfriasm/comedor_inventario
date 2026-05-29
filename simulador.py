import pandas as pd
import random
import os
from datetime import datetime, timedelta

print("⚙️ Optimizando el motor estocástico para la simulación de 60 días completos...")

# ==============================================================================
# CONFIGURACIÓN DE PARÁMETROS BASE
# ==============================================================================
POBLACION_TOTAL = 100
DIAS_SIMULACION = 60  # <<-- AMPLIADO A 2 MESES DE OPERACIÓN
FECHA_INICIO = datetime(2026, 6, 1)

# ==============================================================================
# 1. CREACIÓN DE ARCHIVOS MAESTROS (DATOS FIJOS)
# ==============================================================================

# A. Crear proveedores.csv
proveedores_data = [
    [1, "Distribuidora Central S.A.", "Arroz", "Bulto", 25.0, 450.0],       
    [1, "Distribuidora Central S.A.", "Frijol", "Bulto", 25.0, 625.0],      
    [2, "Frutería El Pollo", "Jitomate", "Caja", 10.0, 220.0],             
    [2, "Frutería El Pollo", "Cebolla", "Caja", 10.0, 180.0],              
    [3, "Rastro Local Premium", "Pollo (Pechuga)", "Caja", 15.0, 1200.0],  
    [3, "Rastro Local Premium", "Res (Bisteck)", "Caja", 15.0, 1800.0],    
    [4, "Lácteos del Norte", "Queso Oaxaca", "Pieza", 5.0, 600.0],         
    [4, "Lácteos del Norte", "Jamón de Pavo", "Paquete", 5.0, 400.0],       
    [1, "Distribuidora Central S.A.", "Tortilla", "Paquete", 10.0, 200.0],  
    [1, "Distribuidora Central S.A.", "Huevo", "Caja (Cono)", 15.0, 600.0]  
]
df_proveedores = pd.DataFrame(proveedores_data, columns=[
    'id_proveedor', 'nombre_proveedor', 'insumo_suministrado', 
    'unidad_mayoreo', 'cantidad_por_unidad_mayoreo', 'costo_unidad_mayoreo'
])
df_proveedores.to_csv('proveedores.csv', index=False)

# B. Crear comensales.csv
nombres = ["Juan", "Pedro", "Ana", "María", "Carlos", "Luis", "Martha", "Sofia", "Jorge", "Elena"]
apellidos = ["Gómez", "Rodríguez", "Mendoza", "Martínez", "Flores", "Sánchez", "Pérez", "Díaz", "Cruz", "Reyes"]

comensales_list = []
random.seed(42) 

for i in range(1, POBLACION_TOTAL + 1):
    nom = f"{random.choice(nombres)} {random.choice(apellidos)} {random.choice(apellidos)}"
    edad = int(random.triangular(18, 45, 25)) 
    imc = round(random.uniform(24.5, 29.5), 2)
    comensales_list.append([i, nom, edad, imc])

df_comensales = pd.DataFrame(comensales_list, columns=['id_comensal', 'nombre_completo', 'edad', 'imc'])
df_comensales.to_csv('comensales.csv', index=False)

# C. Crear menus.csv (Configuración de los 10 menús rotativos por tiempo)
menus_data = [
    # DESAYUNOS (IDs 1 al 10 - Límite ~$20)
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
    
    # COMIDAS (IDs 11 al 20 - Límite ~$35 - Todos incluyen Arroz y Frijol)
    [11, "Comida", "Bisteck de Res en Salsa Verde", 820, 31.00],
    [12, "Comida", "Pechuga de Pollo entomatada", 780, 28.50],
    [13, "Comida", "Puntas de Res a la Mexicana", 810, 32.00],
    [14, "Comida", "Pollo en Mole Poblano", 850, 30.00],
    [15, "Comida", "Guisado de Res con Papas", 800, 31.50],
    [16, "Comida", "Tinga de Pollo Casera", 770, 27.00],
    [17, "Comida", "Milanesa de Pollo Guisada", 830, 29.00],
    [18, "Comida", "Albóndigas de Res en Chipotle", 820, 32.00],
    [19, "Comida", "Pollo a la Tampiqueña", 790, 29.50],
    [20, "Comida", "Cortadillo de Res", 810, 32.00],
    
    # CENAS (IDs 21 al 30 - Límite ~$20)
    [21, "Cena", "Sincronizadas Ligeras", 420, 14.50],
    [22, "Cena", "Molletes con Queso Oaxaca", 440, 13.00],
    [23, "Cena", "Tacos Dorados de Papa", 450, 11.00],
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

# D. Mapas de Recetas para la Simulación Dinámica de Insumos Críticos
# Mapeamos los ingredientes base (en gramos por comensal) para simular el impacto en almacén
recetas_data = []
for m_id in range(1, 31):
    # Todos los desayunos llevan una base proteica o carbohidrato
    if m_id in [1, 4, 10]:
        recetas_data.extend([[m_id, "Huevo", 100.0], [m_id, "Jitomate", 20.0], [m_id, "Tortilla", 30.0]])
    elif m_id in [2, 6, 8]:
        recetas_data.extend([[m_id, "Jamón de Pavo", 40.0], [m_id, "Queso Oaxaca", 30.0]])
    else:
        recetas_data.extend([[m_id, "Tortilla", 60.0], [m_id, "Cebolla", 15.0]])
        
    # Todas las comidas incluyen obligatoriamente Arroz y Frijol (Acompañamiento institucional)
    if m_id >= 11 and m_id <= 20:
        recetas_data.extend([[m_id, "Arroz", 50.0], [m_id, "Frijol", 50.0], [m_id, "Jitomate", 40.0]])
        if m_id in [11, 13, 15, 18, 20]:
            recetas_data.append([m_id, "Res (Bisteck)", 120.0])
        else:
            recetas_data.append([m_id, "Pollo (Pechuga)", 120.0])
            
    # Todas las cenas
    if m_id >= 21 and m_id <= 30:
        if m_id in [21, 22, 27, 28]:
            recetas_data.extend([[m_id, "Queso Oaxaca", 40.0], [m_id, "Tortilla", 40.0]])
        else:
            recetas_data.extend([[m_id, "Jamón de Pavo", 30.0], [m_id, "Tortilla", 50.0]])

df_recetas = pd.DataFrame(recetas_data, columns=['id_menu', 'ingrediente', 'cantidad_por_persona_g_ml'])
df_recetas.to_csv('recetas.csv', index=False)

# ==============================================================================
# 2. PROCESAMIENTO DE LOS 60 DÍAS CONTINUOS
# ==============================================================================
asistencias_list = []
consumo_diario_list = []
salidas_list = []

# Inventario inicial a gran escala para soportar los dos meses
inventario_inicial = {
    "Huevo": 800.0, "Jitomate": 600.0, "Cebolla": 200.0, "Tortilla": 700.0,
    "Arroz": 1000.0, "Frijol": 1000.0, "Res (Bisteck)": 900.0, "Pollo (Pechuga)": 900.0,
    "Jamón de Pavo": 400.0, "Queso Oaxaca": 400.0
}

for dia in range(DIAS_SIMULACION):
    fecha_actual = FECHA_INICIO + timedelta(days=dia)
    fecha_str = fecha_actual.strftime('%Y-%m-%d')
    
    # REGLA: Asistencia Aleatoria (75% - 90%)
    asistencia_hoy = random.randint(75, 90)
    asistentes_ids = random.sample(range(1, POBLACION_TOTAL + 1), asistencia_hoy)
    
    for c_id in range(1, POBLACION_TOTAL + 1):
        estatus = 1 if c_id in asistentes_ids else 0
        asistencias_list.append([fecha_str, c_id, estatus])
        
    # REGLA: Rotación matemática de menús (1 al 10 para cada tiempo)
    # Ejemplo: Dia 0 -> Desayuno 1, Comida 11, Cena 21. Dia 1 -> Desayuno 2, Comida 12, Cena 22...
    id_des = (dia % 10) + 1
    id_com = (dia % 10) + 11
    id_cen = (dia % 10) + 21
    
    c_des = df_menus.loc[df_menus['id_menu'] == id_des, 'costo_porcion_mayoreo'].values[0]
    c_com = df_menus.loc[df_menus['id_menu'] == id_com, 'costo_porcion_mayoreo'].values[0]
    c_cen = df_menus.loc[df_menus['id_menu'] == id_cen, 'costo_porcion_mayoreo'].values[0]
    
    costo_total_dia = (c_des + c_com + c_cen) * asistencia_hoy
    kcal_totales = int(df_menus.loc[df_menus['id_menu'].isin([id_des, id_com, id_cen]), 'total_kcal'].sum())
    
    consumo_diario_list.append([fecha_str, asistencia_hoy, id_des, id_com, id_cen, round(costo_total_dia, 2), kcal_totales])
    
    # Procesar Almacén e Ingredientes
    ingredientes_hoy = df_recetas[df_recetas['id_menu'].isin([id_des, id_com, id_cen])]
    
    for idx, row in ingredientes_hoy.iterrows():
        ing = row['ingrediente']
        gramos_base = row['cantidad_por_persona_g_ml']
        
        # Efecto Cucharón individual (±5%)
        total_consumo_neto_g = sum(gramos_base * random.uniform(0.95, 1.05) for _ in range(asistencia_hoy))
        total_consumo_neto_kg = total_consumo_neto_g / 1000.0
        
        # Merma Operativa (2% al 5%)
        porcentaje_merma = random.uniform(0.02, 0.05)
        cantidad_merma_kg = total_consumo_neto_kg * porcentaje_merma
        total_retirado_almacen_kg = total_consumo_neto_kg + cantidad_merma_kg
        
        salidas_list.append([
            fecha_str, ing, 
            round(total_consumo_neto_kg, 2), 
            round(cantidad_merma_kg, 2), 
            round(total_retirado_almacen_kg, 2)
        ])
        
        if ing in inventario_inicial:
            inventario_inicial[ing] -= total_retirado_almacen_kg

# Escribir los resultados en archivos CSV de gran escala
pd.DataFrame(asistencias_list, columns=['fecha', 'id_comensal', 'asistio']).to_csv('asistencia_historica.csv', index=False)
pd.DataFrame(consumo_diario_list, columns=['fecha', 'asistencia_total', 'id_desayuno', 'id_comida', 'id_cena', 'costo_total_dia', 'kcal_totales_dia']).to_csv('consumo_diario.csv', index=False)
pd.DataFrame(salidas_list, columns=['fecha', 'ingrediente', 'cantidad_neta_consumida_kg', 'cantidad_merma_kg', 'total_retirado_almacen_kg']).to_csv('salidas.csv', index=False)

inventario_rows = [[i+1, ing, round(max(0.0, disp), 2), 40.0] for i, (ing, disp) in enumerate(inventario_inicial.items())]
pd.DataFrame(inventario_rows, columns=['ID', 'Nombre', 'Cantidad_Disponible', 'Stock_Minimo']).to_csv('inventario.csv', index=False)

print("🎯 ¡Simulación macro-operativa completada con éxito!")
print("💾 Los archivos CSV han sido actualizados con el historial completo de 60 días.")