import asyncio
from contextlib import suppress
from attr import define
import dotenv
import os
import logging
import random

import dis_snek
from dis_snek.client import Snake
from dis_snek.client.errors import CommandCheckFailure
from dis_snek import InteractionContext
from dis_snek import ActivityType, Intents, Status, Button, ButtonStyles
from dis_snek import listen
from dis_snek import AutoDefer
from dis_snek import Activity
from dis_snek.api.events import BaseEvent

import scales
import db
import models

dotenv.load_dotenv()
logging.basicConfig()
cls_log = logging.getLogger(dis_snek.logger_name)
cls_log.setLevel(logging.INFO)

bot_log = logging.getLogger('anya')
bot_log.setLevel(logging.DEBUG)

@define(slots=False, kw_only=False)
class DatabaseReady(BaseEvent):
    """
    An event called when the database is ready
    """
    db: db.Database

class Bot(Snake):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = None
        
        for module in scales.default:
            self.grow_scale(f"scales.{module}")

        self.info = lambda *args, **kwargs: bot_log.info(*args, **kwargs)
        self.debug = lambda *args, **kwargs: bot_log.debug(*args, **kwargs)
        self.error = lambda *args, **kwargs: bot_log.error(*args, **kwargs)

        self.info("Bot object created. Connecting to Gateway.")

    @listen()
    async def on_ready(self):
        self.info("Gateway connected. Bot ready.")

        self.db = db.Database(asyncio.get_event_loop())

        self.dispatch(DatabaseReady(db=self.db))

        await self.change_presence(
            activity=Activity(
                name=random.choice(["minds.", "thoughts.", "feelings.", "spies and assasins."]),
                type=ActivityType.LISTENING
            ),
            status=Status.ONLINE
        )

    async def on_command_error(self, ctx: InteractionContext, error: Exception):
        match error:
            case CommandCheckFailure():
                if error.check.__name__ == 'is_manager':
                    await ctx.send(f'You must have the `Manage Server` permission to use this command.', ephemeral=True)
                    return
        await super().on_command_error(ctx, error)

if __name__ == "__main__":
    bot = Bot(
        intents=Intents.GUILDS | Intents.MESSAGES | 1 << 15 | Intents.REACTIONS,
        sync_interactions=True,
        delete_unused_application_cmds=False,
        # auto_defer=AutoDefer(
        #     enabled=True,
        #     ephemeral=True,
        #     time_until_defer=0
        # ),
        activity=Activity(
            name="the gears turn...",
            type=ActivityType.WATCHING
        ),
        status=Status.IDLE,
        total_shards=int(os.environ.get("TOTAL_SHARDS", 1)),
        shard_id=int(os.environ.get("SHARD", 0)),
    )
    bot.start(os.getenv('TOKEN'))