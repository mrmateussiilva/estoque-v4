from pydantic import BaseModel




class Product(BaseModel):
    name: str
    qty: int
    price: float
    category: str

class Supplier(BaseModel):
    name: str
    contact: str

class StockEntry(BaseModel):
    product_id: int
    qty: int

class Order(BaseModel):
    supplier_id: int
    product_id: int
    qty: int