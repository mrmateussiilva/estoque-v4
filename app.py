from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db.db import init_db,get_db
from model.base import Order,Product,StockEntry,Supplier


app = FastAPI()

# Configuração de CORS para permitir o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic


# Rotas para produtos
@app.get("/products")
async def get_products():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = [dict(row) for row in c.fetchall()]
    conn.close()
    return products

@app.post("/products")
async def create_product(product: Product):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO products (name, qty, price, category) VALUES (?, ?, ?, ?)",
              (product.name, product.qty, product.price, product.category))
    conn.commit()
    conn.close()
    return {"message": "Produto criado"}

@app.delete("/products/{id}")
async def delete_product(id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Produto removido"}

# Rotas para entrada/saída de estoque
@app.post("/stock/entry")
async def stock_entry(entry: StockEntry):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE products SET qty = qty + ? WHERE id = ?", (entry.qty, entry.product_id))
    conn.commit()
    conn.close()
    return {"message": "Entrada registrada"}

@app.post("/stock/exit")
async def stock_exit(entry: StockEntry):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT qty FROM products WHERE id = ?", (entry.product_id,))
    qty = c.fetchone()["qty"]
    if qty < entry.qty:
        raise HTTPException(status_code=400, detail="Quantidade insuficiente")
    c.execute("UPDATE products SET qty = qty - ? WHERE id = ?", (entry.qty, entry.product_id))
    conn.commit()
    conn.close()
    return {"message": "Saída registrada"}

# Rotas para fornecedores
@app.get("/suppliers")
async def get_suppliers():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM suppliers")
    suppliers = [dict(row) for row in c.fetchall()]
    conn.close()
    return suppliers

@app.post("/suppliers")
async def create_supplier(supplier: Supplier):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO suppliers (name, contact) VALUES (?, ?)", (supplier.name, supplier.contact))
    conn.commit()
    conn.close()
    return {"message": "Fornecedor criado"}

# Rotas para pedidos
@app.post("/orders")
async def create_order(order: Order):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO orders (supplier_id, product_id, qty) VALUES (?, ?, ?)",
              (order.supplier_id, order.product_id, order.qty))
    c.execute("SELECT name, price FROM products WHERE id = ?", (order.product_id,))
    product = dict(c.fetchone())
    c.execute("SELECT name FROM suppliers WHERE id = ?", (order.supplier_id,))
    supplier = dict(c.fetchone())
    conn.commit()
    conn.close()
    return {
        "supplier_name": supplier["name"],
        "product_name": product["name"],
        "total": product["price"] * order.qty
    }

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)
