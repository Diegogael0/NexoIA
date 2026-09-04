from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://nexo:nexo@localhost:5432/nexo"
    jwt_secret: str = "change-this-before-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    cors_origins: str = "http://localhost:8080"
    admin_username: str = "admin"
    admin_email: str = "admin@nexoia.mx"
    admin_password: str = "12345678"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
