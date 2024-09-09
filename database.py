from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import inspect
from pathlib import Path

# Utility function to get project directory
def get_project_dir():
    try:
        current_script_path = Path(__file__).resolve()
        current_script_dir = current_script_path.parent
    except NameError:
        # This works when running interactively
        current_script_dir = Path.cwd()
    
    return current_script_dir

# Build the DATABASE_URL
DATABASE_URL = "sqlite:///" + str(get_project_dir() / "users.db")

# Initialize the engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

# Function to create database and check for existing tables
def create_database():
    # Create an inspector to check if tables exist
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        print("NO table users")
        # Create all tables that are not yet created
        Base.metadata.create_all(bind=engine)
        print("Table 'users' created successfully.")
    else:    
        print("Table 'users' already exists.")

    # Print all tables in the database
    tables = inspector.get_table_names()
    print("Tables in the database:")
    for table in tables:
        print(table)

# Entry point to create the database
if __name__ == "__main__":
    create_database()
