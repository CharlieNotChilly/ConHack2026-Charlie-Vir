from pydantic import BaseSettings


class Settings(BaseSettings):
    pinecone_api_key: str = ""
    pinecone_index: str = ""
    gemini_api_key: str = ""
    voyage_api_key: str = ""


settings = Settings()
