from dis_snek import slash_command, InteractionCommand, Scale, InteractionContext, OptionTypes, slash_option
import inspect

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
        command: InteractionCommand = next(filter(lambda x: x.name == command, self.bot.application_commands), None)
        if not command:
            await ctx.send("Command not found")
            return
        
        _source = inspect.getsource(command.callback)
        _source = _source.replace("```py\n", "").replace("```", "")
        
        await ctx.send(_source)

    @source.autocomplete('command')
    async def source_autocomplete(self, ctx: InteractionContext, query: str):
        """
        Autocomplete for the source command
        """

        choices = [
            {"name": command.name, "value": command.name}
            for command in self.bot.application_commands
            if query.lower() in command.name.lower()
        ]

        await ctx.send(choices=choices[:24])
    
def setup(bot):
    Source(bot)