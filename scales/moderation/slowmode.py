from dis_snek import slash_command, InteractionCommand, Scale, InteractionContext, OptionTypes, slash_option, GuildChannel
import inspect

class Slowmode(Scale):
    
    @slash_command(name="slowmode", description="Set the slowmode for a channel")
    @slash_option(
        name="length",
        description="The length of the slowmode in seconds",
        opt_type=OptionTypes.INTEGER,
        max_value=21600,
        min_value=0,
        required=True,
    )
    @slash_option(
        name="channel",
        opt_type=OptionTypes.CHANNEL,
        description="The channel to set the slowmode for",
        required=False,
    )
    async def slowmode(self, ctx: InteractionContext, length: int, channel: str = None):
        """
        Set the slowmode for a channel
        """
        channel: GuildChannel = channel or ctx.channel

        if not channel.permissions_for(ctx.author).MANAGE_CHANNELS:
            await ctx.send("You do not have permission to manage channels", ephemeral=True)
            return

        await channel.edit(rate_limit_per_user=length)

        await ctx.send(f"Set slowmode for {channel.mention} to {length} seconds", ephemeral=True)
    
def setup(bot):
    Slowmode(bot)