# software_fatture/database/db_session.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# Nome del DB locale
DB_URL = "sqlite:///fatture.db"

engine = create_engine(DB_URL, echo=False)  # echo=True se vuoi vedere i log SQL
SessionLocal = sessionmaker(bind=engine)

def init_db():
    # Crea effettivamente le tabelle
    Base.metadata.create_all(engine)
