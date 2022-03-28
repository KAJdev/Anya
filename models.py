from enum import Enum
import math
from optparse import Option
from typing import Optional
from bson.objectid import ObjectId
from datetime import date, datetime, timedelta
from dis_snek import Scale, Embed, Button, ActionRow
from dis_snek import Permissions
from dataclasses import dataclass, field
from utils import emoji, color, progress, time
import constants
import uuid
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


@dataclass(slots=True)
class User:
    _id: ObjectId
    id: int
    permissions: int = AnyaPermissions.NONE.value
    manga_page: int = 0

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