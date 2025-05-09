from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    discord_id:str
    smmo_id:int
    ign:str
    ett:int
    btt:int
    daily:bool
    weekly:bool
    monthly:bool
    
@dataclass
class GameStats:
    smmo_id:int
    steps:int
    npc:int
    pvp:int
    date:datetime

@dataclass
class Config:
    name:str
    value:str

@dataclass
class Log:
    id: int
    log: str
    date: datetime