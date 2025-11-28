import asyncpg
from app.config.config import Settings
import pandas as pd
from abc import ABC, abstractmethod
from app.core.schedule.allocator.entities import dbCredentials


settings = Settings()
pool: asyncpg.pool.Pool| None = None 

def postgreCredentials():
    credentials = dbCredentials(
        host=settings.DB_HOST,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )

    return credentials


class dataRepo(ABC):
    @abstractmethod
    async def getData(self):
        pass

class asyncSQLRepo(dataRepo):

    def __init__(self, conn: asyncpg.Connection, query: str, params: tuple =()):
        self.conn = conn
        self.query = query
        self.params = params
    
    async def getData(self):
        return await self.conn.fetch(self.query, *self.params)
    
    async def execute(self):

        return await self.conn.execute(self.query, *self.params)

async def db_pool():
    global pool
    if pool is None:
        creds = postgreCredentials()
        pool = await asyncpg.create_pool(host=creds.host,
                                 database=creds.dbname,
                                 user=creds.user,
                                 password=creds.password,
                                 min_size=1,
                                 max_size=10)

async def get_db():

    if pool is None:
        await db_pool()
    async with pool.acquire() as conn:
        yield conn


class dataFrameAdapter():

    @staticmethod
    def to_dataframe(data: list[asyncpg.Record]) -> pd.DataFrame:
        return pd.DataFrame([dict(record) for record in data])   

