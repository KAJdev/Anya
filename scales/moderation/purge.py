import re
import time
from naff import slash_command, InteractionCommand, Extension, InteractionContext, OptionTypes, slash_option, GuildChannel, DISCORD_EPOCH
import inspect

user_id_regex = re.compile(r"<@!?(\d+)>")

class Purge(Extension):
    
    @slash_command(name="purge", description="Purge messages based on many filters")
    @slash_option(
        name="limit",
        description="The number of messages to delete",
        opt_type=OptionTypes.INTEGER,
        max_value=500,
        min_value=1,
        required=True,
    )
    @slash_option(
        name="users",
        description="Users to purge messages from.",
        opt_type=OptionTypes.STRING,
        required=False,
    )
    @slash_option(
        name="contains",
        description="The string to search for in the message content.",
        opt_type=OptionTypes.STRING,
        required=False,
    )
    @slash_option(
        name="regex",
        description="Delete messages that match this regular expression.",
        opt_type=OptionTypes.STRING,
        required=False,
    )
    @slash_option(
        name="starts_with",
        description="The string to search for at the start of the message content",
        opt_type=OptionTypes.STRING,
        required=False,
    )
    @slash_option(
        name="ends_with",
        description="The string to search for at the end of the message content",
        opt_type=OptionTypes.STRING,
        required=False,
    )
    @slash_option(
        name="skip",
        description="How many messages to skip before applying filters.",
        opt_type=OptionTypes.INTEGER,
        required=False,
        min_value=1,
        max_value=100,
    )
    @slash_option(
        name="is_pinned",
        description="Whether or not to delete pinned messages",
        opt_type=OptionTypes.BOOLEAN,
        required=False,
    )
    @slash_option(
        name="bots",
        description="Whether or not to delete bot messages",
        opt_type=OptionTypes.BOOLEAN,
        required=False,
    )
    @slash_option(
        name="attachments",
        description="Whether or not to delete messages with attachments",
        opt_type=OptionTypes.BOOLEAN,
        required=False,
    )
    @slash_option(
        name="channel",
        opt_type=OptionTypes.CHANNEL,
        description="The channel to purge messages from",
        required=False,
    )
    async def purge(
        self,
        ctx: InteractionContext,
        limit: int,
        users: str = None,
        contains: str = None,
        regex: str = None,
        starts_with: str = None,
        ends_with: str = None,
        skip: int = 0,
        is_pinned: bool = None,
        bots: bool = None,
        attachments: bool = None,
        channel: str = None
    ):
        """
        Purge messages based on many filters
        """
        channel: GuildChannel = channel or ctx.channel
        
        if not channel.permissions_for(ctx.author).MANAGE_MESSAGES:
            await ctx.send("You do not have permission to manage messages", ephemeral=True)
            return
        
        to_delete = []
        i = 0

        await ctx.defer(ephemeral=True)

        old_warning = False

        user_dict = {}

        # 1209600 14 days ago in seconds, 1420070400000 is used to convert to snowflake
        fourteen_days_ago = int((time.time() - 1209600) * 1000.0 - DISCORD_EPOCH) << 22
        async for message in channel.history(limit=5000):

            if i < skip:
                i += 1
                continue

            if message.id < fourteen_days_ago:
                old_warning = True
                break

            if len(to_delete) >= limit:
                break

            if (
                (users and str(message.author.id) not in users) or
                (contains and contains not in message.content) or
                (regex and not re.search(regex, message.content)) or
                (starts_with and not message.content.startswith(starts_with)) or
                (ends_with and not message.content.endswith(ends_with)) or
                (is_pinned is not None and message.pinned != is_pinned) or
                (bots is not None and message.author.bot != bots) or
                (attachments is not None and bool(message.attachments) != attachments)
            ):
                continue

            to_delete.append(message.id)
            user_dict[str(message.author)] = user_dict.get(str(message.author), 0) + 1

        count = len(to_delete)
        while to_delete:
            iteration = [to_delete.pop() for i in range(min(100, len(to_delete)))]
            await channel.delete_messages(iteration, reason=f"Purge by {ctx.author}")
        
        await ctx.send(f"Deleted {count} messages.{' (Messages older than 14 days cannot be purged)' if old_warning else ''}\n\n" + '\n'.join(f"**{author}**: `{number}`" for author,number in user_dict.items()), ephemeral=True)
    
def setup(bot):
    Purge(bot)