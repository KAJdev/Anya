from dataclasses import asdict
from naff import slash_command, listen, Extension, InteractionContext, Button, ComponentContext, Embed, EmbedField, component_callback, Member, Select, SelectOption, spread_to_rows
import models
from db import Update
import random
from datetime import datetime, timedelta
from naff.api.events import Component
from utils import time
import random

IDLE_ACTIONS = [
    "studying",
    "reading",
    "watching anime",
    "watching a movie",
    "training",
    "playing video games",
    "resting",
    "researching",
]

def get_missions() -> list[models.Mission]:
    # get hour of year
    hour_of_year = datetime.utcnow().timetuple().tm_yday * 24 + datetime.utcnow().hour

    # get missions
    random.seed(hour_of_year)
    return [models.Mission() for _ in range(5)]

async def render_dispatch_menu(ctx: InteractionContext, agent_id: str, mission_id: str, user: models.User) -> list:
    await ctx.edit_origin(embed=Embed(
        title="Dispatch an Agent",
        description="Select an agent to dispatch",
        color=0x2f3136,
    ), components=spread_to_rows(
        Select(
            custom_id=f"DISPATCH:agent:{agent_id or ''}:{mission_id or ''}",
            options=[
                SelectOption(
                    label=f"{agent.firstname.title()} {agent.lastname.title()}",
                    description=' / '.join(map(str, agent.stats.values())),
                    value=agent.id,
                    default=agent.id == agent_id,
                ) for agent in user.agents if agent.mission is None
            ]
        ),
        Select(
            custom_id=f"DISPATCH:mission:{agent_id or ''}:{mission_id or ''}",
            options=[
                SelectOption(
                    label=mission.name,
                    description=mission.description,
                    value=mission.id,
                    default=mission.id == mission_id,
                ) for mission in get_missions()
            ]
        ),
        Button(
            label="Back",
            style=2,
            custom_id=f"DISPATCH:back",
        ),
        Button(
            label="Dispatch",
            style=3,
            custom_id=f"DISPATCH:submit:{agent_id or ''}:{mission_id or ''}",
            disabled=not agent_id or not mission_id,
        ), max_in_row=2),
    )

class Headquarters(Extension):

    async def render_hq(self, author: Member, user: models.User) -> tuple[Embed, list]:

        completed_missions: Update = Update()

        brefings = []

        i = 0
        while i < len(user.agents):
            agent = user.agents[i]
            if agent.mission and agent.mission.ended():
                if agent.mission.complete(agent):
                    completed_missions.inc(peanuts=agent.mission.peanuts, world_peace=agent.mission.importance)
                    brefings.append(f"{agent.name} has completed a mission and gathered {agent.mission.peanuts} 🥜 and {agent.mission.importance} 🌍")
                    agent.mission = None
                else:
                    completed_missions.inc(world_peace=-agent.mission.importance)
                    brefings.append(f"{agent.name} has failed a mission. Their service will be remembered. {agent.mission.importance} 🌍 lost.")

                    # kill the agent
                    user.agents.remove(agent)
                    i -= 1
            i += 1

        if completed_missions:
            completed_missions.set(agents=[asdict(agent) for agent in user.agents])
            user = await self.bot.db.update_user(user.id, completed_missions)

        return Embed(
            title=f"{author}'s HQ",
            description=f"`{len(user.agents)}` 🕵️   `{user.peanuts:,}` 🥜   `{user.world_peace:,}` 🌍" + ("\n\nRecruit a new agent to start your mission!" if not user.agents else "") + "\n\n" + "\n".join(brefings),
            color=0x2f3136,
            fields=[
                EmbedField(
                    name=agent.name,
                    inline=True,
                    value=f"💤 {random.choice(IDLE_ACTIONS)}\n" + (' **/** '.join(map(str, agent.stats.values()))) if not agent.mission else f"⚡ {agent.mission.name}\n⏰ {time(agent.mission.ends_at, 'R')}",
                ).to_dict() for agent in user.agents
            ]
        ), [
            Button(
                label="Dispatch Agent",
                style=2,
                custom_id="DISPATCH",
                disabled=all(agent.mission is not None for agent in user.agents)
            ),
            Button(
                label="Recruit Agent",
                style=2,
                custom_id="RECRUIT",
                disabled=len(user.agents) >= 25,
            ),
        ]
    
    @slash_command(name="hq", description="View your HQ and all your spies")
    async def hq(self, ctx: InteractionContext):
        """
        View HQ
        """
        user: models.User = await self.bot.db.fetch_user(ctx.author.id)
        embed, components = await self.render_hq(ctx.author, user)
        await ctx.send(embed=embed, components=components, ephemeral=True)

    @component_callback("RENDERHQ")
    async def go_back(self, ctx: ComponentContext):
        user: models.User = await self.bot.db.fetch_user(ctx.author.id)
        embed, components = await self.render_hq(ctx.author, user)
        await ctx.edit_origin(embed=embed, components=components)
        

    @listen()
    async def on_component(self, event: Component):
        ctx: ComponentContext = event.context

        if not ctx.custom_id.startswith("DISPATCH"):
            return

        user: models.User = await self.bot.db.fetch_user(ctx.author.id)

        if all(agent.mission is not None for agent in user.agents):
            await ctx.send("All agents are busy!")
            return

        match ctx.custom_id.split(":")[1:]:
            case []:
                await render_dispatch_menu(ctx, "", "", user)
            case ["back"]:
                await self.go_back(ctx)
            case ["agent", agent_id, mission_id]:
                await render_dispatch_menu(ctx, ctx.values[0], mission_id, user)
            case ["mission", agent_id, mission_id]:
                await render_dispatch_menu(ctx, agent_id, ctx.values[0], user)
            case ["submit", agent_id, mission_id]:
                for agent in user.agents:
                    if agent.id == agent_id:
                        agent.mission = next(filter(lambda m: m.id == mission_id, get_missions()), None)
                        await self.bot.db.update_user(user.id, Update().set(agents=[asdict(agent) for agent in user.agents]))
                        await self.go_back(ctx)

    @component_callback("RECRUIT")
    async def recruit_agent_place_select(self, ctx: ComponentContext):
        user: models.User = await self.bot.db.fetch_user(ctx.author.id)

        if len(user.agents) <= 0:
            # first time recruiting
            prices = (0,0,0)
        else:
            prices = (100, 250, 500)

        await ctx.edit_origin(embed=Embed(
            title="Recruit an Agent",
            description="Choose a location to recruit an agent from",
            color=0x2f3136,
        ), components=[
            Button(
                label="Back",
                style=2,
                custom_id="RENDERHQ",
            ),
            Button(
                label=f"({prices[0]} 🥜) Bribe an allyway lurker",
                style=2,
                custom_id="BRIBE",
                disabled=user.peanuts < prices[0]
            ),
            Button(
                label=f"({prices[1]} 🥜) Coerce a blue collar worker",
                style=2,
                custom_id="COERCE",
                disabled=user.peanuts < prices[1]
            ),
            Button(
                label=f"({prices[2]} 🥜) Blackmail a high-ranking official",
                style=2,
                custom_id="BLACKMAIL",
                disabled=user.peanuts < prices[2]
            ),
        ])

    @component_callback("BRIBE", "COERCE", "BLACKMAIL")
    async def recruit_agent(self, ctx: ComponentContext):
        user: models.User = await self.bot.db.fetch_user(ctx.author.id)

        if len(user.agents) >= 25:
            await ctx.send("You can't recruit any more agents!")
            return

        new_agent: models.Agent = models.Agent()

        new_agent.generate_stats(*{
            "BRIBE": (1, 10),
            "COERCE": (5, 20),
            "BLACKMAIL": (15, 25),
        }.get(ctx.custom_id, ()))

        upd: Update = Update().push(agents=asdict(new_agent))

        if len(user.agents) > 0:
            upd.inc(peanuts=-{
                "BRIBE": 100,
                "COERCE": 250,
                "BLACKMAIL": 500,
            }.get(ctx.custom_id, 0))

        await self.bot.db.update_user(user.id, upd)

        await ctx.edit_origin(embed=Embed(
            title="You recruited an Agent",
            description=f"**{new_agent.name}**\n" + (' **/** '.join(map(str, new_agent.stats.values()))),
            color=0x2f3136,
        ), components=[
            Button(
                label="Back",
                style=2,
                custom_id="RENDERHQ",
            ),
            Button( 
                label="Recruit another agent",
                style=2,
                custom_id="RECRUIT",
                disabled=len(user.agents) + 1 >= 25,
            ),
        ])

    
def setup(bot):
    Headquarters(bot)