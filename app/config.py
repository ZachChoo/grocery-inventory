import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./grocery_inventory.db")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///./grocery_inventory.db")
    
    # JWT Authentication Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "testing-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # FastAPI Configuration
    API_TITLE: str = "Grocery Store Inventory API"
    API_DESCRIPTION: str = "A backend API for managing grocery store inventory"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Default Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "100"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "1000"))

    # Email Settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")


# Create a single settings instance
settings = Settings()