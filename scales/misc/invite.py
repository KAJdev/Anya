from dis_snek import slash_command, Scale, InteractionContext, OptionTypes, slash_option

class Invite(Scale):
    
    @slash_command(name="invite", description="Add me to your server")
    @slash_option(
        name="admin",
        description="Invite with admin perms",
        opt_type=OptionTypes.BOOLEAN,
        required=False,
    )
    async def invite(self, ctx: InteractionContext, admin: bool = False):
        """
        Add me to your server
        """
        await ctx.send(f"https://discord.com/api/oauth2/authorize?client_id={self.bot.application_id}&permissions={8 if admin else 120796342336}&scope=bot%20applications.commands")
    
def setup(bot):
    Invite(bot)