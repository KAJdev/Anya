from dis_snek import slash_command, InteractionCommand, Scale, InteractionContext, OptionTypes, slash_option, GuildChannel
import models

from models import ModuleToggles
from db import Update

class Modules(Scale):
    
    @slash_command(name="modules", sub_cmd_name="toggle", sub_cmd_description="Toggle a module on or off")
    @slash_option(
        name="module",
        description="The module you wish to toggle",
        opt_type=OptionTypes.STRING,
        required=True,
        autocomplete=True,
    )
    @slash_option(
        name="enabled",
        opt_type=OptionTypes.BOOLEAN,
        description="Setting will enable or disable the module.",
        required=False,
    )
    async def modules(self, ctx: InteractionContext, module: str, enabled: bool = None):
        """
        Toggle a module on or off
        """
        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        module = getattr(ModuleToggles, module, None)

        if module is None:
            await ctx.send("Module not found", ephemeral=True)
            return

        if enabled is None:
            enabled = not guild.module_enabled(module)
        
        if enabled:
            guild.modules |= module
        else:
            guild.modules &= ~module

        await self.bot.db.update_guild(guild.id, Update().set(modules=guild.modules))
        
        await ctx.send(f"Set {module} to {enabled}", ephemeral=True)

    
    @modules.autocomplete('module')
    async def modules_autocomplete(self, ctx: InteractionContext, module: str):
        """
        Autocomplete for the modules command
        """
        choices = [
            {"name": _module.replace('_', '').title(), "value": _module}
            for _module in ModuleToggles.get_modules()
            if module.lower().replace(' ', '_') in _module.lower()
        ]

        await ctx.send(choices=choices[:24])

    
def setup(bot):
    Modules(bot)