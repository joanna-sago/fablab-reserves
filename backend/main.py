from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import date, time, datetime
from typing import List, Optional
import uuid

# SQLAlchemy imports
from sqlalchemy import create_engine, Column, String, Date, Time, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- CONFIGURACIÓ DE LA BASE DE DADES ---
# Per a producció, canviaríem aquesta URL per una variable d'entorn (PostgreSQL)
import os

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fablab_reserves.db"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- CONSTANTS DE NEGOCI ---
HORA_OBERTURA = time(9, 0)
HORA_TANCAMENT = time(13, 30)

# --- MODELS DE LA BASE DE DADES (SQLAlchemy) ---
class ReservaDB(Base):
    __tablename__ = "reserves"

    id = Column(String, primary_key=True, index=True)
    usuari_id = Column(String, index=True, nullable=False) # Email o ID d'estudiant
    servei = Column(String, nullable=False)
    data = Column(Date, nullable=False)
    hora_inici = Column(Time, nullable=False)
    hora_fi = Column(Time, nullable=False)

# Creació de les taules
Base.metadata.create_all(bind=engine)

# --- SCHEMAS DE DADES (Pydantic) ---
class ReservaBase(BaseModel):
    usuari_id: str = Field(..., description="Email o codi d'usuari de la UPC")
    servei: str = Field(..., example="Talladora Làser")
    data: date
    hora_inici: time
    hora_fi: time

    @field_validator('data')
    @classmethod
    def validar_data_futura(cls, v: date):
        if v < date.today():
            raise ValueError("No es poden fer reserves per a dates passades.")
        return v

    @field_validator('hora_inici', 'hora_fi')
    @classmethod
    def validar_horari_fablab(cls, v: time):
        if not (HORA_OBERTURA <= v <= HORA_TANCAMENT):
            raise ValueError(f"L'horari del FabLab és de {HORA_OBERTURA} a {HORA_TANCAMENT}")
        return v

class ReservaCreate(ReservaBase):
    pass

class Reserva(ReservaBase):
    id: str

    class Config:
        from_attributes = True

class ReservaRead(BaseModel):
    id: str
    usuari_id: str
    servei: str
    data: date
    hora_inici: time
    hora_fi: time

    class Config:
        from_attributes = True


# --- DEPENDÈNCIES ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- APP API ---
app = FastAPI(
    title="API FabLab UPC Terrassa (Producció)",
    description="Sistema professional de gestió de reserves amb persistència i control de solapaments.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # per desenvolupament
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---

@app.get("/", tags=["Sistema"])
def estat_api():
    return {
        "status": "online",
        "fablab": "UPC Terrassa",
        "horari_limit": "09:00 - 13:30"
    }

@app.get("/reserves", response_model=List[ReservaRead], tags=["Reserves"])
def llistar_reserves(
    servei: Optional[str] = None, 
    data: Optional[date] = None, 
    db: Session = Depends(get_db)
):
    """Llista les reserves amb filtres opcionals."""
    query = db.query(ReservaDB)
    if servei:
        query = query.filter(ReservaDB.servei == servei)
    if data:
        query = query.filter(ReservaDB.data == data)
    return query.all()

@app.post("/reserves", response_model=Reserva, status_code=status.HTTP_201_CREATED, tags=["Reserves"])
def crear_reserva(reserva_in: ReservaCreate, db: Session = Depends(get_db)):
    """
    Crea una reserva comprovant solapaments del MATEIX servei.
    Nota: Un usuari pot fer reserves simultànies de DIFERENTS serveis.
    """
    # 1. Validació bàsica de lògica temporal
    if reserva_in.hora_inici >= reserva_in.hora_fi:
        raise HTTPException(
            status_code=400, 
            detail="L'hora d'inici ha de ser anterior a la de finalització."
        )

    # 2. Detecció de solapaments (Concurrency Control)
    # Busquem si existeix alguna reserva del mateix servei el mateix dia on les hores es creuin
    solapament = db.query(ReservaDB).filter(
        ReservaDB.servei == reserva_in.servei,
        ReservaDB.data == reserva_in.data,
        ReservaDB.hora_inici < reserva_in.hora_fi,
        ReservaDB.hora_fi > reserva_in.hora_inici
    ).first()

    if solapament:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El servei '{reserva_in.servei}' ja està reservat en aquesta franja horària."
        )

    # 3. Creació de la reserva
    db_reserva = ReservaDB(
        id=str(uuid.uuid4()),
        **reserva_in.model_dump()
    )
    
    try:
        db.add(db_reserva)
        db.commit()
        db.refresh(db_reserva)
        return db_reserva
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al desar la reserva a la base de dades.")

@app.delete("/reserves/{reserva_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Reserves"])
def cancel_lar_reserva(reserva_id: str, db: Session = Depends(get_db)):
    """Elimina una reserva del sistema."""
    db_reserva = db.query(ReservaDB).filter(ReservaDB.id == reserva_id).first()
    if not db_reserva:
        raise HTTPException(status_code=404, detail="Reserva no trobada")
    
    db.delete(db_reserva)
    db.commit()
    return None

# --- NOTES PER A MANTENIMENT (ALEMBIC) ---
"""
Per a migracions futures:
1. Instal·lar alembic: pip install alembic
2. Inicialitzar: alembic init migrations
3. Configurar env.py amb el model de SQLAlchemy
4. Generar migració: alembic revision --autogenerate -m "crear_taula_reserves"
"""