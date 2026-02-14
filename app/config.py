import sys
import logging
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    access_token: str = Field(..., alias="ACCESS_TOKEN")
    app_id: str = Field(..., alias="APP_ID")
    app_secret: str = Field(..., alias="APP_SECRET")
    recipient_waid: str = Field(..., alias="RECIPIENT_WAID")
    version: str = Field(..., alias="VERSION")
    phone_number_id: str = Field(..., alias="PHONE_NUMBER_ID")
    verify_token: str = Field(..., alias="VERIFY_TOKEN")

    class Config:
        env_file = ".env"
        extra = "ignore"  

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )