from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Using the psycopg driver (a Python asynchronous/synchronous adapter for PostgreSQL)
DATABASE_URL = "postgresql+psycopg://lpl:lpl01470@localhost:5434/spotify_db"

# The engine is the core database interface, responsible for managing the connection pool and SQL execution.
# create_engine enables connection pooling by default, making it suitable for web applications.
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory function that creates a new database session each time it is called.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all model classes and is used to define the table structure.
Base = declarative_base()