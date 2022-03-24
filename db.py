from datetime import datetime
from typing import Any, Optional
import os
import models
import constants
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
from dacite import from_dict
from dataclasses import asdict

class Update:

    def __init__(self, **kwargs) -> None:
        self.update = {}

    def _modify_document(self, aspect: str) -> callable:
        def wrapper(**kwargs) -> 'Update':
            if f"${aspect}" not in self.update:
                self.update[f"${aspect}"] = {}

            self.update[f"${aspect}"].update(kwargs)
            return self

        return wrapper

    def __getattribute__(self, __name: str) -> Any:
        if __name in ('update', '_modify_document'):
            return super().__getattribute__(__name)
        return self._modify_document(__name)

    def __bool__(self) -> bool:
        return bool(self.update)


class Database:

    def __init__(self) -> None:
        self.motor = AsyncIOMotorClient(os.getenv("MONGO"))
        self.db = self.motor[os.getenv("DB_NAME", "staging").lower()]
        self.cache = {}

    async def _fetch(self, collection: str, query: dict, limit: int = 1) -> Any:
        if limit == 1:
            return await self.db[collection].find_one(query)
        else:
            return await self.db[collection].find(query).to_list(length=limit)

    async def _insert(self, collection: str, data: dict | list) -> Any:
        if isinstance(data, dict):
            return await self.db[collection].insert_one(data)
        else:
            return await self.db[collection].insert_many(data)

    async def _update(self, collection: str, query: dict, data: dict, upsert: bool = False, many: bool = False) -> Any:
        if many:
            return await self.db[collection].update_many(query, data, upsert=upsert)
        else:
            return await self.db[collection].update_one(query, data, upsert=upsert)

    async def _delete(self, collection: str, query: dict, many: bool = False) -> Any:
        if many:
            return await self.db[collection].delete_many(query)
        else:
            return await self.db[collection].delete_one(query)

    async def fetch_user(self, id: int) -> models.User:
        user = await self._fetch("users", {"id": id}, limit=1)

        if user is None:
            user = models.User(_id=None,id=id)

            user_dict = asdict(user)
            del user_dict["_id"]
            user._id = (await self._insert("users", user_dict)).inserted_id

            return user

        return from_dict(data_class=models.User, data=user)

    async def update_user(self, id: int, data: Update | dict) -> None:
        print(data.update)
        await self._update("users", {"id": id}, data.update if isinstance(data, Update) else data, upsert=False, many=False)

    async def fetch_guild(self, id: int) -> models.Guild:
        guild = await self._fetch("guilds", {"id": id}, limit=1)

        if guild is None:
            guild = models.Guild(_id=None,id=id)

            guild_dict = asdict(guild)
            del guild_dict["_id"]
            guild._id = (await self._insert("guilds", guild_dict)).inserted_id

            return guild

        return from_dict(data_class=models.Guild, data=guild)

    async def update_guild(self, id: int, data: Update | dict) -> None:
        print(data.update)
        await self._update("guilds", {"id": id}, data.update if isinstance(data, Update) else data, upsert=False, many=False)

    

    