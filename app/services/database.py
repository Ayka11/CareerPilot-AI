from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class JobDB(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    company = Column(String)
    title = Column(String)
    url = Column(String, unique=True)
    salary = Column(String)
    location = Column(String)
    remote = Column(Boolean)
    part_time = Column(Boolean)
    flexible = Column(Boolean)
    description = Column(Text)
    skills = Column(Text)  # JSON string or separate table later
    source = Column(String)
    score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied = Column(Boolean, default=False)

engine = create_engine("sqlite:///data/jobs.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
