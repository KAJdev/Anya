from enum import Enum
import math
from optparse import Option
import string
from typing import Optional
from bson.objectid import ObjectId
from datetime import date, datetime, timedelta
from dis_snek import Scale, Embed, Button, ActionRow
from dis_snek import Permissions
from dataclasses import dataclass, field
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

    @classmethod
    def has_module(cls, modules: 'ModuleToggles', module: 'ModuleToggles') -> bool:
        return bool(modules & module)

    @classmethod
    def get_modules(cls) -> list[str]:
        return (module for module in cls.__members__ if module != 'NONE')

    @classmethod
    def all(cls) -> 'ModuleToggles':
        return cls.MESSAGE_REFERENCES | cls.OCR_REPLY | cls.FXTWITTER

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

@dataclass(slots=True)
class User:
    _id: ObjectId
    id: int
    permissions: int = AnyaPermissions.NONE.value
    manga_page: int = 0
    agents: list[Agent] = field(default_factory=list)
    peanuts: int = 0
    world_peace: int = 0

    def has_permision(self, permission: AnyaPermissions) -> bool:
        return AnyaPermissions.has_permission(AnyaPermissions(self.permissions), permission)

    def add_permision(self, permission: AnyaPermissions) -> None:
        self.permissions |= permission.value

    def remove_permision(self, permission: AnyaPermissions) -> None:
        self.permissions &= ~permission.value


@dataclass(slots=True)
class Guild:
    _id: ObjectId
    id: int
    modules: int = ModuleToggles.default().value
    auto_thread_channels: list[int] = field(default_factory=list)
    auto_publish_channels: list[int] = field(default_factory=list)

    def module_enabled(self, module: ModuleToggles) -> bool:
        return ModuleToggles.has_module(ModuleToggles(self.modules), module)

    def add_module(self, module: ModuleToggles) -> None:
        self.modules |= module.value

    def remove_module(self, module: ModuleToggles) -> None:
        self.modules &= ~module.value


class AdminScale(Scale):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.database = bot.db.db
        self.add_scale_check(self.is_manager)

    async def is_manager(self, ctx):
        return ctx.author.has_permission(Permissions.MANAGE_GUILD)