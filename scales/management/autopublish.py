from dis_snek import slash_command, listen, Scale, InteractionContext, OptionTypes, slash_option, GuildChannel, Permissions, ChannelTypes
import models
from db import Update

from dis_snek.api.events import MessageCreate

class AutoPublish(Scale):
    
    @slash_command(name="autopublish", sub_cmd_name="toggle", sub_cmd_description="Toggle auto publishing for a channel")
    @slash_option(
        name="channel",
        description="The channel to auto publish news for",
        opt_type=OptionTypes.CHANNEL,
        channel_types=[ChannelTypes.GUILD_NEWS],
        required=True,
    )
    @slash_option(
        name="enabled",
        opt_type=OptionTypes.BOOLEAN,
        description="will enable or disable explicitly.",
        required=False,
    )
    async def modules(self, ctx: InteractionContext, channel: GuildChannel, enabled: bool = None):
        """
        Toggle auto publishing for a channel
        """
        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        if not ctx.author.has_permission(Permissions.MANAGE_GUILD):
            await ctx.send("You do not have permission to toggle auto publishing", ephemeral=True)
            return

        if enabled is None:
            enabled = not channel.id in guild.auto_publish_channels

        if enabled and channel.id not in guild.auto_publish_channels:
            await self.bot.db.update_guild(guild.id, Update().push(auto_publish_channels=channel.id))

        if not enabled and channel.id in guild.auto_publish_channels:
            await self.bot.db.update_guild(guild.id, Update().pull(auto_publish_channels=channel.id))

        await ctx.send(f"New messages will now automatically be published in {channel.mention}." if enabled else f"New messages will no longer automatically be published in {channel.mention}.", ephemeral=True)

    
    @listen()
    async def on_message_create(self, event: MessageCreate):
        if event.message.guild is None: return

        guild: models.Guild = await self.bot.db.fetch_guild(event.message.guild.id)

        if event.message.channel.id in guild.auto_publish_channels:
            await event.message.publish()

    
def setup(bot):
    AutoPublish(bot)