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
from enum import Enum, Flag

class AnyaPermissions(Flag):
    NONE = 0
    ADMIN = 1

    VIEW_SOURCE = 2

    @classmethod
    def has_permission(cls, user, permission):
        return user.permissions & permission or user.permissions & cls.ADMIN


@dataclass(slots=True)
class User:
    _id: ObjectId
    id: int
    permissions: AnyaPermissions = AnyaPermissions.NONE


class AdminScale(Scale):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.database = bot.db.db
        self.add_scale_check(self.is_manager)

    async def is_manager(self, ctx):
        return ctx.author.has_permission(Permissions.MANAGE_GUILD)