from cgitb import text
import io
from dis_snek import slash_command, Message, listen, Scale, InteractionContext, OptionTypes, slash_option, Attachment, SlashCommandChoice, File, message_command, context_menu, CommandTypes
import aiohttp, PIL, pytesseract, models

from dis_snek.api.events import MessageCreate

class OCR(Scale):

    async def do_ocr(self, image: Attachment, lang: str = 'eng') -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(image.url) as resp:
                data = await resp.read()

        image = PIL.Image.open(io.BytesIO(data))
        return pytesseract.image_to_string(image, lang=lang)
    
    @slash_command(name="ocr", description="Get text from an image")
    @slash_option(
        name="image",
        opt_type=OptionTypes.ATTACHMENT,
        description="The image to get text from",
        required=True,
    )
    @slash_option(
        name="lang",
        opt_type=OptionTypes.STRING,
        description="The language to use for OCR",
        required=False,
        choices=[
            SlashCommandChoice(lang, lang) for lang in pytesseract.get_languages(config='')[:24]
        ]
    )
    async def ocr(self, ctx: InteractionContext, image: Attachment, lang: str = 'eng'):
        """
        get text from an image
        """
        if not image.content_type.startswith("image/"):
            await ctx.send("This is not an image", ephemeral=True)
            return

        text = await self.do_ocr(image, lang)

        if len(text) == 0:
            await ctx.send("No text found", ephemeral=True)
            return

        if len(text) > 2000:
            await ctx.send(file=File(io.BytesIO(text.encode('utf-8')), "text.txt"))
        else:
            await ctx.send(f"```\n{text.replace('```', '')}\n```")


    async def message_ocr(self, message: Message):
        texts = []

        for attachment in message.attachments:
            if attachment.content_type.startswith("image/"):
                texts.append((attachment.filename, await self.do_ocr(attachment, 'eng')))

        return texts


    @context_menu(name="Get Text From Image", context_type=CommandTypes.MESSAGE)
    async def ocr_message(self, ctx: InteractionContext):
        texts = await self.message_ocr(list(ctx.resolved.messages.values())[0])

        if all_text_length := sum(len(text[1]) for text in texts) > 0:
            if all_text_length > 2000:
                await ctx.send(files=[File(io.BytesIO(t[1].encode('utf-8')), t[0]) for t in texts])
            else:
                await ctx.send("".join(f"```\n{text[1].replace('```', '')}\n```" for text in texts))

        else:
            await ctx.send("No text found", ephemeral=True)


    @listen()
    async def on_message_create(self, event: MessageCreate):
        message: Message = event.message

        if not message.author.bot and message.content and "ocr" in message.content and message.message_reference:

            guild: models.Guild = await self.bot.db.fetch_guild(message.guild.id)

            if not guild.module_enabled(models.ModuleToggles.OCR_REPLY):
                return

            referenced = await message.fetch_referenced_message()
            texts = await self.message_ocr(referenced)

            if texts:
                if sum(len(text[1]) for text in texts) > 2000:
                    await message.reply(files=[File(io.BytesIO(t[1].encode('utf-8')), t[0]) for t in texts])
                else:
                    await message.reply("".join(f"```\n{text[1].replace('```', '')}\n```" for text in texts))
    
def setup(bot):
    OCR(bot)