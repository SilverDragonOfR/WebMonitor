import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum
from datetime import datetime, timezone

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./web_monitor.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StatusType(str, enum.Enum):
    INITIAL = "INITIAL"
    UP = "UP"
    DOWN = "DOWN"
    END = "END"

class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    check_interval_seconds = Column(Integer, default=300)
    expected_status_code = Column(Integer, default=200)
    
    status_history = relationship("SiteStatusHistory", back_populates="site", cascade="all, delete")   

class SiteStatusHistory(Base):
    __tablename__ = "site_status_history"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"))
    status = Column(Enum(StatusType), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    last_checked = Column(DateTime, default=datetime.now(timezone.utc))
    last_status_change = Column(DateTime, default=datetime.now(timezone.utc))

    site = relationship("Site", back_populates="status_history")
    
class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, nullable=False)
    discord_webhook_url = Column(String, unique=True, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    
def remove_db():
    Base.metadata.drop_all(bind=engine)