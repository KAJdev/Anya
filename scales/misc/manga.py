from dis_snek import slash_command, Embed, listen, Scale, InteractionContext, OptionTypes, slash_option, Button, SlashCommandChoice, ComponentContext, EmbedFooter
import aiohttp, models, bs4

from db import Update

class Manga(Scale):

    def __init__(self, bot):
        super().__init__()

        self.manga_pages = []
        self.chapters = {}
        self.indexing = False

    async def index_chapter(self, chapter_number: float, chapter_url: str) -> list[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(chapter_url) as resp:
                data = await resp.text()

        chapter_soup = bs4.BeautifulSoup(data, 'html.parser')

        self.chapters[chapter_number] = len(self.manga_pages)

        for page in chapter_soup.find_all('img'):
            if page.get('src') and page.get('src').startswith('https://spy-xfamily.com/wp-content/uploads/'):
                self.manga_pages.append(page.get('src'))


    async def index_manga(self, url: str = 'https://spy-xfamily.com/') -> None:
        self.chapters.clear()
        self.manga_pages.clear()

        self.indexing = True

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.text()
        soup = bs4.BeautifulSoup(data, 'html.parser')

        chapters = []

        all_chapters = []
        
        for ul in soup.find_all('ul'):
            for li in ul.find_all('li'):
                if li.a:
                    all_chapters.append(li.a)

        all_chapters = list(set(all_chapters))

        for chapter in all_chapters:
            chapter_url = chapter.get('href')

            try:
                chapter_number = float(chapter.text.split()[-1])
            except ValueError:
                self.bot.error(f"Could not parse chapter number `{chapter.text}`")
                continue

            chapters.append((chapter_number, chapter_url))

        chapters.sort(key=lambda x: x[0])

        for chapter in chapters:
            await self.index_chapter(*chapter)

        self.bot.info(f"Indexed {len(self.manga_pages)} manga pages and {len(self.chapters)} chapters")
        self.indexing = False

    async def search_chapters(self, query: str) -> list[SlashCommandChoice]:
        if not self.chapters:
            await self.index_manga()

        chapters = []

        for chapter in self.chapters:
            if len(chapters) >= 25:
                break
            if query.lower() in str(chapter).lower():
                chapters.append(SlashCommandChoice(f"Mission {str(chapter).split('.0')[0]}", str(chapter)).to_dict())

        return chapters

        
    async def render_manga_page(self, page: int = 0) -> Embed:
        if not self.manga_pages:
            await self.index_manga()

        embed = Embed(
            footer=EmbedFooter(text=f"Chapter {await self.get_pages_chapter(page):.0f}/{str(list(self.chapters.keys())[-1]).split('.0')[0]} | Page {page + 1}/{len(self.manga_pages)}"),
            color=0x2f3136
        )

        embed.set_image(url=self.manga_pages[page])

        print(f"Rendering page {page}: {self.manga_pages[page]}")

        return embed

    async def get_pages_chapter(self, page: int = 0) -> float:
        if not self.chapters:
            await self.index_manga()

        prospect_chapter = 1

        for chapter,start_page_index in self.chapters.items():
            if page >= start_page_index and chapter > prospect_chapter:
                prospect_chapter = chapter

        return prospect_chapter

        
    @listen()
    async def on_ready(self):
        if not self.manga_pages:
            await self.index_manga()
    
    @slash_command(name="manga", description="Fetch a page from the SPY X FAMILY manga")
    @slash_option(
        name="chapter",
        opt_type=OptionTypes.STRING,
        description="Fetch the first page of this chapter",
        required=False,
        autocomplete=True,
    )
    @slash_option(
        name="page",
        opt_type=OptionTypes.INTEGER,
        description="Fetch a specific page number",
        required=False,
        min_value=1,
        max_value=1000,
    )
    async def manga_command(self, ctx: InteractionContext, chapter: int = None, page: int = None):
        """
        Fetch a page from the SPY X FAMILY manga
        """
        if self.indexing:
            await ctx.send("Indexing manga, please wait", ephemeral=True)
            return

        if page is not None:
            page -= 1

        if not chapter and not page:
            user: models.User = await self.bot.db.fetch_user(ctx.author.id)
            page = user.manga_page

        if chapter is None and page is None:
            await ctx.send("Please specify a chapter or a page number", ephemeral=True)
            return

        if page is None and chapter is not None:
            page = self.chapters[float(chapter)]

        await ctx.send(embed=await self.render_manga_page(page), components=[
            Button(
                label="Back",
                custom_id=f"MANGA:{page - 1}:{ctx.author.id}",
                style=2,
                disabled=page == 0
            ),
            Button(
                label="Next",
                custom_id=f"MANGA:{page + 1}:{ctx.author.id}",
                style=2,
                disabled=page == len(self.manga_pages) - 1
            )
        ])

    @manga_command.autocomplete('chapter')
    async def manga_command_autocomplete(self, ctx: InteractionContext, chapter: str):
        await ctx.send(choices=await self.search_chapters(chapter))

    @listen()
    async def on_component(self, event) -> None:
        event: ComponentContext = event.context

        match event.custom_id.split(':'):
            case ["MANGA", page, user]:
                if self.indexing:
                    await event.send("Indexing manga, please wait", ephemeral=True)
                    return

                if user != str(event.author.id):
                    await event.send("This is someone else's session!", ephemeral=True)
                    return

                page = int(page)

                await self.bot.db.update_user(event.author.id, Update().set(manga_page=page))
                await event.edit_origin(embed=await self.render_manga_page(page), components=[
                    Button(
                        label="Back",
                        custom_id=f"MANGA:{page - 1}:{event.author.id}",
                        style=2,
                        disabled=page == 0
                    ),
                    Button(
                        label="Next",
                        custom_id=f"MANGA:{page + 1}:{event.author.id}",
                        style=2,
                        disabled=page == len(self.manga_pages) - 1
                    )
                ])
    
def setup(bot):
    Manga(bot)