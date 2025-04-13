import sqlite3

# Conexão com SQLite
def get_db():
    conn = sqlite3.connect("stock.db")
    conn.row_factory = sqlite3.Row
    return conn

# Criação das tabelas
def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        qty INTEGER NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER,
        product_id INTEGER,
        qty INTEGER,
        FOREIGN KEY(supplier_id) REFERENCES suppliers(id),
        FOREIGN KEY(product_id) REFERENCES products(id))''')
    conn.commit()
    conn.close()

