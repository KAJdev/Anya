import asyncio
from datetime import datetime
from dis_snek import slash_command, Scale, InteractionContext, OptionTypes, slash_option, SlashCommandChoice, Message, listen
import random

import models

from dis_snek.api.events import MessageCreate

class Random(Scale):

    def __init__(self, bot):
        super().__init__()
        self.randoms = {
            'video': [],
            'meme': [],
            'song': [],
        }

    @listen()
    async def on_ready(self):
        await self.pull_randoms()
        
    async def pull_randoms(self):
        all_randoms = await self.bot.db._fetch("randoms", {}, limit=None)

        self.randoms = {
            'video': [],
            'meme': [],
            'song': [],
        }

        for random in all_randoms:
            self.randoms[random['type']].append(random['url'])
    
    @slash_command(name="random", description="yes")
    @slash_option(
        name="type",
        description="How random",
        opt_type=OptionTypes.STRING,
        required=False,
        choices=[
            SlashCommandChoice("Video", 'video'),
            SlashCommandChoice("Meme", 'meme'),
            SlashCommandChoice("Song", 'song')
        ]
    )
    async def rand(self, ctx: InteractionContext, type: str = None):
        """
        Post some random stuff
        """
        choice = random.choice(self.randoms.get(type) if type else [item for sublist in self.randoms.values() for item in sublist])

        await ctx.send(choice)

    @listen()
    async def on_message_create(self, event: MessageCreate):
        message: Message = event.message

        if not message.content:
            return

        match message.content.split():
            case ["?random", action, type, *urls]:

                user: models.User = await self.bot.db.fetch_user(event.message.author.id)

                if user.has_permision(models.AnyaPermissions.ADD_RANDOMS):

                    if type not in self.randoms:
                        await message.reply("Invalid type")
                        return

                    if action == "add":
                        await self.bot.db._insert("randoms", [{
                            'url': url,
                            'type': type,
                            'added_by': user.id,
                            'added_at': datetime.utcnow()
                        } for url in urls])

                        self.randoms[type].extend(urls)

                        await message.reply(f"Added {', '.join('<'+url+'>' for url in urls)} to the {type} random list")

                    elif action == "remove":
                        await self.bot.db._delete("randoms", {
                            'url': {'$in': urls},
                            'type': type
                        }, many=True)

                        for url in urls:
                            if url in self.randoms[type]:
                                self.randoms[type].remove(url)

                        await message.reply(f"Removed {', '.join('<'+url+'>' for url in urls)} from the {type} random list")
                    else:
                        await message.reply("Invalid action")

        
    
def setup(bot):
    Random(bot)