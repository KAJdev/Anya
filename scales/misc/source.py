import io
import json
from naff import Message, slash_command, InteractionCommand, Extension, InteractionContext, OptionTypes, slash_option, File, context_menu, CommandTypes
import inspect, models

class Source(Extension):

    @context_menu(name="Get Message Source", context_type=CommandTypes.MESSAGE)
    async def get_source(self, ctx: InteractionContext):
        with io.StringIO() as f:
            f.write(json.dumps(list(ctx.resolved.messages.values())[0].to_dict(), indent=2))
            f.seek(0)
            await ctx.send(file=File(f, file_name="message.json"))
    
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

        command: InteractionCommand = next(filter(lambda x: x.name == command.split()[0] and (x.sub_cmd_name == command.split()[1] if len(command.split()) > 1 else True), self.bot.application_commands), None)
        if not command:
            await ctx.send("Command not found")
            return

        _source = inspect.getsource(command.callback.func).replace("```py\n", "").replace("```", "")

        if len(_source) + 10 > 2000:
            await ctx.send(file=File(io.BytesIO(_source.encode()), file_name=f"{command.name}.py"))
        else:
            await ctx.send(f"```py\n{_source}```")

    @source.autocomplete('command')
    async def source_autocomplete(self, ctx: InteractionContext, command: str):
        """
        Autocomplete for the source command
        """

        choices = [
            {
                "name": _command.name + (f" {_command.sub_cmd_name}" if getattr(_command, "sub_cmd_name", None) else ""),
                "value": _command.name + (f" {_command.sub_cmd_name}" if getattr(_command, "sub_cmd_name", None) else "")
            }
            for _command in self.bot.application_commands
            if command.lower() in _command.name.lower()
        ]

        await ctx.send(choices=choices[:24])
    
def setup(bot):
    Source(bot)