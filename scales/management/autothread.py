from naff import slash_command, listen, Extension, InteractionContext, OptionTypes, slash_option, GuildChannel, Permissions
import models

from models import ModuleToggles
from db import Update

from naff.api.events import MessageCreate

class AutoThread(Extension):
    
    @slash_command(name="autothread", sub_cmd_name="toggle", sub_cmd_description="Toggle autothread for a channel")
    @slash_option(
        name="channel",
        description="The channel to auto create threads for",
        opt_type=OptionTypes.CHANNEL,
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
        toggle auto threading for a channel
        """
        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        if not ctx.author.has_permission(Permissions.MANAGE_GUILD):
            await ctx.send("You do not have permission to toggle auto threading", ephemeral=True)
            return

        if enabled is None:
            enabled = not channel.id in guild.auto_thread_channels

        if enabled and channel.id not in guild.auto_thread_channels:
            await self.bot.db.update_guild(guild.id, Update().push(auto_thread_channels=channel.id))

        if not enabled and channel.id in guild.auto_thread_channels:
            await self.bot.db.update_guild(guild.id, Update().pull(auto_thread_channels=channel.id))

        await ctx.send(f"New messages will now automatically create threads in {channel.mention}." if enabled else f"New messages will no longer automatically create threads in {channel.mention}.", ephemeral=True)

    
    @listen()
    async def on_message_create(self, event: MessageCreate):
        if event.message.guild is None: return

        guild: models.Guild = await self.bot.db.fetch_guild(event.message.guild.id)

        if event.message.channel.id in guild.auto_thread_channels:
            await event.message.create_thread(
                name=event.message.content[:50],
                reason="Auto thread created",
            )

    
def setup(bot):
    AutoThread(bot)