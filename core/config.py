import os
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

class Settings:
    def __init__(self):
        # Validate database configuration on initialization
        if not os.getenv("DATABASE_URL"):
            raise ValueError("DATABASE_URL environment variable is not set")
        
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    MILVUS_ENDPOINT: str = os.getenv("MILVUS_ENDPOINT")
    MILVUS_PORT: str = os.getenv("MILVUS_PORT")
    MILVUS_TOKEN: str = os.getenv("MILVUS_TOKEN")
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:5000"]
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "postgres")  # Set default if not specified
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL")

settings = Settings()

# Debug output
print(f"Loaded DATABASE_URL: {settings.DATABASE_URL}")
print(f"Loaded DATABASE_NAME: {settings.DATABASE_NAME}")