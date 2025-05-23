from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
from urllib.parse import quote_plus
from datetime import datetime

password = quote_plus("MJs119629@03770")
SQLALCHEMY_DATABASE_URL = f'mysql+pymysql://mateusfinderbit:{password}@estoquesilkart.mysql.uhserver.com/estoquesilkart'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI app
app = FastAPI(title="Estoque API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database models
class TintaDB(Base):
    __tablename__ = "tintas"
    id = Column(Integer, primary_key=True, index=True)
    color = Column(String(255), index=True)
    type = Column(String(255))
    productQty = Column(Integer)
    productQtyLitros = Column(Float)
    qtyMin = Column(Float, nullable=True)

class PapelDB(Base):
    __tablename__ = "papeis"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255), index=True)
    qtyUnit = Column(Integer)
    qtyMetros = Column(Integer)
    qtyMin = Column(Float, nullable=True)

class TecidoDB(Base):
    __tablename__ = "tecidos"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255), index=True)
    qtyMetros = Column(Float)
    width = Column(Float)
    qtyMin = Column(Float, nullable=True)

class TecidoCortadoDB(Base):
    __tablename__ = "tecidos_cortados"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255), index=True)
    quantity = Column(Integer)
    measurement = Column(String(50))
    qtyMin = Column(Float, nullable=True)

class SupplierDB(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    phone = Column(String(50))
    email = Column(String(255))

class EntryDB(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50))  # "tinta", "papel", "tecido", "tecido-cortado"
    product_id = Column(Integer, index=True)
    quantity = Column(Float)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    date = Column(DateTime, default=datetime.utcnow)

class ExitDB(Base):
    __tablename__ = "exits"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50))  # "tinta", "papel", "tecido", "tecido-cortado"
    product_id = Column(Integer, index=True)
    quantity = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models for validation
class TintaCreate(BaseModel):
    color: str
    type: str
    productQty: int
    productQtyLitros: float
    qtyMin: Optional[float] = 0

class PapelCreate(BaseModel):
    type: str
    qtyUnit: int
    qtyMetros: int
    qtyMin: Optional[float] = 0

class TecidoCreate(BaseModel):
    type: str
    qtyMetros: float
    width: float
    qtyMin: Optional[float] = 0

class TecidoCortadoCreate(BaseModel):
    type: str
    quantity: int
    measurement: str
    qtyMin: Optional[float] = 0

class SupplierCreate(BaseModel):
    name: str
    phone: str
    email: str

class EntryCreate(BaseModel):
    category: str
    product_id: int
    quantity: float
    supplier_id: int

class ExitCreate(BaseModel):
    category: str
    product_id: int
    quantity: float

class TintaResponse(TintaCreate):
    id: int
    class Config:
        orm_mode = True

class PapelResponse(PapelCreate):
    id: int
    class Config:
        orm_mode = True

class TecidoResponse(TecidoCreate):
    id: int
    class Config:
        orm_mode = True

class TecidoCortadoResponse(TecidoCortadoCreate):
    id: int
    class Config:
        orm_mode = True

class SupplierResponse(SupplierCreate):
    id: int
    class Config:
        orm_mode = True

class EntryResponse(EntryCreate):
    id: int
    date: datetime
    class Config:
        orm_mode = True

class ExitResponse(ExitCreate):
    id: int
    date: datetime
    class Config:
        orm_mode = True

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to update stock
async def update_stock(db: Session, category: str, product_id: int, quantity: float, is_entry: bool):
    if category == "tinta":
        product = db.query(TintaDB).filter(TintaDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Tinta not found")
        if is_entry:
            product.productQty += int(quantity)
        else:
            if product.productQty < quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock for tinta")
            product.productQty -= int(quantity)
    elif category == "papel":
        product = db.query(PapelDB).filter(PapelDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Papel not found")
        if is_entry:
            product.qtyUnit += int(quantity)
        else:
            if product.qtyUnit < quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock for papel")
            product.qtyUnit -= int(quantity)
    elif category == "tecido":
        product = db.query(TecidoDB).filter(TecidoDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Tecido not found")
        if is_entry:
            product.qtyMetros += quantity
        else:
            if product.qtyMetros < quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock for tecido")
            product.qtyMetros -= quantity
    elif category == "tecido-cortado":
        product = db.query(TecidoCortadoDB).filter(TecidoCortadoDB.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Tecido Cortado not found")
        if is_entry:
            product.quantity += int(quantity)
        else:
            if product.quantity < quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock for tecido cortado")
            product.quantity -= int(quantity)
    else:
        raise HTTPException(status_code=400, detail="Invalid category")
    db.commit()

# Tinta endpoints
@app.post("/products-tinta", response_model=TintaResponse, status_code=201)
async def create_tinta(tinta: TintaCreate, db: Session = Depends(get_db)):
    if not tinta.color.strip():
        raise HTTPException(status_code=400, detail="Color is required")
    if not tinta.type.strip():
        raise HTTPException(status_code=400, detail="Type is required")
    if tinta.productQty <= 0:
        raise HTTPException(status_code=400, detail="productQty must be positive")
    if tinta.productQtyLitros <= 0:
        raise HTTPException(status_code=400, detail="productQtyLitros must be positive")
    if tinta.qtyMin < 0:
        raise HTTPException(status_code=400, detail="qtyMin cannot be negative")

    db_tinta = TintaDB(**tinta.dict())
    db.add(db_tinta)
    db.commit()
    db.refresh(db_tinta)
    return db_tinta

@app.get("/products-tinta", response_model=list[TintaResponse])
async def get_tintas(db: Session = Depends(get_db)):
    return db.query(TintaDB).all()

@app.get("/products-tinta/{id}", response_model=TintaResponse)
async def get_tinta(id: int, db: Session = Depends(get_db)):
    tinta = db.query(TintaDB).filter(TintaDB.id == id).first()
    if not tinta:
        raise HTTPException(status_code=404, detail="Tinta not found")
    return tinta

@app.put("/products-tinta/{id}", response_model=TintaResponse)
async def update_tinta(id: int, tinta: TintaCreate, db: Session = Depends(get_db)):
    db_tinta = db.query(TintaDB).filter(TintaDB.id == id).first()
    if not db_tinta:
        raise HTTPException(status_code=404, detail="Tinta not found")
    for key, value in tinta.dict().items():
        setattr(db_tinta, key, value)
    db.commit()
    db.refresh(db_tinta)
    return db_tinta

@app.delete("/products-tinta/{id}", status_code=204)
async def delete_tinta(id: int, db: Session = Depends(get_db)):
    tinta = db.query(TintaDB).filter(TintaDB.id == id).first()
    if not tinta:
        raise HTTPException(status_code=404, detail="Tinta not found")
    db.delete(tinta)
    db.commit()
    return None

# Papel endpoints
@app.post("/products-papel", response_model=PapelResponse, status_code=201)
async def create_papel(papel: PapelCreate, db: Session = Depends(get_db)):
    if not papel.type.strip():
        raise HTTPException(status_code=400, detail="Type is required")
    if papel.qtyUnit <= 0:
        raise HTTPException(status_code=400, detail="qtyUnit must be positive")
    if papel.qtyMetros <= 0:
        raise HTTPException(status_code=400, detail="qtyMetros must be positive")
    if papel.qtyMin < 0:
        raise HTTPException(status_code=400, detail="qtyMin cannot be negative")

    db_papel = PapelDB(**papel.dict())
    db.add(db_papel)
    db.commit()
    db.refresh(db_papel)
    return db_papel

@app.get("/products-papel", response_model=list[PapelResponse])
async def get_papeis(db: Session = Depends(get_db)):
    return db.query(PapelDB).all()

@app.get("/products-papel/{id}", response_model=PapelResponse)
async def get_papel(id: int, db: Session = Depends(get_db)):
    papel = db.query(PapelDB).filter(PapelDB.id == id).first()
    if not papel:
        raise HTTPException(status_code=404, detail="Papel not found")
    return papel

@app.put("/products-papel/{id}", response_model=PapelResponse)
async def update_papel(id: int, papel: PapelCreate, db: Session = Depends(get_db)):
    db_papel = db.query(PapelDB).filter(PapelDB.id == id).first()
    if not db_papel:
        raise HTTPException(status_code=404, detail="Papel not found")
    for key, value in papel.dict().items():
        setattr(db_papel, key, value)
    db.commit()
    db.refresh(db_papel)
    return db_papel

@app.delete("/products-papel/{id}", status_code=204)
async def delete_papel(id: int, db: Session = Depends(get_db)):
    papel = db.query(PapelDB).filter(PapelDB.id == id).first()
    if not papel:
        raise HTTPException(status_code=404, detail="Papel not found")
    db.delete(papel)
    db.commit()
    return None

# Tecido endpoints
@app.post("/products-tecido", response_model=TecidoResponse, status_code=201)
async def create_tecido(tecido: TecidoCreate, db: Session = Depends(get_db)):
    if not tecido.type.strip():
        raise HTTPException(status_code=400, detail="Type is required")
    if tecido.qtyMetros <= 0:
        raise HTTPException(status_code=400, detail="qtyMetros must be positive")
    if tecido.width <= 0:
        raise HTTPException(status_code=400, detail="width must be positive")
    if tecido.qtyMin < 0:
        raise HTTPException(status_code=400, detail="qtyMin cannot be negative")

    db_tecido = TecidoDB(**tecido.dict())
    db.add(db_tecido)
    db.commit()
    db.refresh(db_tecido)
    return db_tecido

@app.get("/products-tecido", response_model=list[TecidoResponse])
async def get_tecidos(db: Session = Depends(get_db)):
    return db.query(TecidoDB).all()

@app.get("/products-tecido/{id}", response_model=TecidoResponse)
async def get_tecido(id: int, db: Session = Depends(get_db)):
    tecido = db.query(TecidoDB).filter(TecidoDB.id == id).first()
    if not tecido:
        raise HTTPException(status_code=404, detail="Tecido not found")
    return tecido

@app.put("/products-tecido/{id}", response_model=TecidoResponse)
async def update_tecido(id: int, tecido: TecidoCreate, db: Session = Depends(get_db)):
    db_tecido = db.query(TecidoDB).filter(TecidoDB.id == id).first()
    if not db_tecido:
        raise HTTPException(status_code=404, detail="Tecido not found")
    for key, value in tecido.dict().items():
        setattr(db_tecido, key, value)
    db.commit()
    db.refresh(db_tecido)
    return db_tecido

@app.delete("/products-tecido/{id}", status_code=204)
async def delete_tecido(id: int, db: Session = Depends(get_db)):
    tecido = db.query(TecidoDB).filter(TecidoDB.id == id).first()
    if not tecido:
        raise HTTPException(status_code=404, detail="Tecido not found")
    db.delete(tecido)
    db.commit()
    return None

# Tecido Cortado endpoints
@app.post("/products-tecido-cortado", response_model=TecidoCortadoResponse, status_code=201)
async def create_tecido_cortado(tecido_cortado: TecidoCortadoCreate, db: Session = Depends(get_db)):
    if not tecido_cortado.type.strip():
        raise HTTPException(status_code=400, detail="Type is required")
    if tecido_cortado.type.lower() not in ["malha", "tactel"]:
        raise HTTPException(status_code=400, detail="Type must be 'malha' or 'tactel'")
    if tecido_cortado.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be positive")
    if not tecido_cortado.measurement.strip():
        raise HTTPException(status_code=400, detail="measurement is required")
    if not tecido_cortado.measurement.count('x') == 1:
        raise HTTPException(status_code=400, detail="measurement must be in format 'widthxheight'")
    try:
        width, height = map(float, tecido_cortado.measurement.split('x'))
        if width <= 0 or height <= 0:
            raise HTTPException(status_code=400, detail="width and height must be positive")
    except ValueError:
        raise HTTPException(status_code=400, detail="measurement must be in format 'widthxheight' with numeric values")
    if tecido_cortado.qtyMin < 0:
        raise HTTPException(status_code=400, detail="qtyMin cannot be negative")

    db_tecido_cortado = TecidoCortadoDB(**tecido_cortado.dict())
    db.add(db_tecido_cortado)
    db.commit()
    db.refresh(db_tecido_cortado)
    return db_tecido_cortado

@app.get("/products-tecido-cortado", response_model=list[TecidoCortadoResponse])
async def get_tecidos_cortados(db: Session = Depends(get_db)):
    return db.query(TecidoCortadoDB).all()

@app.get("/products-tecido-cortado/{id}", response_model=TecidoCortadoResponse)
async def get_tecido_cortado(id: int, db: Session = Depends(get_db)):
    tecido_cortado = db.query(TecidoCortadoDB).filter(TecidoCortadoDB.id == id).first()
    if not tecido_cortado:
        raise HTTPException(status_code=404, detail="Tecido Cortado not found")
    return tecido_cortado

@app.put("/products-tecido-cortado/{id}", response_model=TecidoCortadoResponse)
async def update_tecido_cortado(id: int, tecido_cortado: TecidoCortadoCreate, db: Session = Depends(get_db)):
    db_tecido_cortado = db.query(TecidoCortadoDB).filter(TecidoCortadoDB.id == id).first()
    if not db_tecido_cortado:
        raise HTTPException(status_code=404, detail="Tecido Cortado not found")
    if not tecido_cortado.type.strip():
        raise HTTPException(status_code=400, detail="Type is required")
    if tecido_cortado.type.lower() not in ["malha", "tactel"]:
        raise HTTPException(status_code=400, detail="Type must be 'malha' or 'tactel'")
    if tecido_cortado.quantity <= 0:
        raise HTTPException(status_code=400, detail="quantity must be positive")
    if not tecido_cortado.measurement.strip():
        raise HTTPException(status_code=400, detail="measurement is required")
    if not tecido_cortado.measurement.count('x') == 1:
        raise HTTPException(status_code=400, detail="measurement must be in format 'widthxheight'")
    try:
        width, height = map(float, tecido_cortado.measurement.split('x'))
        if width <= 0 or height <= 0:
            raise HTTPException(status_code=400, detail="width and height must be positive")
    except ValueError:
        raise HTTPException(status_code=400, detail="measurement must be in format 'widthxheight' with numeric values")
    if tecido_cortado.qtyMin < 0:
        raise HTTPException(status_code=400, detail="qtyMin cannot be negative")

    for key, value in tecido_cortado.dict().items():
        setattr(db_tecido_cortado, key, value)
    db.commit()
    db.refresh(db_tecido_cortado)
    return db_tecido_cortado

@app.delete("/products-tecido-cortado/{id}", status_code=204)
async def delete_tecido_cortado(id: int, db: Session = Depends(get_db)):
    tecido_cortado = db.query(TecidoCortadoDB).filter(TecidoCortadoDB.id == id).first()
    if not tecido_cortado:
        raise HTTPException(status_code=404, detail="Tecido Cortado not found")
    db.delete(tecido_cortado)
    db.commit()
    return None

# Supplier endpoints
@app.post("/suppliers", response_model=SupplierResponse, status_code=201)
async def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    if not supplier.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    if not supplier.phone.strip():
        raise HTTPException(status_code=400, detail="Phone is required")
    if not supplier.email.strip():
        raise HTTPException(status_code=400, detail="Email is required")

    db_supplier = SupplierDB(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

@app.get("/suppliers", response_model=list[SupplierResponse])
async def get_suppliers(db: Session = Depends(get_db)):
    return db.query(SupplierDB).all()

@app.delete("/suppliers/{id}", status_code=204)
async def delete_supplier(id: int, db: Session = Depends(get_db)):
    supplier = db.query(SupplierDB).filter(SupplierDB.id == id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(supplier)
    db.commit()
    return None

# Entry endpoints
@app.post("/entries", response_model=EntryResponse, status_code=201)
async def create_entry(entry: EntryCreate, db: Session = Depends(get_db)):
    if entry.category not in ["tinta", "papel", "tecido", "tecido-cortado"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    if entry.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    supplier = db.query(SupplierDB).filter(SupplierDB.id == entry.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Update stock
    await update_stock(db, entry.category, entry.product_id, entry.quantity, is_entry=True)

    # Record entry
    db_entry = EntryDB(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

# Exit endpoints
@app.post("/exits", response_model=ExitResponse, status_code=201)
async def create_exit(exit: ExitCreate, db: Session = Depends(get_db)):
    if exit.category not in ["tinta", "papel", "tecido", "tecido-cortado"]:
        raise HTTPException(status_code=400, detail="Invalid category")
    if exit.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    # Update stock
    await update_stock(db, exit.category, exit.product_id, exit.quantity, is_entry=False)

    # Record exit
    db_exit = ExitDB(**exit.dict())
    db.add(db_exit)
    db.commit()
    db.refresh(db_exit)
    return db_exit

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
