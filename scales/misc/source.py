from dis_snek import slash_command, InteractionCommand, Scale, InteractionContext, OptionTypes, slash_option
import inspect, models

class Source(Scale):
    
    @slash_command(name="source", description="Get the source code for a command")
    @slash_option(
        name="command",
        opt_type=OptionTypes.STRING,
        description="The command to get the source code for",
        required=True,
        autocomplete=True
    )
    async def source(self, ctx: InteractionContext, command: str):
        """
        Get the source code from self.bot.application_commands
        """
        # user: models.User = await self.bot.db.fetch_user(ctx.author.id)

        # if not user.has_permission(models.AnyaPermissions.VIEW_SOURCE):
        #     await ctx.send("You do not have permission to view source code", ephemeral=True)
        #     return

        command: InteractionCommand = next(filter(lambda x: x.name == command, self.bot.application_commands), None)
        if not command:
            await ctx.send("Command not found")
            return

        _source = inspect.getsource(command.callback.func)
        _source = _source.replace("```py\n", "").replace("```", "")
        
        await ctx.send(f"```py\n{_source}```")

    @source.autocomplete('command')
    async def source_autocomplete(self, ctx: InteractionContext, command: str):
        """
        Autocomplete for the source command
        """

        choices = [
            {"name": _command.name, "value": _command.name}
            for _command in self.bot.application_commands
            if command.lower() in _command.name.lower()
        ]

        await ctx.send(choices=choices[:24])
    
def setup(bot):
    Source(bot)