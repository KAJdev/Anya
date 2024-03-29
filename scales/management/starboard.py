import asyncio
from audioop import add
from dataclasses import dataclass, field
import datetime
import random
from dacite import from_dict
from naff import Color, Embed, EmbedAuthor, EmbedFooter, IntervalTrigger, Member, Message, Task, User, slash_command, listen, Extension, InteractionContext, OptionTypes, slash_option, GuildChannel, Permissions
import models

from models import ModuleToggles, StarboardMessage
from db import Update

from naff.api.events import MessageReactionAdd, MessageCreate, MessageUpdate

REPLY_FACTOR = 0.75
REACT_SCORE = 1

MIN_SCORE = 4

@dataclass(slots=True)
class PredicateStarMessage:
    message: Message
    additional_reactions: int
    replies: list[int] = field(default_factory=list)

    @property
    def score(self) -> int:
        return (len(self.replies) * REPLY_FACTOR) + (self.additional_reactions * REACT_SCORE)

class Starboard(Extension):

    def __init__(self, bot):
        super().__init__()

        self.predicate_star_messages: dict[int, PredicateStarMessage] = {}
        self.starboard_message_cache: dict[int, dict[int, StarboardMessage]] = {}
        self.messages_to_update: list[PredicateStarMessage] = []

    def add_starboard_message_to_cache(self, msg: StarboardMessage):
        self.starboard_message_cache.setdefault(msg.guild_id, {})[msg.message_id] = msg

    def render_starboard_post(self, message: Message, reply_count: int, additional_reactions: int):
        footer_text = []

        if reply_count == 1:
            footer_text.append("1 reply")
        elif reply_count > 1:
            footer_text.append(f"{reply_count} replies")

        if additional_reactions == 1:
            footer_text.append("1 reaction")
        elif additional_reactions > 0:
            footer_text.append(f"{additional_reactions} reactions")

        if isinstance(message.author, Member):
            author = EmbedAuthor(
                name=message.author.display_name,
                icon_url=message.author.display_avatar.url
            )
        elif isinstance(message.author, User):
            author = EmbedAuthor(
                name=message.author.username,
                icon_url=message.author.avatar.url
            )

        embed = Embed(
            title=f'#{message.channel.name}',
            url=message.jump_url,
            description=message.content,
            author=author,
            footer=EmbedFooter(
                text="  ".join(footer_text)
            ),
            color=Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        )

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        if message.embeds:
            embed.set_thumbnail(url=getattr(getattr(message.embeds[0], "thumbnail", None), 'url', None))

        return embed


    @Task.create(IntervalTrigger(minutes=2))
    async def starboard_loop(self):
        for predicate in self.messages_to_update:
            guild: models.Guild = await self.bot.db.fetch_guild(predicate.message.guild.id)

            if guild.module_enabled(ModuleToggles.STARBOARD) and guild.starboard_channel:
                channel = await self.bot.fetch_channel(guild.starboard_channel)

                if channel is not None:

                    msg = await self.bot.http.edit_message({
                        'embeds': [self.render_starboard_post(predicate.message, len(predicate.replies), predicate.additional_reactions).to_dict()],
                    }, channel.id, predicate.message.id)

                    if msg:
                        msg = Message.from_dict(msg)

                        # update the message in the database
                        await self.bot.db.update_starboard_message(msg, predicate)

                        # update the message in the cache
                        self.starboard_message_cache[msg.guild.id][msg.id] = msg

                        # remove the previous message from the cache
                        del self.starboard_message_cache[msg.guild.id][predicate.message.id]

        self.messages_to_update = []
                    

    async def calculate_message_score(self, message: Message, reply_id: int = None):
        new_reaction_score = 0

        for reaction in message.reactions:
            new_reaction_score += max(reaction.count - 1, 0)

        new_reaction_score *= REACT_SCORE

        if message.id not in self.predicate_star_messages:
            self.predicate_star_messages[message.id] = PredicateStarMessage(
                message=message,
                additional_reactions=new_reaction_score
            )

        else:
            self.predicate_star_messages[message.id].additional_reactions = new_reaction_score
            self.predicate_star_messages[message.id].message = message

        if reply_id is not None and reply_id not in self.predicate_star_messages[message.id].replies:
            self.predicate_star_messages[message.id].replies.append(reply_id)

        if self.predicate_star_messages[message.id].score >= MIN_SCORE:
            if message.id not in self.starboard_message_cache.setdefault(message.guild.id, {}):
                await self.post_starboard_message(message, self.predicate_star_messages[message.id])
            else:
                self.messages_to_update.append(self.predicate_star_messages[message.id])

            if message.id in self.predicate_star_messages:
                del self.predicate_star_messages[message.id]

    async def post_starboard_message(self, message: Message, predicate: PredicateStarMessage):
        guild: models.Guild = await self.bot.db.fetch_guild(message.guild.id)
        channel = await self.bot.fetch_channel(guild.starboard_channel)

        if channel is not None:

            check = await self.bot.db._fetch("starboard_messages", {"message_id": message.id})

            if check is not None:
                return

            msg = await channel.send(embed=self.render_starboard_post(message, len(predicate.replies), predicate.additional_reactions))

            # save the message to the database
            new_post = await self.bot.db.save_starboard_message(msg, predicate)

            # add the new message to the cache
            self.add_starboard_message_to_cache(new_post)

    
    @slash_command(name="starboard", sub_cmd_name="channel", sub_cmd_description="Set the channel where starboard messages will appear")
    @slash_option(
        name="channel",
        description="The channel to post starboard messages to",
        opt_type=OptionTypes.CHANNEL,
        required=True,
    )
    async def starboard_channel(self, ctx: InteractionContext, channel: GuildChannel):
        """
        Set the channel where starboard messages will appear
        """
        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        if not ctx.author.has_permission(Permissions.MANAGE_GUILD):
            await ctx.send("You do not have permission to manage the starboard", ephemeral=True)
            return

        await self.bot.db.update_guild(guild.id, Update().set(starboard_channel=channel.id))

        await ctx.send(f"Starboard messages will now appear in {channel.mention}.", ephemeral=True)

    @listen()
    async def on_ready(self):
        # wait for the database to be ready (little hacky)
        await asyncio.sleep(5)

        self.bot.info("Populating starboard cache")

        self.starboard_message_cache = {}

        # fetch the last couple of messages from the starboard channel
        last = await self.bot.db._fetch("starboard_messages", {'posted': {'$gte':datetime.datetime.utcnow() - datetime.timedelta(days=14)}}, limit=500)

        for message in last:
            self.add_starboard_message_to_cache(from_dict(models.StarboardMessage, message))

        self.bot.info(f"Starboard cache populated with {len(self.starboard_message_cache)} messages")

        self.starboard_loop.start()
    
    @listen()
    async def on_message_reaction_add(self, event: MessageReactionAdd):
        if event.message.guild is None: return

        guild: models.Guild = await self.bot.db.fetch_guild(event.message.guild.id)

        if guild.module_enabled(ModuleToggles.STARBOARD):
            if event.message.channel.id == guild.starboard_channel:
                return

            # respect the allowed starboard channels
            allowed = guild.starboard_overrides.get(str(event.message.channel.id), True)

            if pc := getattr(event.message.channel, "parent_id", None) is not None:
                allowed = guild.starboard_overrides.get(str(pc), True)

            if allowed:
                await self.calculate_message_score(event.message)

    @listen()
    async def on_message_create(self, event: MessageCreate):
        if event.message.guild is None: return

        guild: models.Guild = await self.bot.db.fetch_guild(event.message.guild.id)

        if guild.module_enabled(ModuleToggles.STARBOARD):
            if event.message.channel.id == guild.starboard_channel:
                return

            # respect the allowed starboard channels
            allowed = guild.starboard_overrides.get(str(event.message.channel.id), True)

            if pc := getattr(event.message.channel, "parent_id", None) is not None:
                allowed = guild.starboard_overrides.get(str(pc), True)

            if allowed:
                referenced = await event.message.fetch_referenced_message()

                if referenced is not None and referenced.author.id != event.message.author.id:
                    await self.calculate_message_score(referenced, event.message.id)


    # @listen()
    # async def on_message_update(self, event: MessageUpdate):
    #     if event.after.guild is None: return

    #     guild: models.Guild = await self.bot.db.fetch_guild(event.after.guild.id)

    #     if guild.module_enabled(ModuleToggles.STARBOARD):
    #         if event.after.channel.id == guild.starboard_channel:
    #             return

    #         if event.after.id in self.starboard_message_cache.setdefault(event.after.guild.id, {}):
    #             await self.calculate_message_score(event.after)

    @slash_command(name="starboard", sub_cmd_name="toggle", sub_cmd_description="Toggle the ability to put msgs on the starboard for a channel")
    @slash_option(
        name="channel",
        description="The channel to allow/deny starboard msgs for",
        opt_type=OptionTypes.CHANNEL,
        required=True,
    )
    @slash_option(
        name="enabled",
        opt_type=OptionTypes.BOOLEAN,
        description="will enable or disable explicitly.",
        required=False,
    )
    async def starboard_toggle(self, ctx: InteractionContext, channel: GuildChannel, enabled: bool = None):
        """
        toggle auto threading for a channel
        """
        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        if not ctx.author.has_permission(Permissions.MANAGE_GUILD):
            await ctx.send("You do not have permission to toggle starboarding messages for channels", ephemeral=True)
            return

        if enabled is None:
            enabled = not guild.starboard_overrides.get(str(channel.id), True)

        await self.bot.db.update_guild(guild.id, {'$set': {f'starboard_overrides.{channel.id}': enabled}})

        await ctx.send(f"Popular messages in {channel.mention} will be posted on the starboard." if enabled else f"No messages from {channel.mention} will be posted on the starboard.", ephemeral=True)


    @slash_command(name="starboard", sub_cmd_name="overrides", sub_cmd_description="View the starboard overrides for this server")
    async def starboard_overrides(self, ctx: InteractionContext):
        """
        view the starboard overrides for this server
        """
        guild: models.Guild = await self.bot.db.fetch_guild(ctx.guild.id)

        if not ctx.author.has_permission(Permissions.MANAGE_GUILD):
            await ctx.send("You do not have permission to view starboard overrides", ephemeral=True)
            return

        overrides = guild.starboard_overrides

        if not overrides:
            await ctx.send("No overrides set", ephemeral=True)
            return

        embed = Embed(title="Starboard Overrides", color=0xFFD700)

        for channel_id, enabled in overrides.items():
            channel: GuildChannel = ctx.guild.get_channel(int(channel_id))

            if channel is None:
                continue

            embed.add_field(name=channel.name, value=f"Enabled: {enabled}")

        await ctx.send(embed=embed)
    
def setup(bot):
    Starboard(bot)