import shutil
import sqlite3
from main import init_db, DB_SQLITE

PRODUCTOS_50 = [
    ("Laptop Lenovo", "Computadoras", 750.00, 10),
    ("Laptop HP", "Computadoras", 820.00, 8),
    ("Laptop Dell", "Computadoras", 900.00, 6),
    ("Laptop Asus", "Computadoras", 680.00, 12),
    ("Laptop Acer", "Computadoras", 620.00, 5),
    ("Monitor Samsung 24", "Computadoras", 180.00, 15),
    ("Monitor LG 27", "Computadoras", 250.00, 9),
    ("Mini PC Intel", "Computadoras", 420.00, 7),
    ("Memoria RAM 16 GB", "Computadoras", 65.00, 25),
    ("Disco SSD 1 TB", "Computadoras", 95.00, 20),
    ("Teclado Logitech", "Periféricos", 28.00, 30),
    ("Mouse Logitech", "Periféricos", 18.00, 40),
    ("Teclado mecánico", "Periféricos", 75.00, 12),
    ("Mouse gamer", "Periféricos", 45.00, 14),
    ("Webcam HD", "Periféricos", 55.00, 10),
    ("Audífonos USB", "Periféricos", 35.00, 18),
    ("Micrófono USB", "Periféricos", 85.00, 4),
    ("Impresora Epson", "Periféricos", 230.00, 6),
    ("Escáner Canon", "Periféricos", 190.00, 3),
    ("Proyector Epson", "Periféricos", 580.00, 2),
    ("Disco HDD 1 TB", "Almacenamiento", 52.00, 18),
    ("Disco HDD 2 TB", "Almacenamiento", 78.00, 14),
    ("SSD SATA 500 GB", "Almacenamiento", 45.00, 24),
    ("SSD NVMe 2 TB", "Almacenamiento", 160.00, 8),
    ("Memoria USB 32 GB", "Almacenamiento", 11.00, 50),
    ("Memoria USB 64 GB", "Almacenamiento", 16.00, 40),
    ("MicroSD 128 GB", "Almacenamiento", 24.00, 22),
    ("Disco externo 2 TB", "Almacenamiento", 115.00, 10),
    ("NAS 2 bahías", "Almacenamiento", 320.00, 3),
    ("Lector de tarjetas", "Almacenamiento", 14.00, 27),
    ("Router TP-Link", "Redes", 65.00, 17),
    ("Switch 8 puertos", "Redes", 45.00, 15),
    ("Switch 24 puertos", "Redes", 210.00, 4),
    ("Access Point WiFi", "Redes", 120.00, 9),
    ("Cable UTP 5 m", "Redes", 8.00, 60),
    ("Cable UTP 10 m", "Redes", 13.00, 40),
    ("Patch Panel 24", "Redes", 95.00, 6),
    ("Rack 12U", "Redes", 280.00, 3),
    ("Adaptador USB WiFi", "Redes", 22.00, 25),
    ("Firewall compacto", "Redes", 480.00, 2),
    ("UPS 1000 VA", "Accesorios", 165.00, 7),
    ("Regleta eléctrica", "Accesorios", 22.00, 35),
    ("Adaptador HDMI", "Accesorios", 15.00, 28),
    ("Cable HDMI 2 m", "Accesorios", 12.00, 50),
    ("Hub USB", "Accesorios", 32.00, 19),
    ("Base refrigerante", "Accesorios", 39.00, 11),
    ("Mochila laptop", "Accesorios", 48.00, 16),
    ("Soporte monitor", "Accesorios", 55.00, 9),
    ("Mouse pad", "Accesorios", 10.00, 42),
    ("Organizador de cables", "Accesorios", 9.00, 38),
]

def cargar():
    init_db()
    conn = sqlite3.connect(DB_SQLITE)
    cursor = conn.cursor()
    insertados = 0
    for nombre, categoria, precio, stock in PRODUCTOS_50:
        try:
            cursor.execute(
                "INSERT INTO productos (nombre, categoria, precio, stock) VALUES (?, ?, ?, ?)",
                (nombre, categoria, precio, stock)
            )
            insertados += 1
        except sqlite3.IntegrityError:
            print(f"Omitido (ya existe): {nombre}")
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM productos")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT categoria, COUNT(*) FROM productos GROUP BY categoria")
    categorias = cursor.fetchall()
    conn.close()

    print(f"Registros nuevos insertados: {insertados}")
    print(f"Total actual en {DB_SQLITE}: {total} productos")
    print("Distribución por categoría:", categorias)

    if total == 50:
        shutil.copyfile(DB_SQLITE, "tienda_original_50.db")
        print("Respaldo creado: tienda_original_50.db (50 registros intactos).")

if __name__ == "__main__":
    cargar()