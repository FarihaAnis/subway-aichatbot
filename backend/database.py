from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ Database Configuration
DB_URL = "mysql+mysqlconnector://username:password@localhost:3306/subway_db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ✅ Define Database Model (Previously in `schemas.py`)
class SubwayOutlet(Base):
    __tablename__ = "subway_outlets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    operating_hours = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    waze_link = Column(String, nullable=True)

# ✅ Create tables in the database
Base.metadata.create_all(bind=engine)
