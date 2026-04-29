from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    pinecone_api_key: str = ""
    pinecone_index: str = ""
    pinecone_dimension: int = 3072
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_disabled: bool = False
    gemini_api_key: str = ""
    gemini_fallback: bool = True
    voyage_api_key: str = ""
    uploads_dir: str = "./data/uploads"


settings = Settings()
