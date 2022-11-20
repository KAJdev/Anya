import aiohttp
from naff import listen, Extension, Webhook, File
import re, models, aiohttp, io

from naff.api.events import MessageCreate, MessageUpdate

twitter_link_regex = re.compile(r'https?:\/\/(?:.*\.)?(?:twitter\.com|t\.co)\/(?:[^\/]*\/)?(\w+)\/status\/(\d+)')

class Vxtwitter(Extension):

    @listen()
    async def on_message_update(self, event: MessageUpdate):
        message = event.after

        if message.author.bot:
            return

        # extract the twitter link from the message link
        twitter_link = re.search(twitter_link_regex, message.content or "")

        # fetch the message if there is one
        if twitter_link and any(['https://twitter.com/i/videos' in embed.url for embed in message.embeds]):
            guild_stuff: models.Guild = await self.bot.db.fetch_guild(message.guild.id)

            if not guild_stuff.module_enabled(models.ModuleToggles.VXTWITTER):
                return

            # clear the embeds
            await message.suppress_embeds()

            # send the better twitter link
            await message.reply(
                content=twitter_link.group().replace("twitter.com", "vxtwitter.com")
            )

    
def setup(bot):
    Vxtwitter(bot)