from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        validation_alias=AliasChoices("MONGODB_URL", "MONGODB_URI", "mongodb_url", "mongodb_uri"),
    )
    mongodb_database: str = "trinetra"

    jwt_secret: str = "default_secret_key_trinetra_verification"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    use_mock_mode: bool = True

    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

