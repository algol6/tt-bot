from dataclasses import dataclass, asdict, field

@dataclass
class MongoDbDataclass:
    _id: str
    def as_dict(self):
        return {key: value for key, value in asdict(self).items() if value is not None}

@dataclass
class User(MongoDbDataclass):
    ign:str
    discord_id:int
    smmo_id:int
    ett:int
    btt:int
    daily:bool
    weekly:bool
    monthly:bool
    
@dataclass
class GameStats(MongoDbDataclass):
    smmo_id:int
    steps:int
    npc:int
    pvp:int
    year:int
    month:int
    day:int
    time:int
    
@dataclass
class GameLbReward(MongoDbDataclass):
    daily:bool
    weekly:bool
    monthly:bool
