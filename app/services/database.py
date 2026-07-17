from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class JobApplication(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    job_url = Column(String, unique=True)
    company = Column(String)
    title = Column(String)
    score = Column(Integer)
    status = Column(String, default='applied')
    applied_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default='')

engine = create_engine('sqlite:///data/applications.db', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
