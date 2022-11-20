from ast import Bytes
from io import BytesIO
import random
from naff import File, Modal, ModalContext, ShortText, slash_command, Extension, InteractionContext
from pyparsing import col
import models

from PIL import Image, ImageDraw, ImageFont

SIZE = 16
PLACE_SIZE = 64
FACTOR = 10

def draw_ellipse(draw: ImageDraw, x, y, width, height, color, border_color=None, border_width=1):
    """
    calculate bounding box based on SIZE x and y of drawing and draw an ellipse in it
    """
    bound_box = (x - width, y - height, x + width, y + height)
    draw.ellipse(bound_box, fill=color, outline=border_color, width=border_width)

def draw_chord(draw: ImageDraw, x, y, width, height, color, start = 0, end = 180):
    """
    calculate bounding box based on SIZE x and y of drawing and draw a chord in it
    """
    bound_box = (x - width, y - height, x + width, y + height)
    draw.chord(bound_box, start, end, fill=color)

def draw_arc(draw: ImageDraw, x, y, width, height, color, start = 0, end = 180):
    """
    calculate bounding box based on SIZE x and y of drawing and draw a chord in it
    """
    bound_box = (x - width, y - height, x + width, y + height)
    draw.arc(bound_box, start, end, fill=color)

def draw_rectangle(draw: ImageDraw, x, y, width, height, color, border_color=None, border_width=1):
    """
    calculate bounding box based on SIZE x and y of drawing and draw a rectangle in it
    """
    bound_box = (x - width, y - height, x + width, y + height)
    draw.rectangle(bound_box, fill=color, outline=border_color, width=border_width)

def draw_rounded_rectangle(draw: ImageDraw, x, y, width, height, color, border_color=None, border_width=1, radius=3):
    """
    calculate bounding box based on SIZE x and y of drawing and draw a rectangle in it
    """
    bound_box = (x - width, y - height, x + width, y + height)
    draw.rounded_rectangle(bound_box, radius=radius, fill=color, outline=border_color, width=border_width)

def draw_progress_bar(draw: ImageDraw, x, y, width, height, color, fill_color, progress, border_color=None, border_width=1):
    """
    calculate bounding box based on SIZE x and y of drawing and draw a rectangle in it
    """
    draw_rounded_rectangle(draw, x, y, width, height, (0,0,0,0), border_color, border_width, 1)
    draw_rectangle(draw, x, y, width-1, height-1, fill_color, border_width, 1)
    draw_rectangle(draw, x, y, width * progress - 1, height - 1, color, border_width, 1)

class Tamagotchi(Extension):


    async def create_tamagotchi(self, ctx: InteractionContext) -> tuple[InteractionContext, models.Tamagotchi]:
        name_modal = Modal(
            title="What's your tamagotchi's name?",
            components=[
                ShortText(label="Name", placeholder="Tamagotchi's name", required=True, max_length=100, custom_id="name"),
            ]
        )

        await ctx.send_modal(name_modal)
        ctx: ModalContext = await self.bot.wait_for_modal(name_modal)

        t = await self.bot.db.create_tamagotchi(ctx.author.id, ctx.responses['name'])

        return ctx, t

    def generate_photo(self, t: models.Tamagotchi, frame: int = 0) -> BytesIO:
        photo = Image.new('RGBA', (SIZE, SIZE), color=(0,0,0,0))
        draw = ImageDraw.Draw(photo)

        random.seed(t.genes.seed)
        
        # draw the body
        (draw_ellipse if t.genes.body_shape else draw_rounded_rectangle)(draw, SIZE/2, SIZE/2 + SIZE/8, t.genes.body_width.bounded(3, 5), t.genes.body_height.bounded(3, 5),
            (
                t.genes.color_r.bounded(0, 255),
                t.genes.color_g.bounded(0, 255),
                t.genes.color_b.bounded(0, 255),
            ),
            (
                t.genes.body_edge_color_r.bounded(0, 255),
                t.genes.body_edge_color_g.bounded(0, 255),
                t.genes.body_edge_color_b.bounded(0, 255),
            ),
            t.genes.body_edge_width.bounded(0, 2)
        )

        # draw the arms
        draw.line(
            (
                SIZE/2 + 1,
                SIZE/2,

                SIZE/2 + t.genes.arm_length.bounded(0, SIZE/2, 3) + 1,
                t.genes.arm_length.bounded(SIZE/3, SIZE/2, 3),
            ),
            (
                t.genes.arm_color_r.bounded(0, 255),
                t.genes.arm_color_g.bounded(0, 255),
                t.genes.arm_color_b.bounded(0, 255),
            ),
            t.genes.arm_width.bounded(1, 3)
        )

        draw.line(
            (
                SIZE/2 + 1,
                SIZE/2,

                SIZE/2 - t.genes.arm_length.bounded(0, SIZE/2, 3) + 1,
                t.genes.arm_length.bounded(SIZE/3, SIZE/2, 3),
            ),
            (
                t.genes.arm_color_r.bounded(0, 255),
                t.genes.arm_color_g.bounded(0, 255),
                t.genes.arm_color_b.bounded(0, 255),
            ),
            t.genes.arm_width.bounded(1, 3)
        )

        # draw the head
        if t.genes.head_shape:
            draw_chord(draw, SIZE/2, SIZE/3, t.genes.head_width.bounded(3, 5), t.genes.head_height.bounded(4, 5), 
                (
                    t.genes.color_r.bounded(0, 255),
                    t.genes.color_g.bounded(0, 255),
                    t.genes.color_b.bounded(0, 255),
                ),
                135,
                45
            )

        else:
            draw_rounded_rectangle(draw, SIZE/2, SIZE/3, t.genes.head_width.bounded(3, 5), t.genes.head_height.bounded(4, 5), 
                (
                    t.genes.color_r.bounded(0, 255),
                    t.genes.color_g.bounded(0, 255),
                    t.genes.color_b.bounded(0, 255),
                ),
            )
        
        # draw eyes
        draw_rectangle(draw, SIZE/2 - SIZE/8, SIZE/3, 0, t.genes.eye_size.bounded(0, 1),
            (
                t.genes.eye_color_r.bounded(0, 100),
                t.genes.eye_color_g.bounded(0, 100),
                t.genes.eye_color_b.bounded(0, 100),
            )
        )

        draw_rectangle(draw, SIZE/2 + SIZE/8, SIZE/3, 0, t.genes.eye_size.bounded(0, 1),
            (
                t.genes.eye_color_r.bounded(0, 100),
                t.genes.eye_color_g.bounded(0, 100),
                t.genes.eye_color_b.bounded(0, 100),
            )
        )
        

        # draw the mouth
        (draw_chord if t.genes.mouth_shape else draw_arc)(draw, SIZE/2, SIZE/2, SIZE/8, t.genes.mouth_size.bounded(1, 3),
            (
                t.genes.mouth_color_r.bounded(0, 255),
                t.genes.mouth_color_g.bounded(0, 255),
                t.genes.mouth_color_b.bounded(0, 255),
            )
        )

        # loop through image pixels
        for x in range(SIZE):
            for y in range(SIZE):
                # if the pixel is not transparent
                if (p := photo.getpixel((x, y)))[3] != 0:
                    # apply a tiny bit of noise to the pixel
                    noise = random.randint(-5, 5) - round(y)
                    photo.putpixel((x, y), (
                        p[0] + noise,
                        p[1] + noise,
                        p[2] + noise,
                        p[3]
                    ))

        return photo

    def composite_to_background(self, photo: Image) -> BytesIO:
        background = Image.new('RGBA', (PLACE_SIZE, PLACE_SIZE//2), color=(0,0,0,0))
        draw = ImageDraw.Draw(background)

        # background
        draw.rounded_rectangle((2, 2, PLACE_SIZE-2, PLACE_SIZE//2-2), 6, fill=(100,100,100), outline=(0,0,0,50), width=1)
        draw.rounded_rectangle((5, 5, PLACE_SIZE//2-5, PLACE_SIZE//2-5), 3, fill=(80,80,80))

        background.paste(photo, (7, 9), photo)

        # draw progress bars
        #draw_progress_bar(draw, PLACE_SIZE//2 + 5, PLACE_SIZE//3, 10, 3, (255,255,255), (0,0,0), 0.7)
        draw_progress_bar(draw, PLACE_SIZE//2 + 13, (PLACE_SIZE//3), 15, 1, (255,255,255,255), (0,0,0,255), 0.5, (80,80,80,255), 1)

        b = BytesIO()
        background.resize((PLACE_SIZE * FACTOR, PLACE_SIZE//2 * FACTOR), Image.NEAREST).save(b, format='png')
        b.seek(0)
        return b
    
    @slash_command(name="tamagotchi", description="Play with a Tamagotchi")
    async def tamagotchi_command(self, ctx: InteractionContext):
        """
        Play with a Tamagotchi
        """
        t = await self.bot.db.fetch_tamagotchi(ctx.author.id)

        if t is None:
            ctx, t = await self.create_tamagotchi(ctx)

        await ctx.defer()

        photo = self.composite_to_background(self.generate_photo(t))

        await ctx.send(files=[File(photo, "tamagotchi.png")])
        
    
def setup(bot):
    Tamagotchi(bot)