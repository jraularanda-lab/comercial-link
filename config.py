import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "CAMBIAR-ESTA-CLAVE")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://comercial:comercial@localhost/comercial_link"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
