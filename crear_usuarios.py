import sqlite3
import hashlib

DB_NAME = "comedor.db"

def encriptar_password(password):
    """Aplica el algoritmo criptográfico SHA-256 a una contraseña de texto plano."""
    # Convierte el texto a bytes y genera el hash
    hash_object = hashlib.sha256(password.encode())
    # Retorna el hash como una cadena de texto alfanumérica legible
    return hash_object.hexdigest()

def inyectar_usuarios_semilla():
    print("🔑 Iniciando proceso de encriptación e inyección de cuentas maestras...")
    
    # Verificar si la base de datos existe
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()
    
    # Lista de usuarios de prueba con sus respectivos roles y contraseñas iniciales
    usuarios_por_crear = [
        ("admin", "admin123", "Administrador"),
        ("despensero", "despensa123", "Despensero"),
        ("cocina", "cocina123", "Cocina"),
        ("supervisor", "super123", "Supervisor")
    ]
    
    for username, password_plana, rol in usuarios_por_crear:
        # Pasamos la contraseña por nuestro motor criptográfico antes de guardarla
        password_segura = encriptar_password(password_plana)
        
        try:
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, rol, estado)
                VALUES (?, ?, ?, 1);
            """, (username, password_segura, rol))
            print(f"✅ Usuario '{username}' registrado exitosamente bajo el rol [{rol}].")
        except sqlite3.IntegrityError:
            print(f"⚠️ El usuario '{username}' ya existe en la base de datos. Saltando registro.")
            
    conexion.commit()
    conexion.close()
    print("🎯 ¡Proceso de inicialización de credenciales completado con éxito!")

if __name__ == "__main__":
    inyectar_usuarios_semilla()