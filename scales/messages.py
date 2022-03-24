from asyncore import dispatcher_with_send
from dacite import from_dict
from dis_snek import slash_command, Button, ButtonStyles, listen, Embed, Scale, Modal, ShortText, ParagraphText, InteractionContext, OptionTypes, slash_attachment_option, ModalContext, auto_defer, slash_option
import os
import models
import re

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
            referenced_message = await (await self.bot.fetch_channel(channel)).fetch_message(message_id)

            # get the webhooks for the channel
            webhooks = await message.channel.fetch_webhooks()

            anyas_webhook = None

            # look for one named "Anya Message References"
            for webhook in webhooks:
                if webhook.name == 'Anya Message References':
                    anyas_webhook = webhook
                    break
            else:
                # if there is none, create one
                anyas_webhook = await message.channel.create_webhook(name='Anya Message References', avatar=self.bot.user.avatar.url)

            # send the message to the webhook
            await anyas_webhook.send(
                content=referenced_message.content,
                username=f"{referenced_message.author.username}#{referenced_message.author.discriminator} [MESSAGE REFERENCE]" if not referenced_message.author.username.endswith(" [MESSAGE REFERENCE]") else referenced_message.author.username,
                avatar_url=referenced_message.author.avatar.url,
                embeds=referenced_message.embeds
            )

    
def setup(bot):
    Messages(bot)