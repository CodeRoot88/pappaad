import os

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

load_dotenv()


def get_url():
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "glitchads")

    if db_host.startswith("/cloudsql/"):
        # If db_host is a Cloud SQL socket, no need for port
        DATABASE_URL = f"postgresql+psycopg://{db_user}:{db_password}@/{db_name}?host={db_host}"
    else:
        # Standard TCP connection
        db_port = os.getenv("DB_PORT", "5432")
        DATABASE_URL = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    return DATABASE_URL


engine = create_engine(
    get_url(),
    # should look into other options
)


def get_db_session():
    with Session(engine) as session:
        yield session
