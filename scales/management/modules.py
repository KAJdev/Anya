from naff import slash_command, InteractionCommand, Extension, InteractionContext, OptionTypes, slash_option, Permissions
import models

from models import ModuleToggles
from db import Update

class Modules(Extension):
    
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
    async def modules_toggle(self, ctx: InteractionContext, module: str, enabled: bool = None):
        """
        Toggle a module on or off
        """
        if not ctx.author.has_permission(Permissions.MANAGE_GUILD):
            await ctx.send("You do not have permission to toggle modules", ephemeral=True)
            return

        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        _module = getattr(ModuleToggles, module, None)

        if _module is None:
            await ctx.send("Module not found", ephemeral=True)
            return

        if enabled is None:
            enabled = not guild.module_enabled(_module)
        
        if enabled:
            guild.add_module(_module)
        else:
            guild.remove_module(_module)

        await self.bot.db.update_guild(guild.id, Update().set(modules=guild.modules))
        
        await ctx.send(f"{'enabled' if enabled else 'disabled'} `{module.replace('_', ' ').title()}`.", ephemeral=True)

    
    @modules_toggle.autocomplete('module')
    async def modules_autocomplete(self, ctx: InteractionContext, module: str):
        """
        Autocomplete for the modules command
        """
        choices = [
            {"name": _module.replace('_', ' ').title(), "value": _module}
            for _module in ModuleToggles.get_modules()
            if module.lower().replace(' ', '_') in _module.lower()
        ]

        await ctx.send(choices=choices[:24])


    @slash_command(name="modules", sub_cmd_name="view", sub_cmd_description="View modules and their current state")
    async def modules_view(self, ctx: InteractionContext):
        """
        View modules and their current state
        """
        if not ctx.author.has_permission(Permissions.MANAGE_GUILD):
            await ctx.send("You do not have permission to toggle modules", ephemeral=True)
            return

        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        modules = ModuleToggles(guild.modules)

        await ctx.send(
            "\n".join([f"**{module.name.replace('_', ' ').title()}**: `{'enabled' if ModuleToggles.has_module(modules, module) else 'disabled'}`" for module in ModuleToggles.__members__.values() if module is not ModuleToggles.NONE]),
            ephemeral=True
        )

    
def setup(bot):
    Modules(bot)