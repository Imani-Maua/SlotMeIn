from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.config.config import Settings

settings = Settings()


database = settings.DATABASE_URL
engine = create_engine(database, echo=False, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)

def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_db = session