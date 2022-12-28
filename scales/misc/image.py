import asyncio
from datetime import datetime
import aiohttp
from naff import Embed, EmbedAttachment, slash_command, Extension, InteractionContext, OptionTypes, slash_option, SlashCommandChoice, Message, listen
import random
from main import DatabaseReady

import models

from naff.api.events import MessageCreate

ENDPOINT = "https://api.prototyped.ai"

ANIME_KEYWORDS = [
	"1girl",
	"2girls",
	"highres",
	"looking at viewer",
	"looking_at_viewer",
]

POSSIBLE_ANIME_KEYWORDS = [
	"breasts",
	"skirt",
	"blush",
	"smile",
	"solo",
	"simple background",
	"simple_background",
	"multiple girls",
	"multiple_girls"
]

class Image(Extension):
	
	@slash_command(name="image", description="Generate an image from AI")
	@slash_option(
		name="prompt",
		description="What do you want to see?",
		opt_type=OptionTypes.STRING,
		required=True
	)
	@slash_option(
		name="model",
		description="What model to use",
		opt_type=OptionTypes.STRING,
		required=False,
		choices=[
			SlashCommandChoice("Normal", 'sd-1.5'),
			SlashCommandChoice("Anime", 'anythingv3'),
		]
	)
	@slash_option(
		name="negative_prompt",
		description="What do you NOT want to see?",
		opt_type=OptionTypes.STRING,
		required=False
	)
	@slash_option(
		name="size",
		description="Image dimensions",
		opt_type=OptionTypes.STRING,
		required=False,
		choices=[
		  SlashCommandChoice("Square", '512x512'),
		  SlashCommandChoice("Wide", '768x512'),
		  SlashCommandChoice("Tall", '512x768'),
		]
	)
	@slash_option(
		name="cfg_scale",
		description="low = wandering, hight = focused",
		opt_type=OptionTypes.NUMBER,
		required=False,
		min_value=0,
		max_value=35
	)
	@slash_option(
		name="steps",
		description="low = noisy, hight = sharp",
		opt_type=OptionTypes.INTEGER,
		required=False,
		min_value=10,
		max_value=100
	)
	async def image(
		self,
		ctx: InteractionContext,
		prompt: str = None,
		model: str = "sd-1.5",
		negative_prompt: str = None,
		size: str = "512x512",
		cfg_scale: float = 7,
		steps: int = 50,
	):
		"""
		Generate an image from AI
		"""

		asyncio.create_task(ctx.defer())

		c = 0
		for i in prompt.split(" "):
			if i.lower() in POSSIBLE_ANIME_KEYWORDS:
				c += 1

		if model == "anythingv3" or any([x in prompt.lower() for x in ANIME_KEYWORDS]) or c > 1:
			payload = {
				"prompt": prompt,
				"negative_prompt": negative_prompt,
				"steps": steps,
				"width": int(size.split("x")[0]),
				"height": int(size.split("x")[1]),
				"scale": cfg_scale,
				"count": 1,
			}

			path = "anime"

		else:
			payload = {
				"prompt": prompt,
				"steps": steps,
				"width": int(size.split("x")[0]),
				"height": int(size.split("x")[1]),
				"scale": cfg_scale,
				"count": 1,
			}

			path = "image"

		self.bot.info(f"making image: {payload}")

		async with aiohttp.ClientSession() as session:
			async with session.post(f"{ENDPOINT}/{path}", json=payload) as resp:
				try:
					data = await resp.json()
				except Exception as e:
					print((await resp.text()))
					return await ctx.send("Something went wrong")

		await ctx.send(embeds=[
			Embed(
				description=prompt,
				image=EmbedAttachment(
					url=data.pop().get("image")
				),
				color=0x2f3136
			)
		])
	
def setup(bot):
	Image(bot)