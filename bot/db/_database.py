from dotenv import load_dotenv
load_dotenv()
from os import getenv

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from enum import Enum
from aiomysql import IntegrityError, connect
from . import models as model 
import asyncio
from datetime import datetime

sem = asyncio.Semaphore(1)

class Collection(Enum):
    USER = "user"
    STATS = "stats"
    CONFIG = "config"

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
                    res = [list(x) for x in res]
                    print(res)
                    return res
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
        ]

        for statement in sql_statements:
            await Database._insert(statement)

    @staticmethod
    async def select_user_discord(discord_id:int) -> model.User | None:
        data = await Database._select("SELECT * FROM user WHERE discord_id=%s",(discord_id,))
        if data is not None and len(data) != 0:
            return model.User(**data)
        return None
    
    @staticmethod
    async def select_user_smmoid(smmo_id:int) -> model.User | None:
        data = await Database._select("SELECT * FROM user WHERE smmo_id=%s",(smmo_id,))
        if data is not None and len(data) != 0:
            return model.User(**data)
        return None
    
    @staticmethod
    async def select_user_all() -> list[model.User]:
        data = await Database._select("SELECT * FROM user")
        if data is not None and len(data) != 0:
            return [model.User(**v) for v in data]
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
        data = await Database._select("SELECT * FROM stats WHERE smmo_id=%s AND datetime>=%s ORDER BY datetime DESC LIMIT 1")
        if data is not None and len(data) != 0:
            return model.GameStats(**data)
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
        await Database._insert("DELETE FROM stats WHERE datetime<=%s",(datetime,))

    @staticmethod
    async def select_config(name:str) -> model.Config | None:
        data = await Database._select("SELECT * FROM config WHERE name=%s",(name,))
        if data is not None and len(data) != 0:
            return model.Config(**data)
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
        
class Database2:
    uri:str = getenv("DATABASE_URI")

    @staticmethod
    async def _get_db() -> AsyncIOMotorClient:
        async with sem:
            client = AsyncIOMotorClient(Database2.uri, server_api=ServerApi('1'))
            return client.ttdb

    @staticmethod
    async def insert_one(collection:str,obj:dict):
        db = await Database2._get_db()
        await db[collection].insert_one(obj)

    @staticmethod
    async def insert(collection:str,objs:list[dict]):
        db = await Database2._get_db()
        return await db[collection].insert_many([x for x in objs])

    @staticmethod
    async def select_one(collection:str,obj:dict):
        db = await Database2._get_db()
        if collection == Collection.STATS.value:
            obj = [
                    {
                        '$match': {
                            'smmo_id': obj["smmo_id"], 
                            'year': {
                                '$gte': obj["year"]
                            }, 
                            'month': {
                                '$gte': obj["month"]
                            }, 
                            'day': {
                                '$gte': obj["day"]
                            }
                        }
                    }, {
                        '$sort': {
                            'year': 1, 
                            'month': 1, 
                            'day': 1
                        }
                    }, {
                        '$limit': 1
                    }
                ]
                
            aaaa =  await db[collection].aggregate(obj).to_list()
            if len(aaaa) == 0:
                return None
            return aaaa[0]
        try:
            return await db[collection].find_one(obj)
        except:
            return None
    
    @staticmethod
    async def select(collection:str):
        db = await Database2._get_db()
        cursor = db[collection].find({})
        return await cursor.to_list()
    
    @staticmethod
    async def update_one(collection:str, old_obj:dict, new_obj:dict) -> None:
        db = await Database2._get_db()
        await db[collection].update_one({"_id":old_obj["_id"]}, {"$set":new_obj})

    @staticmethod
    async def update_one_user_reward_status(usr:dict,type:str, status:bool):
        db = await Database2._get_db()
        await db[Collection.USER.value].update_many({"_id":usr._id},{"$set":{type:status}})