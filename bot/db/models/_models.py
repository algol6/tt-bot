from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    discord_id:int
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
    value:int