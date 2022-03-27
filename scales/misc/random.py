from dis_snek import slash_command, Scale, InteractionContext, OptionTypes, slash_option, SlashCommandChoice
import constants, random

class Random(Scale):
    
    @slash_command(name="random", description="yes")
    @slash_option(
        name="type",
        description="How random",
        opt_type=OptionTypes.STRING,
        required=False,
        choices=[
            SlashCommandChoice("Video", 'video'),
            SlashCommandChoice("Meme", 'meme'),
            SlashCommandChoice("Song", 'song')
        ]
    )
    async def rand(self, ctx: InteractionContext, type: str = None):
        """
        Post some random stuff
        """
        choice = random.choice(constants.RANDOMS.get(type) if type else [item for sublist in constants.RANDOMS.values() for item in sublist])

        await ctx.send(choice)
        
    
def setup(bot):
    Random(bot)