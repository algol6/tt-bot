from dotenv import load_dotenv
load_dotenv()
from os import getenv

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from enum import Enum
import asyncio

sem = asyncio.Semaphore(1)

class Collection(Enum):
    USER = "user"
    STATS = "stats"
    CONFIG = "config"

class Database:
    uri:str = getenv("DATABASE_URI")

    @staticmethod
    async def _get_db() -> AsyncIOMotorClient:
        async with sem:
            client = AsyncIOMotorClient(Database.uri, server_api=ServerApi('1'))
            return client.ttdb

    @staticmethod
    async def insert_one(collection:str,obj:dict):
        db = await Database._get_db()
        await db[collection].insert_one(obj)

    @staticmethod
    async def insert(collection:str,objs:list[dict]):
        db = await Database._get_db()
        return await db[collection].insert_many([x for x in objs])

    @staticmethod
    async def select_one(collection:str,obj:dict):
        db = await Database._get_db()
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
        
        return await db[collection].find_one(obj)
    
    @staticmethod
    async def select(collection:str):
        db = await Database._get_db()
        cursor = db[collection].find({})
        return await cursor.to_list()
    
    @staticmethod
    async def update_one(collection:str, old_obj:dict, new_obj:dict):
        db = await Database._get_db()
        await db[collection].update_one({"_id":old_obj["_id"]}, {"$set":new_obj})

    @staticmethod
    async def update_one_user_reward_status(usr:dict,type:str, status:bool):
        db = await Database._get_db()
        await db[Collection.USER.value].update_many({"_id":usr._id},{"$set":{type:status}})