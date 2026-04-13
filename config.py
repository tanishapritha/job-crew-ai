from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SPREADSHEET_ID: str
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "credentials.json"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    MAIL_FROM: str = ""
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    ADZUNA_APP_ID: str = ""
    ADZUNA_API_KEY: str = ""
    DASHBOARD_URL: str = ""
    UNSUBSCRIBE_BASE_URL: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
