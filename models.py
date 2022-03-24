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

    @classmethod
    def has_module(cls, modules: 'ModuleToggles', module: 'ModuleToggles') -> bool:
        return bool(modules & module) or bool(modules & cls.ALL)

    @classmethod
    def get_modules(cls) -> list[str]:
        return (module for module in cls.__members__ if module != 'NONE')


@dataclass(slots=True)
class User:
    _id: ObjectId
    id: int
    permissions: AnyaPermissions = AnyaPermissions.NONE

    def has_permision(self, permission: AnyaPermissions) -> bool:
        return AnyaPermissions.has_permission(self, permission)


@dataclass(slots=True)
class Guild:
    _id: ObjectId
    id: int
    modules: ModuleToggles = ModuleToggles.ALL

    def module_enabled(self, module: ModuleToggles) -> bool:
        return ModuleToggles.has_module(self.modules, module)


class AdminScale(Scale):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.database = bot.db.db
        self.add_scale_check(self.is_manager)

    async def is_manager(self, ctx):
        return ctx.author.has_permission(Permissions.MANAGE_GUILD)