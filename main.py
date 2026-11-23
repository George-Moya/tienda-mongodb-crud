import os
import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Taller Integrador - Inventario FastAPI (SQLite + MongoDB)",
    description="API REST para CRUD de 50 productos, reportes SQL y migración a MongoDB"
)

DB_SQLITE = "tienda.db"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB", "tienda")

class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    categoria: str = Field(..., min_length=1)
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    categoria: Optional[str] = Field(None, min_length=1)
    precio: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)

def get_sqlite_conn():
    conn = sqlite3.connect(DB_SQLITE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL CHECK(precio > 0),
            stock INTEGER NOT NULL CHECK(stock >= 0)
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_mongo_collection():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client[MONGO_DB_NAME]
    return client, db["productos"]

# --- ACTIVIDAD 1 Y 2: CRUD SQLITE ---
@app.post("/productos", status_code=201, tags=["1. CRUD SQLite"])
def crear_producto(producto: ProductoCreate):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO productos (nombre, categoria, precio, stock) VALUES (?, ?, ?, ?)",
            (producto.nombre.strip(), producto.categoria.strip(), producto.precio, producto.stock)
        )
        conn.commit()
        return {"mensaje": "Producto registrado", "id": cursor.lastrowid, **producto.model_dump()}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail=f"El producto '{producto.nombre}' ya existe.")
    finally:
        conn.close()

@app.get("/productos", tags=["1. CRUD SQLite"])
def listar_productos():
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY id ASC")
    filas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"total": len(filas), "productos": filas}

@app.get("/productos/{producto_id}", tags=["1. CRUD SQLite"])
def obtener_producto(producto_id: int):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    fila = cursor.fetchone()
    conn.close()
    if not fila:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return dict(fila)

@app.put("/productos/{producto_id}", tags=["1. CRUD SQLite"])
def actualizar_producto(producto_id: int, datos: ProductoUpdate):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    actual = cursor.fetchone()
    if not actual:
        conn.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    nuevo_nombre = datos.nombre.strip() if datos.nombre is not None else actual["nombre"]
    nueva_categoria = datos.categoria.strip() if datos.categoria is not None else actual["categoria"]
    nuevo_precio = datos.precio if datos.precio is not None else actual["precio"]
    nuevo_stock = datos.stock if datos.stock is not None else actual["stock"]

    cursor.execute(
        "UPDATE productos SET nombre = ?, categoria = ?, precio = ?, stock = ? WHERE id = ?",
        (nuevo_nombre, nueva_categoria, nuevo_precio, nuevo_stock, producto_id)
    )
    conn.commit()
    conn.close()
    return {
        "mensaje": "Producto actualizado",
        "antes": dict(actual),
        "despues": {
            "id": producto_id,
            "nombre": nuevo_nombre,
            "categoria": nueva_categoria,
            "precio": nuevo_precio,
            "stock": nuevo_stock
        }
    }

@app.delete("/productos/{producto_id}", tags=["1. CRUD SQLite"])
def eliminar_producto(producto_id: int):
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    fila = cursor.fetchone()
    if not fila:
        conn.close()
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Producto eliminado", "producto_eliminado": dict(fila)}

# --- ACTIVIDAD 3: REPORTES SQL ---
@app.get("/reportes/resumen", tags=["2. Reportes SQL"])
def reportes_inventario():
    conn = get_sqlite_conn()
    cursor = conn.cursor()

    sql_mayor = "SELECT * FROM productos ORDER BY precio DESC LIMIT 1"
    cursor.execute(sql_mayor)
    mayor_precio = dict(cursor.fetchone())

    sql_menor = "SELECT * FROM productos ORDER BY precio ASC LIMIT 1"
    cursor.execute(sql_menor)
    menor_precio = dict(cursor.fetchone())

    sql_stock_bajo = "SELECT * FROM productos WHERE stock < 5 ORDER BY stock ASC"
    cursor.execute(sql_stock_bajo)
    stock_bajo = [dict(r) for r in cursor.fetchall()]

    sql_valor_total = "SELECT ROUND(SUM(precio * stock), 2) AS valor_total FROM productos"
    cursor.execute(sql_valor_total)
    valor_total = cursor.fetchone()["valor_total"]

    sql_por_categoria = """
        SELECT categoria, COUNT(*) AS cantidad_productos, SUM(stock) AS unidades_totales
        FROM productos
        GROUP BY categoria
    """
    cursor.execute(sql_por_categoria)
    por_categoria = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "1_producto_mayor_precio": {"sql": sql_mayor, "resultado": mayor_precio},
        "2_producto_menor_precio": {"sql": sql_menor, "resultado": menor_precio},
        "3_stock_inferior_a_5": {"sql": sql_stock_bajo, "cantidad": len(stock_bajo), "resultado": stock_bajo},
        "4_valor_total_inventario_usd": {"sql": sql_valor_total, "resultado": valor_total},
        "5_productos_por_categoria": {"sql": sql_por_categoria.strip(), "resultado": por_categoria}
    }

# --- ACTIVIDAD 4 Y 5: MONGODB ---
@app.get("/mongo/ping", tags=["3. MongoDB"])
def verificar_conexion_mongo():
    try:
        client, _ = get_mongo_collection()
        resultado = client.admin.command("ping")
        client.close()
        return {"estado": "Conectado a MongoDB", "base_datos": MONGO_DB_NAME, "ping": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")

@app.get("/mongo/productos", tags=["3. MongoDB"])
def listar_productos_mongo():
    client, col = get_mongo_collection()
    docs = list(col.find({}, {"_id": 0}).sort("id_origen", 1))
    client.close()
    return {"total_en_mongo": len(docs), "productos": docs}

@app.post("/mongo/productos", status_code=201, tags=["3. MongoDB"])
def insertar_producto_mongo(producto: ProductoCreate):
    client, col = get_mongo_collection()
    if col.find_one({"nombre": producto.nombre.strip()}):
        client.close()
        raise HTTPException(status_code=400, detail="El producto ya existe en MongoDB")
    ultimo = col.find_one(sort=[("id_origen", -1)])
    siguiente_id = (ultimo["id_origen"] + 1) if ultimo and "id_origen" in ultimo else 1
    nuevo_doc = {
        "id_origen": siguiente_id,
        "nombre": producto.nombre.strip(),
        "categoria": producto.categoria.strip(),
        "precio": producto.precio,
        "stock": producto.stock
    }
    col.insert_one(nuevo_doc)
    nuevo_doc.pop("_id", None)
    client.close()
    return {"mensaje": "Producto insertado en MongoDB", "producto": nuevo_doc}