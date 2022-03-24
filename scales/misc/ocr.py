import io
from dis_snek import slash_command, Message, InteractionCommand, Scale, InteractionContext, OptionTypes, slash_option, Attachment, SlashCommandChoice, File
import aiohttp, PIL, pytesseract

from dis_snek.api.events import MessageCreate

class OCR(Scale):
    
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

        async with aiohttp.ClientSession() as session:
            async with session.get(image.url) as resp:
                data = await resp.read()

        image = PIL.Image.open(io.BytesIO(data))
        text = pytesseract.image_to_string(image, lang=lang)

        await ctx.send(file=File(io.BytesIO(text.encode('utf-8')), "text.txt"))


    @listen()
    async def on_message_create(self, event: MessageCreate):
        message: Message = event.message

        if message.author.bot:
            return

        if "ocr" in message.content:
            pass

    
def setup(bot):
    OCR(bot)