from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database

# ULR_DATABASE = "sqlite:///./manager.db"
# engine = create_engine(ULR_DATABASE , connect_args={"check_same_thread" : False} , echo=True)
#
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#ULR_DATABASE = "postgresql://postgres:admin@localhost/nitweb4"
ULR_DATABASE = "postgresql://postgres:admin@postgres_container:5432/nitweb4"


engine = create_engine(ULR_DATABASE, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
