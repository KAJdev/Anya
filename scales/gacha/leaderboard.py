from curses import ACS_PI
from dataclasses import asdict
from dis_snek import slash_command, listen, Scale, InteractionContext, Button, ComponentContext, Embed, EmbedField, component_callback, Member, Select, SelectOption, spread_to_rows
import models
from db import Update
import random
from datetime import datetime, timedelta
from dis_snek.api.events import Component
from utils import time
import random
from dacite import from_dict

class Leaderboard(Scale):

    async def fetch_user_list(self, aspect: str = 'peanuts', length: int = 10) -> list[models.User]:
        return [from_dict(data_class=models.User, data=user) for user in (await self.bot.db.db.users.find({}).sort(aspect, -1).to_list(length=length))]
    
    @slash_command(name="leaderboard", description="View the spy leaderboard")
    async def leaderboard_command(self, ctx: InteractionContext):
        """
        View the spy leaderboard
        """
        users = await self.fetch_user_list()
        embed = Embed(
            title="Leaderboard",
            description="\n".join(f"{i+1}. {user.firstname.title()} {user.lastname.title()} - {user.peanuts}" for i, user in enumerate(users)),
            color=0x2f3136,
        )
        await ctx.reply(embed=embed)
    
def setup(bot):
    Leaderboard(bot)