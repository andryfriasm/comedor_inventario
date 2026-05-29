import pandas as pd
import sqlite3
import os

DB_NAME = "comedor.db"
ARCHIVO_RECETAS = "recetas.csv"

def inicializar_sistema_raciones():
    print("🚀 Inicializando estructuras para el modelo de raciones automatizado...")

    # 1. Crear el catálogo de recetas estándar (CSV)
    # Define cuántos kilogramos o unidades de cada insumo se requieren para UNA SOLA RACIÓN (1 persona)
    # Los IDs de los insumos deben coincidir con los de tu catálogo actual
    columnas_recetas = ['id_receta', 'nombre_platillo', 'id_insumo', 'nombre_insumo', 'porcion_por_persona_kg_u']
    
    recetas_data = [
        # Menú 1: Milanesa de Pollo con Arroz (Insumos ID 1, 2, 3 de ejemplo)
        [1, "Milanesa de Pollo con Arroz", 1, "Pechuga de Pollo", 0.150],  # 150 gramos por persona
        [1, "Milanesa de Pollo con Arroz", 2, "Arroz Blanco", 0.080],      # 80 gramos por persona
        [1, "Milanesa de Pollo con Arroz", 3, "Aceite Vegetal", 0.015],    # 15 mililitros/gramos por persona
        
        # Menú 2: Picadillo de Res con Verduras
        [2, "Picadillo de Res", 4, "Carne Molida de Res", 0.120],
        [2, "Picadillo de Res", 5, "Papa", 0.050],
        [2, "Picadillo de Res", 6, "Zanahoria", 0.040],
        
        # Menú 3: Chilaquiles con Huevo y Frijoles
        [3, "Chilaquiles con Huevo", 7, "Tortilla de Maíz", 0.100],
        [3, "Chilaquiles con Huevo", 8, "Huevo", 0.120],                   # ~2 piezas
        [3, "Chilaquiles con Huevo", 9, "Frijol Negro", 0.060]
    ]
    
    df_recetas = pd.DataFrame(recetas_data, columns=columnas_recetas)
    df_recetas.to_csv(ARCHIVO_RECETAS, index=False)
    print(f"✔️ Catálogo de recetas estándar creado con éxito en '{ARCHIVO_RECETAS}'.")

    # 2. Crear la tabla de conciliación y control de servicio en SQLite
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Crear tabla de confirmaciones simuladas de Telegram si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confirmaciones_telegram (
            id_confirmacion INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            id_empleado TEXT NOT NULL,
            tipo_comida TEXT NOT NULL,
            asistira INTEGER DEFAULT 1
        );
    """)
    
    # Insertar datos de prueba para el día de hoy en Telegram (Simulación de 85 confirmados)
    cursor.execute("DELETE FROM confirmaciones_telegram WHERE fecha = date('now');")
    for i in range(85):
        cursor.execute("""
            INSERT INTO confirmaciones_telegram (fecha, id_empleado, tipo_comida)
            VALUES (date('now'), ?, 'Comida');
        """, (f"EMP_{1000+i}",))

    # Crear la tabla reina del control de desperdicios e indicadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS control_servicio_diario (
            id_servicio INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            tipo_comida TEXT NOT NULL,
            menu_asignado TEXT NOT NULL,
            confirmados_telegram INTEGER NOT NULL,
            raciones_planeadas INTEGER NOT NULL,
            raciones_reales_preparadas INTEGER,
            raciones_servidas_reales INTEGER,
            raciones_sobrantes INTEGER,
            raciones_faltantes INTEGER,
            produccion_emergencia INTEGER DEFAULT 0,
            hora_inicio TEXT,
            hora_cierre TEXT,
            comentarios TEXT,
            usuario_cierre TEXT,
            estado_servicio TEXT DEFAULT 'PLANEADO' -- PLANEADO, PREPARADO, CERRADO
        );
    """)
    
    conexion.commit()
    conexion.close()
    print("✔️ Tabla 'control_servicio_diario' integrada y poblada con confirmaciones de prueba de Telegram.")

if __name__ == "__main__":
    inicializar_sistema_raciones()