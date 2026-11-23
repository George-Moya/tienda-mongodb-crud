import os
import sqlite3
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

SQLITE_ORIGEN = "tienda_original_50.db"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "tienda")

def migrar_y_verificar():
    conn = sqlite3.connect(SQLITE_ORIGEN)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY id ASC")
    registros_sqlite = [dict(row) for row in cursor.fetchall()]
    conn.close()

    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    coleccion = db["productos"]
    coleccion.create_index("id_origen", unique=True)

    for reg in registros_sqlite:
        documento = {
            "id_origen": reg["id"],
            "nombre": reg["nombre"],
            "categoria": reg["categoria"],
            "precio": reg["precio"],
            "stock": reg["stock"]
        }
        coleccion.update_one({"id_origen": reg["id"]}, {"$set": documento}, upsert=True)

    total_sqlite = len(registros_sqlite)
    total_mongo = coleccion.count_documents({})
    print(f"Conteo SQLite ({SQLITE_ORIGEN}): {total_sqlite} registros")
    print(f"Conteo MongoDB ({MONGO_DB}.productos): {total_mongo} documentos\n")

    ids_prueba = [1, 15, 25, 35, 45]
    print("--- COMPARACIÓN DE 5 REGISTROS EQUIVALENTES ---")
    for pid in ids_prueba:
        orig = next(r for r in registros_sqlite if r["id"] == pid)
        dest = coleccion.find_one({"id_origen": pid}, {"_id": 0})
        print(f"ID {pid}:")
        print(f"  SQLite  -> {orig}")
        print(f"  MongoDB -> {dest}")

    client.close()

if __name__ == "__main__":
    migrar_y_verificar()