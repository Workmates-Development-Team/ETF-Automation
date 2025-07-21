from sqlalchemy import create_engine, Column, Integer, Float, String, Date, Time, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config import IST, DB_URL

# Initialize SQLAlchemy
Base = declarative_base()
engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)

# Define Database Models
class ETF(Base):
    __tablename__ = 'etfs'
    etf_id = Column(Integer, primary_key=True)
    etf_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))

class InvestmentCycle(Base):
    __tablename__ = 'investment_cycles'
    cycle_id = Column(Integer, primary_key=True)
    etf_id = Column(Integer, nullable=False)
    total_amount = Column(Float(15, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))
    updated_at = Column(DateTime, default=lambda: datetime.now(IST))

class InvestmentSchedule(Base):
    __tablename__ = 'investment_schedules'
    schedule_id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, nullable=False)
    week_number = Column(Integer, nullable=False)
    execution_date = Column(Date, nullable=False)
    execution_time = Column(Time, default='15:00:00', nullable=False)
    amount = Column(Float(15, 2), nullable=False)
    quantity = Column(Integer, default=0)  # New column to store executed quantity
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))
    updated_at = Column(DateTime, default=lambda: datetime.now(IST))

class ExecutionHistory(Base):
    __tablename__ = 'execution_history'
    execution_id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, nullable=False)
    execution_timestamp = Column(DateTime, nullable=False)
    amount = Column(Float(15, 2), nullable=False)
    status = Column(String(20), nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(IST))

# Create tables
Base.metadata.create_all(engine)