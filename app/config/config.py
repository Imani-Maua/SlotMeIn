from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST : str
    DB_NAME : str
    DB_USER : str
    DB_PASSWORD : str
    DATABASE_URL : str
    KEY : str
    RESEND_API_KEY: str
    REDIS_URL: str = "redis://localhost:6379"
    WEATHER_LAT: float = 47.4979
    WEATHER_LON: float = 19.0402
    WEATHER_API_URL: str = "https://api.open-meteo.com/v1/forecast"

    class Config:
        env_file = ".env"