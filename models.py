from enum import Enum
import math
from optparse import Option
import string
from typing import Any, Optional
from bson.objectid import ObjectId
from datetime import date, datetime, timedelta
from naff import Extension, Embed, Button, ActionRow
from naff import Permissions
from dataclasses import asdict, dataclass, field
from utils import emoji, color, progress, time
import constants
import uuid
import random
from enum import Enum, Flag, auto

class AnyaPermissions(Flag):
    NONE = auto()
    ADMIN = auto()

    VIEW_SOURCE = auto()
    ADD_RANDOMS = auto()

    @classmethod
    def has_permission(cls, permissions: 'AnyaPermissions', permission: 'AnyaPermissions') -> bool:
        return bool(permissions & permission) or bool(permissions & cls.ADMIN)

    @classmethod
    def get_permissions(cls) -> list[str]:
        return (member for member in cls.__members__ if member != 'NONE')

class ModuleToggles(Flag):
    NONE = auto()

    MESSAGE_REFERENCES = auto()
    OCR_REPLY = auto()
    FXTWITTER = auto()
    CHARACTER = auto()
    STARBOARD = auto()

    @classmethod
    def has_module(cls, modules: 'ModuleToggles', module: 'ModuleToggles') -> bool:
        return bool(modules & module)

    @classmethod
    def get_modules(cls) -> list[str]:
        return (module for module in cls.__members__ if module != 'NONE')

    @classmethod
    def all(cls) -> 'ModuleToggles':
        return cls.MESSAGE_REFERENCES | cls.OCR_REPLY | cls.FXTWITTER | cls.CHARACTER | cls.STARBOARD

    @classmethod
    def default(cls) -> 'ModuleToggles':
        return cls.MESSAGE_REFERENCES | cls.OCR_REPLY | cls.FXTWITTER

MISSION_STRUCTURES = {
    "trust": "Deliver",
    "wits": "Sabotage",
    "stealth": "Sneak",
}

MISSION_OBJECTS = {
    "trust": [
        "a note",
        "war plans",
        "a list of people",
        "a list of places",
        "schematics",
    ],
    "wits": [
        "an attack",
        "a plan",
        "a terrorist attack",
        "war plans"
    ],
    "stealth": [
        "tapes",
        "plans",
        "a high ranking official",
        "a celebrity",
        "the president"
    ],
}

SECONDARY_OBJECTS = {
    "trust": [
        "to a person",
        "to a place",
        "to HQ",
        "to the government",
        "to the police",
        "to the military",
    ],
    "wits": [
        "alone",
        "without much intel",
        "with intel",
    ],
    "stealth": [
        "across the country",
        "across the world",
        "over the border",
        "through enemy territory",
        "without being detected",
    ],
}

@dataclass(slots=True)
class Mission:
    affinity: str = field(default_factory=lambda: random.choice(['trust', 'wits', 'stealth']))
    difficulty: int = field(default_factory=lambda: random.randint(0,5))
    satisfactory: int = field(default_factory=lambda: random.randint(15,24))
    peanuts: int = field(default_factory=lambda: random.randint(3,10))
    importance: int = field(default_factory=lambda: random.randint(10,20))
    length: int = field(default_factory=lambda: random.randint(5,120))
    started_at: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: ''.join(random.choices(string.ascii_letters, k=8)))

    @property
    def name(self) -> str:
        return f"{MISSION_STRUCTURES[self.affinity]} {MISSION_OBJECTS[self.affinity][self.difficulty % len(MISSION_OBJECTS)]} {SECONDARY_OBJECTS[self.affinity][self.importance % len(SECONDARY_OBJECTS)]}"

    @property
    def description(self) -> str:
        return f"in {self.length} minutes for {self.peanuts} 🥜"

    @property
    def ends_at(self) -> datetime:
        return self.started_at + timedelta(minutes=self.length)

    def ended(self) -> bool:
        return self.ends_at <= datetime.utcnow()

    def complete(self, agent: 'Agent') -> bool:
        # calculate if the mission completed or not based on agent stats
        # if the agent's affinity is greater than the mission's satisfaction, the mission always completes
        # if the agent's affinity is less than the mission's difficulty, the mission always fails
        # otherwise the mission is completed with a random chance of success determined by the agent's affinity
        # and the mission's difficulty and satisfaction (the agent's affinity is the primary factor)

        if agent.stats.get(self.affinity, 0) >= self.satisfactory:
            return True
        
        if agent.stats.get(self.affinity, 0) < self.difficulty:
            return False
            
        random.seed()
        return random.random() < 0.5


@dataclass(slots=True)
class Agent:
    firstname: str = field(default_factory=lambda: ''.join(random.choices(['lo', 'ko', 'ra', 'wo', 'cr', 'ar', 'no', 'ba'], k=random.randint(2,4))))
    lastname: str = field(default_factory=lambda: ''.join(random.choices(['lo', 'ko', 'ra', 'wo', 'cr', 'ar', 'no', 'ba'], k=random.randint(3,6))))
    stats: dict = field(default_factory=lambda: {'trust': random.randint(0,25), 'wits': random.randint(0,25), 'stealth': random.randint(0,25)})
    mission: Optional[Mission] = field(default=None)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def generate_stats(self, low: int = 0, high: int = 25):
        for stat in self.stats:
            self.stats[stat] = random.randint(low, high)

    @property
    def name(self) -> str:
        return f"{self.firstname.title()} {self.lastname.title()}"

    @property
    def description(self) -> str:
        return f"{self.firstname} {self.lastname} is a {self.stats['trust']}/{self.stats['wits']}/{self.stats['stealth']} agent"

@dataclass(slots=True)
class StarboardMessage:
    _id: ObjectId

    message_id: int
    channel_id: int
    guild_id: int
    author_id: int
    additional_reactions: int

    posted_message_id: int
    replies: list[int] = field(default_factory=list)
    last_edited: datetime = field(default_factory=datetime.utcnow)
    posted: datetime = field(default_factory=datetime.utcnow)

@dataclass(slots=True)
class User:
    _id: ObjectId
    id: int
    permissions: int = AnyaPermissions.NONE.value
    manga_pages: dict[str, int] = field(default_factory=dict)
    agents: list[Agent] = field(default_factory=list)
    peanuts: int = 0
    world_peace: int = 0

    def has_permision(self, permission: AnyaPermissions) -> bool:
        return AnyaPermissions.has_permission(AnyaPermissions(self.permissions), permission)

    def add_permision(self, permission: AnyaPermissions) -> None:
        self.permissions |= permission.value

    def remove_permision(self, permission: AnyaPermissions) -> None:
        self.permissions &= ~permission.value

@dataclass
class TamagotchiGenes:

    seed: float
    height: float
    width: float
    segments: float

    color_r: float
    color_g: float
    color_b: float

    body_edge_color_r: float
    body_edge_color_g: float
    body_edge_color_b: float

    eye_color_r: float
    eye_color_g: float
    eye_color_b: float
    eye_size: float
    eye_shape: bool

    mouth_color_r: float
    mouth_color_g: float
    mouth_color_b: float
    mouth_size: float
    mouth_shape: bool

    body_shape: bool
    body_width: float
    body_height: float
    body_edge_width: float

    head_shape: bool
    head_width: float
    head_height: float
    head_edge_width: float

    arm_length: float
    arm_angle: float
    arm_height: float
    arm_width: float

    arm_color_r: float
    arm_color_g: float
    arm_color_b: float

    mutation_rate: float
    female: bool

    class BoundedValue(float):
        def bounded(self, upper, lower, digits = None) -> int:
            """
            return a float clamped between upper and lower in integer form
            """

            return round(((upper - lower) * self) + lower, digits)

    def __post_init__(self) -> None:
        # clamp values to be between 0 and 1, via wrapping
        for key, value in self.__dict__.items():
            if value < 0:
                self.__dict__[key] = 1 + value
            elif value > 1:
                self.__dict__[key] = value - 1
        
    @classmethod
    def from_parents(cls, mother: 'TamagotchiGenes', father: 'TamagotchiGenes') -> 'TamagotchiGenes':
        kwargs = {}
        for key, tp in cls.__annotations__.items():

            if tp == float:
                kwargs[key] = random.uniform(mother.__dict__[key], father.__dict__[key]) + random.uniform(mother.mutation_rate, father.mutation_rate)
            elif tp == bool:
                kwargs[key] = random.choice([mother.__dict__[key], father.__dict__[key]])

        return cls(**kwargs)

    @classmethod
    def from_nothing(cls) -> 'TamagotchiGenes':
        kwargs = {}
        for key, tp in cls.__annotations__.items():
            if tp == float:
                kwargs[key] = random.uniform(0, 1)
            elif tp == bool:
                kwargs[key] = random.choice([True, False])

        return cls(**kwargs)

    @property
    def male(self) -> bool:
        return not self.female

    def __getattribute__(self, __name: str) -> Any:
        value = super().__getattribute__(__name)

        if isinstance(value, float):
            return self.BoundedValue(value)
        return value


@dataclass(slots=True)
class Tamagotchi:
    _id: ObjectId
    owner: int
    genes: TamagotchiGenes = field(default_factory=TamagotchiGenes.from_nothing)
    name: str = field(default_factory=lambda: ''.join(random.choices(string.ascii_letters, k=random.randint(3,8))))
    birthday: datetime = field(default_factory=datetime.utcnow)

    @property
    def age(self) -> timedelta:
        return (datetime.utcnow() - self.birthday)

@dataclass(slots=True)
class Guild:
    _id: ObjectId
    id: int
    modules: int = ModuleToggles.default().value
    auto_thread_channels: list[int] = field(default_factory=list)
    auto_publish_channels: list[int] = field(default_factory=list)
    starboard_overrides: dict[str, bool] = field(default_factory=dict)
    starboard_channel: int = None

    def module_enabled(self, module: ModuleToggles) -> bool:
        return ModuleToggles.has_module(ModuleToggles(self.modules), module)

    def add_module(self, module: ModuleToggles) -> None:
        self.modules |= module.value

    def remove_module(self, module: ModuleToggles) -> None:
        self.modules &= ~module.value


class AdminExtension(Extension):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.database = bot.db.db
        self.add_Extension_check(self.is_manager)

    async def is_manager(self, ctx):
        return ctx.author.has_permission(Permissions.MANAGE_GUILD)