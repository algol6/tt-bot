from dotenv import load_dotenv
load_dotenv()
from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from enum import Enum

class Collection(Enum):
    USER = "user"
    STATS = "stats"
    CONFIG = "config"

class Database:
    uri:str = getenv("DATABASE_URI")
    @staticmethod
    async def insert_one(collection:str,obj:dict):
        client = AsyncIOMotorClient(Database.uri, server_api=ServerApi('1'))
        db = client.ttdb
        await db[collection].insert_one(obj)

    @staticmethod
    async def insert(collection:str,objs:list[dict]):
        client = AsyncIOMotorClient(Database.uri, server_api=ServerApi('1'))
        db = client.ttdb
        return await db[collection].insert_many([x for x in objs])

    @staticmethod
    async def select_one(collection:str,obj:dict):
        client = AsyncIOMotorClient(Database.uri, server_api=ServerApi('1'))
        db = client.ttdb
        return await db[collection].find_one(obj)
    
    @staticmethod
    async def select(collection:str):
        client = AsyncIOMotorClient(Database.uri, server_api=ServerApi('1'))
        db = client.ttdb
        cursor = db[collection].find()
        return cursor.to_list()
    
    @staticmethod
    async def update_one(collection:str, old_obj:dict, new_obj:dict):
        client = AsyncIOMotorClient(Database.uri, server_api=ServerApi('1'))
        db = client.ttdb
        await db[collection].update_one({"_id":old_obj["_id"]}, {"$set":new_obj})

    @staticmethod
    async def update_one_user_reward_status(usr:dict,type:str, status:bool):
        client = AsyncIOMotorClient(Database.uri, server_api=ServerApi('1'))
        db = client.ttdb
        await db[Collection.USER.value].update_many({"_id":usr._id},{"$set":{type:status}})