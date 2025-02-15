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

# Defining an Enum for website status types
class StatusType(str, enum.Enum):
    INITIAL = "INITIAL" # When a site is added
    UP = "UP" # When the site check is success
    DOWN = "DOWN" # When the site check is failure
    END = "END" # When a site is removed

# Represents each individual site
class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False) # URl cannot be same
    name = Column(String, nullable=True)
    check_interval_seconds = Column(Integer, default=300) # default 5 min
    expected_status_code = Column(Integer, default=200)
    
    # Foreign key, so that on delete the history is deleted automatically
    status_history = relationship("SiteStatusHistory", back_populates="site", cascade="all, delete")   

# Represents each statuc check stored
class SiteStatusHistory(Base):
    __tablename__ = "site_status_history"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE")) # Foreign key
    status = Column(Enum(StatusType), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    last_checked = Column(DateTime, default=datetime.now(timezone.utc)) # Time when this check was made
    last_status_change = Column(DateTime, default=datetime.now(timezone.utc)) # Time when the last differing (in status) check was made

    # Again foreign key
    site = relationship("Site", back_populates="status_history")
    
# This just stores the webhooks for each site
class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, nullable=False) # No foreign key, so that we can fill any we wish by http request, without worrying over whether the site is presnt or not
    discord_webhook_url = Column(String, unique=True, nullable=False)

# create all the tables
def init_db():
    Base.metadata.create_all(bind=engine)
    
# drop all the tables
def remove_db():
    Base.metadata.drop_all(bind=engine)