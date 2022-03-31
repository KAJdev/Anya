import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional
import os
import models
import constants
import pymongo
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

            if aspect == 'inc':
                for key, value in kwargs.items():
                    self.update[f"${aspect}"][key] = self.update[f"${aspect}"].get(key, 0) + value
            else:
                self.update[f"${aspect}"].update(kwargs)
            return self

        return wrapper

    def __getattribute__(self, __name: str) -> Any:
        if __name in ('update', '_modify_document'):
            return super().__getattribute__(__name)
        return self._modify_document(__name)

    def __bool__(self) -> bool:
        return bool(self.update)

class TTLCache:

    __slots__ = ('_cache', '_ttl', 'next_ttl', 'put_event')

    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._cache = {}
        self.next_ttl = None
        self.put_event = asyncio.Event()

        #asyncio.create_task(self.ttl_loop())

    def put(self, collection: str, key: Any, value: Any) -> None:
        if collection not in self._cache:
            self._cache[collection] = {}

        self._cache[collection][key] = {
            'value': value,
            'time': datetime.utcnow()
        }

        self.next_ttl = datetime.utcnow() + timedelta(seconds=self._ttl)

        self.put_event.set()

    def get(self, collection: str, key: Any) -> Optional[Any]:
        if collection not in self._cache:
            return None

        if key not in self._cache[collection]:
            return None

        return self._cache[collection][key]['value']

    async def ttl_loop(self) -> None:
        while True:
            while True:
                self.put_event.clear()
                
                if self.next_ttl is None:
                    break

                await asyncio.wait([
                    self.put_event.wait(),
                    asyncio.sleep((self.next_ttl - datetime.utcnow()).total_seconds())
                ], return_when=asyncio.FIRST_COMPLETED)

                self._cache = {
                    collection: {
                        key: value for key, value in self._cache[collection].items()
                        if (datetime.utcnow() - value['time']).total_seconds() < self.ttl
                    } for collection in self._cache
                }

            await self.put_event.wait()
            


class Database:

    def __init__(self) -> None:
        self.motor = AsyncIOMotorClient(os.getenv("MONGO"))
        self.db = self.motor[os.getenv("DB_NAME", "staging").lower()]
        self.cache = TTLCache(constants.CACHE_TTL)

    async def _fetch(self, collection: str, query: dict, limit: int = 1) -> Any:
        if limit == 1:
            return await self.db[collection].find_one(query)
        return await self.db[collection].find(query).to_list(length=limit)

    async def _insert(self, collection: str, data: dict | list) -> Any:
        if isinstance(data, dict):
            return await self.db[collection].insert_one(data)
        return await self.db[collection].insert_many(data)

    async def _update(self, collection: str, query: dict, data: dict, upsert: bool = False, many: bool = False) -> Any:
        if many:
            return await self.db[collection].update_many(query, data, upsert=upsert)
        return await self.db[collection].update_one(query, data, upsert=upsert)

    async def _find_and_update(self, collection: str, query: dict, data: dict, after: bool = True) -> Any:
        return await self.db[collection].find_one_and_update(query, data, return_document=pymongo.ReturnDocument.AFTER if after else pymongo.ReturnDocument.BEFORE)

    async def _delete(self, collection: str, query: dict, many: bool = False) -> Any:
        if many:
            return await self.db[collection].delete_many(query)
        return await self.db[collection].delete_one(query)

    async def fetch_user(self, id: int) -> models.User:
        if user := self.cache.get("users", id):
            return user

        user = await self._fetch("users", {"id": id}, limit=1)

        if user is None:
            user = models.User(_id=None,id=id)

            user_dict = asdict(user)
            del user_dict["_id"]
            user._id = (await self._insert("users", user_dict)).inserted_id

            self.cache.put("users", id, user)

            return user

        user = from_dict(data_class=models.User, data=user)

        self.cache.put("users", id, user)

        return user

    async def update_user(self, id: int, data: Update | dict) -> None:
        user = await self._find_and_update("users", {"id": id}, data.update if isinstance(data, Update) else data)

        if user is not None:
            user = from_dict(data_class=models.User, data=user)
            self.cache.put("users", id, user)

        return user

    async def fetch_guild(self, id: int) -> models.Guild:
        if guild := self.cache.get("guilds", id):
            return guild

        guild = await self._fetch("guilds", {"id": id}, limit=1)

        if guild is None:
            guild = models.Guild(_id=None,id=id)

            guild_dict = asdict(guild)
            del guild_dict["_id"]
            guild._id = (await self._insert("guilds", guild_dict)).inserted_id

            self.cache.put("guilds", id, guild)

            return guild

        guild = from_dict(data_class=models.Guild, data=guild)

        self.cache.put("guilds", id, guild)

        return guild

    async def update_guild(self, id: int, data: Update | dict) -> None:
        guild = await self._find_and_update("guilds", {"id": id}, data.update if isinstance(data, Update) else data)

        if guild is not None:
            guild = from_dict(data_class=models.Guild, data=guild)
            self.cache.put("guilds", id, guild)

        return guild