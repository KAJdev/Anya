import aiohttp
from dis_snek import listen, Scale, Webhook, File
import re, models, aiohttp, io

from dis_snek.api.events import MessageCreate, MessageUpdate

twitter_link_regex = re.compile(r'https?:\/\/(?:.*\.)?(?:twitter\.com|t\.co)\/(?:[^\/]*\/)?(\w+)\/status\/(\d+)')

class Fxtwitter(Scale):

    @listen()
    async def on_message_create(self, event: MessageCreate):
        message = event.message

        if message.author.bot:
            return

        # extract the twitter link from the message link
        twitter_link = re.search(twitter_link_regex, message.content or "")

        # fetch the message if there is one
        if twitter_link:
            guild_stuff: models.Guild = await self.bot.db.fetch_guild(message.guild.id)

            if not guild_stuff.module_enabled(models.ModuleToggles.FXTWITTER):
                return

            # clear the embeds
            await message.suppress_embeds()

            # send the better twitter link
            await message.reply(
                content=twitter_link.group().replace("twitter.com", "fxtwitter.com")
            )

    
def setup(bot):
    Fxtwitter(bot)