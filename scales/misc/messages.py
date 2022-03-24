import aiohttp
from dis_snek import listen, Scale, Webhook, File
import re, models, aiohttp, io

from dis_snek.api.events import MessageCreate

message_link_regex = re.compile(r'https?:\/\/(?:.*\.)?(?:discord(?:app)?\.com|discord\.gg)\/channels\/(\d+)\/(\d+)\/(\d+)')
message_id_regex = re.compile(r'\d+')

class Messages(Scale):
    
    @listen()
    async def on_message_create(self, event: MessageCreate):
        message = event.message

        if message.author.bot:
            return

        guild = channel = message_id = None

        # extract the message id from the message link
        message_link = re.search(message_link_regex, message.content or "")
        if message_link:
            guild, channel, message_id = message_link.groups()
        
        elif message_id := re.search(message_id_regex, message.content or ""):
            guild = str(message.guild.id)
            channel = str(message.channel.id)
            message_id = message_id.group()

        # fetch the message if there is one
        if message_id and guild and channel:
            # guild_stuff: models.Guild = await self.bot.db.fetch_guild(guild)

            # if not guild_stuff.module_enabled(models.ModuleToggles.MESSAGE_REFERENCES):
            #     return

            referenced_message = await (await self.bot.fetch_channel(channel)).fetch_message(message_id)

            # get the webhooks for the channel
            webhooks = await message.channel.fetch_webhooks()

            anyas_webhook: Webhook = None

            # look for one named "Anya Message References"
            for webhook in webhooks:
                if webhook.name == 'Anya Message References':
                    anyas_webhook = webhook
                    break
            else:
                # if there is none, create one
                anyas_webhook = await message.channel.create_webhook(name='Anya Message References')

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
            )

    
def setup(bot):
    Messages(bot)