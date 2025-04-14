from pydantic import BaseModel,Field




class Product(BaseModel):
    name: str
    qty: int
    price: float
    category: str

class ProductTinta(BaseModel):
    cor: str = Field(alias="color")
    type: str
    qty_unit: int = Field(alias="productQty")
    qty_litros: int = Field(alias="productQtyLitros")

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