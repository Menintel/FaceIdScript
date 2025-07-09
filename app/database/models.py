from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

class Person(Base):
    """Person model to store information about registered individuals"""
    __tablename__ = "people"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FaceEncoding(Base):
    """Stores face encodings for each person"""
    __tablename__ = "face_encodings"
    
    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, index=True)
    encoding = Column(Text, nullable=False)  # JSON string of the face encoding
    image_path = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
