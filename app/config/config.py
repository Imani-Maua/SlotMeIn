from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST : str
    DB_NAME : str
    DB_USER : str
    DB_PASSWORD : str
    DATABASE_URL : str
    KEY : str
    RESEND_API_KEY: str

    class Config:
        env_file = ".env"