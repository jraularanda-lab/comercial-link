import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "CAMBIAR-ESTA-CLAVE")
    
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "defaultdb")
    
    if all([DB_USER, DB_PASSWORD, DB_HOST]):
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            f"?ssl_ca={BASE_DIR / 'ca.pem'}&ssl_verify_cert=false"
        )
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://comercial:comercial@localhost/comercial_link"
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
