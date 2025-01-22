from dataclasses import dataclass, field

@dataclass
class GuildMemberInfo:
    user_id: int = field(default_factory=None)
    position: str = field(default_factory=None)
    name: str = field(default_factory=None)
    level: int = field(default_factory=None)
    safe_mode: bool = field(default_factory=None)
    banned: bool = field(default_factory=None)
    current_hp: int = field(default_factory=None)
    max_hp: int = field(default_factory=None)
    warrior: bool = field(default_factory=None)
    steps: int = field(default_factory=None)
    npc_kills: int = field(default_factory=None)
    user_kills: int = field(default_factory=None)
    last_activity: int = field(default_factory=None)


@dataclass
class GuildInfo:
    id: int
    name: str
    tag: str
    owner: int
    exp: int
    current_season_exp: int
    passive: bool
    icon: str
    legacy_exp: int
    member_count: int
    eligible_for_guild_war: bool

@dataclass
class ShortGuildInfo:
    id: int = field(default_factory=None)
    name: str = field(default_factory=None)

@dataclass
class Location:
    id: int
    name: str

@dataclass
class PlayerInfo:
    id: int
    name: str
    avatar: str
    motto: str
    level: int
    profile_number: str
    exp: int
    gold: int
    steps: int
    npc_kills: int
    user_kills: int
    quests_complete: int
    quests_performed: int
    dexterity: int
    defence: int
    strength: int
    bonus_dex: int
    bonus_def: int
    bonus_str: int
    hp: int
    last_activity: int
    max_hp: int
    safeMode: bool
    banned: bool
    background: int
    membership: bool
    tasks_completed: int
    boss_kills: int
    market_trades: int
    reputation: int
    creation_date: str
    bounties_completed: int
    dailies_unlocked: int
    chests_opened: int
    current_location: Location
    guild: ShortGuildInfo  = field(default_factory=None)

    def __post_init__(self):
        self.current_location = Location(**self.current_location)
        self.guild = ShortGuildInfo(**self.guild)
