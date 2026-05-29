import sqlite3
import os

DB_NAME = "comedor.db"

def inicializar_infraestructura_seguridad():
    print(f"⚙️ Iniciando construcción de la base de datos relacional: '{DB_NAME}'...")
    
    # Establecer conexión con el motor SQLite (si el archivo no existe, lo crea automáticamente)
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # --------------------------------------------------------------------------
    # TABLA 1: USUARIOS (CONTROL DE ACCESO DE PERSONAL)
    # --------------------------------------------------------------------------
    print("🔨 Creando estructura para la tabla 'usuarios'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL,
            estado INTEGER NOT NULL DEFAULT 1
        );
    """)
    
    # --------------------------------------------------------------------------
    # TABLA 2: BITÁCORA DE ACTIVIDADES (AUDITORÍA HISTÓRICA IMBORRABLE)
    # --------------------------------------------------------------------------
    print("🔨 Creando estructura para la tabla 'bitacora_actividades'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_actividades (
            id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modulo TEXT NOT NULL,
            accion TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario)
        );
    """)
    
    # Guardar los cambios estructurales en el archivo físico y cerrar conexión
    conexion.commit()
    conexion.close()
    
    print(f"✅ ¡Base de datos '{DB_NAME}' e infraestructura de seguridad creadas con éxito!")

if __name__ == "__main__":
    inicializar_infraestructura_seguridad()