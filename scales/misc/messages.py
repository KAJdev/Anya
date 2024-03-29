from lib2to3.pytree import Base
import aiohttp
from naff import listen, Extension, Webhook, File, Message, GuildText, AllowedMentions, BaseChannel, ThreadChannel
import re, models, aiohttp, io

from naff.api.events import MessageCreate
from naff.client.errors import NotFound

message_link_regex = re.compile(r'https?:\/\/(?:.*\.)?(?:discord(?:app)?\.com|discord\.gg)\/channels\/(\d+)\/(\d+)\/(\d+)')
message_id_regex = re.compile(r'(\d+){10,}')

def get_context(message: Message):
    guild = channel = message_id = None

    # extract the message id from the message link
    message_link = re.search(message_link_regex, message.content or "")
    if message_link:
        guild, channel, message_id = message_link.groups()
    
    elif message_id := re.search(message_id_regex, message.content or ""):
        guild = str(message.guild.id)
        channel = str(message.channel.id)
        message_id = message_id.group()

    return guild, channel, message_id

async def get_anya_hook(channel: BaseChannel) -> Webhook:
    # get the webhooks for the channel
    webhooks = await channel.fetch_webhooks()

    # look for one named "Anya Message References"
    for webhook in webhooks:
        if webhook.name == 'Anya Message References':
            return webhook
    else:
        # if there is none, create one
        return await channel.create_webhook(name='Anya Message References')

class Messages(Extension):
    
    @listen()
    async def on_message_create(self, event: MessageCreate):
        message = event.message

        if message.author.bot:
            return

        guild, channel, message_id = get_context(message)

        # fetch the message if there is one
        if guild and channel and message_id:
            guild_stuff: models.Guild = await self.bot.db.fetch_guild(int(guild))

            if not guild_stuff.module_enabled(models.ModuleToggles.MESSAGE_REFERENCES):
                return

            try:
                referenced_message = await (await self.bot.fetch_channel(channel)).fetch_message(message_id)
            except NotFound:
                return

            if not referenced_message:
                return

            thread = None

            if pc := event.message.channel.__dict__.get('parent_id') is not None:
                print(pc)
                thread = message.channel.id
                anyas_webhook: Webhook = await get_anya_hook(await self.bot.fetch_channel(pc))

            else:
                anyas_webhook: Webhook = await get_anya_hook(message.channel)

            # make own attachments
            attachments = []
            for attachment in referenced_message.attachments:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as resp:
                        attachments.append(File(io.BytesIO(await resp.read()), file_name=attachment.filename))

            # send the message to the webhook
            await anyas_webhook.send(
                content=referenced_message.content,
                username=f"{referenced_message.author.username}#{referenced_message.author.discriminator} [MESSAGE REFERENCE]" if not referenced_message.author.username.endswith(" [MESSAGE REFERENCE]") else referenced_message.author.username,
                avatar_url=referenced_message.author.avatar.url,
                embeds=referenced_message.embeds,
                files=attachments,
                allowed_mentions=AllowedMentions(parse=[], users=[], roles=[]),
                thread=thread,
            )

    
def setup(bot):
    Messages(bot)