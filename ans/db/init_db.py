"""
Database initialization script for the Agent Name Service.
"""
import os
from sqlalchemy import create_engine
from .models import Base

def init_database(db_url: str = "sqlite:///ans.db") -> None:
    """
    Initialize the database by creating all tables.
    
    Args:
        db_url: Database URL
    """
    # Create database directory if it doesn't exist
    if db_url.startswith("sqlite:///"):
        db_path = db_url[10:]  # Remove "sqlite:///"
        db_dir = os.path.dirname(db_path)
        if db_dir:  # Only create directory if path has a directory component
            os.makedirs(db_dir, exist_ok=True)

    # Create engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_database() 