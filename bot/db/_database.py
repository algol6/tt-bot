from dotenv import load_dotenv
load_dotenv()
from os import getenv

from aiomysql import IntegrityError, connect
from . import models as model 
import asyncio
from datetime import datetime

sem = asyncio.Semaphore(1)

class Database:
    MYSQL_ROUTER_HOST = getenv("MYSQL_ROUTER_HOST")
    MYSQL_ROUTER_PORT = int(getenv("MYSQL_ROUTER_PORT", 6446))
    MYSQL_USER = getenv("MYSQL_USER")
    MYSQL_PASSWORD = getenv("MYSQL_PASSWORD")
    MYSQL_DB = getenv("MYSQL_DB")

    @staticmethod
    async def _select(query:str, parameters:tuple=()) -> list | None:
        try:
            async with await connect(host=Database.MYSQL_ROUTER_HOST,
                                        port=Database.MYSQL_ROUTER_PORT,
                                        user=Database.MYSQL_USER,
                                        password=Database.MYSQL_PASSWORD,
                                        db=Database.MYSQL_DB) as db:
                async with await db.cursor() as cur:
                    await cur.execute(query,parameters)
                    # res = [x for x in await cur.fetchall()]
                    # return [[v for v in x] for x in res] if len(res)!=0 and type(res[0]) is tuple else res
                    return list(await cur.fetchall())
        except Exception as e:
            print(e)
            return None
        
    @staticmethod
    async def _insert(query:str, parameters:tuple=()) -> None:
        try:
            async with await connect(host=Database.MYSQL_ROUTER_HOST,
                                        port=Database.MYSQL_ROUTER_PORT,
                                        user=Database.MYSQL_USER,
                                        password=Database.MYSQL_PASSWORD,
                                        db=Database.MYSQL_DB) as db:
                async with await db.cursor() as cur:
                    await cur.execute(query,parameters)
                    await db.commit()
        except Exception as e:
            print(e)
            raise IntegrityError()
        
    @staticmethod
    async def create_table() -> None:
        sql_statements = [
            """CREATE TABLE IF NOT EXISTS user(
                discord_id CHAR(30) PRIMARY KEY,
                smmo_id INTEGER(10) UNIQUE,
                ign CHAR(30),
                ett INTEGER(10),
                btt INTEGER(10),
                daily BOOL,
                weekly BOOL,
                monthly BOOL
            );""",

            """CREATE TABLE IF NOT EXISTS stats(
                smmo_id INTEGER(10),
                steps INTEGER(8),
                npc INTEGER(8),
                pvp INTEGER(8),
                date DATETIME,
                PRIMARY KEY(smmo_id,date)
            );""",

            """CREATE TABLE IF NOT EXISTS config(
                name CHAR(4) PRIMARY KEY,
                value CHAR(20)
            );""",

            """CREATE TABLE IF NOT EXISTS log(
                id INTEGER NOT NULL AUTO_INCREMENT,
                log TEXT,
                date DATETIME,
                PRIMARY KEY(id)
            );"""
        ]

        for statement in sql_statements:
            await Database._insert(statement)

    @staticmethod
    async def select_log() -> list[model.Log]:
        data = await Database._select("SELECT * FROM log")
        if data is not None and len(data)!=0:
            return [model.Log(v[0],v[1],v[2]) for v in data]
        return []
    
    @staticmethod
    async def insert_log(message:str,date:datetime) -> bool:
        try:
            await Database._insert("INSERT INTO log VALUES(%s,%s)",(message,date))
            return True
        except IntegrityError:
            return False
        
    async def delete_log(date:datetime) -> None:
        await Database._insert("DELETE FROM log WHERE date<=%s",(date,))

    @staticmethod
    async def select_user_discord(discord_id:int) -> model.User | None:
        data = await Database._select("SELECT * FROM user WHERE discord_id=%s",(discord_id,))
        if data is not None and len(data) != 0:
            return model.User(data[0][0],data[0][1],data[0][2],data[0][3],data[0][4],data[0][5],data[0][6],data[0][7])
        return None
    
    @staticmethod
    async def select_user_smmoid(smmo_id:int) -> model.User | None:
        data = await Database._select("SELECT * FROM user WHERE smmo_id=%s",(smmo_id,))
        if data is not None and len(data) != 0:
            return model.User(data[0][0],data[0][1],data[0][2],data[0][3],data[0][4],data[0][5],data[0][6],data[0][7])
        return None
    
    @staticmethod
    async def select_user_all() -> list[model.User]:
        data = await Database._select("SELECT * FROM user")
        if data is not None and len(data) != 0:
            return [model.User(v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7]) for v in data]
        return []
    
    @staticmethod
    async def insert_user(discord_id:int, smmo_id:int, ign:str, ett:int, btt:int, daily:bool, weekly:bool, monthly:bool) -> bool:
        try:
            await Database._insert("INSERT INTO user VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",(discord_id,smmo_id,ign,ett,btt,daily,weekly,monthly,))
            return True
        except IntegrityError:
            return False

    @staticmethod
    async def update_user(discord_id:int,ign:str,ett:int,btt:int,daily:bool,weekly:bool,monthly:bool):
        await Database._insert("UPDATE user SET ign=%s,ett=%s,btt=%s,daily=%s,weekly=%s,monthly=%s WHERE discord_id=%s",(ign,ett,btt,daily,weekly,monthly,discord_id))

    @staticmethod
    async def delete_user(smmo_id:int) -> None:
        await Database._insert("DELETE FROM user WHERE smmo_id=%s",(smmo_id,))

    @staticmethod
    async def select_stats(smmo_id:int, datetime:datetime) -> model.GameStats | None:
        data = await Database._select("SELECT * FROM stats WHERE smmo_id=%s AND date>=%s ORDER BY date ASC LIMIT 1",(smmo_id,datetime,))
        if data is not None and len(data) != 0:
            return model.GameStats(data[0][0],data[0][1],data[0][2],data[0][3],data[0][4])
        return None
    
    @staticmethod
    async def insert_stats(smmo_id:int,steps:int,npc:int,pvp:int,datetime:datetime) -> bool:
        try:
            await Database._insert("INSERT INTO stats VALUES (%s,%s,%s,%s,%s)",(smmo_id,steps,npc,pvp,datetime,))
            return True
        except IntegrityError:
            return False

    @staticmethod
    async def delete_stats(datetime:datetime) -> None:
        await Database._insert("DELETE FROM stats WHERE date<=%s",(datetime,))

    @staticmethod
    async def select_config(name:str) -> model.Config | None:
        data = await Database._select("SELECT * FROM config WHERE name=%s",(name,))
        if data is not None and len(data) != 0:
            return model.Config(data[0][0],data[0][1])
        return None

    @staticmethod
    async def insert_config(name:str,value:int) -> bool:
        try:
            await Database._insert("INSERT INTO config VALUES (%s,%s)",(name,value,))
            return True
        except IntegrityError:
            return False
        
    @staticmethod
    async def update_config(name:str,value:int) -> None:
        await Database._insert("UPDATE config SET value=%s WHERE name=%s",(value,name,))
        