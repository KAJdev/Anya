from dataclasses import dataclass, field
from random import choices
from naff import slash_command, Embed, listen, Extension, InteractionContext, OptionTypes, slash_option, Button, SlashCommandChoice, ComponentContext, EmbedFooter
import aiohttp, models, bs4

MANGAS = {
    'spy_family': 'https://spy-xfamily.com/',
    'chainsaw_man': 'https://chainsaw-man-manga.online/'
}

PAGE_SCHEMA = {
    'spy_family': lambda page: page.startswith('https://spy-xfamily.com/wp-content/uploads/'),
    'chainsaw_man': lambda page: 'userapi.com/impf/' in page
}

@dataclass
class MangaIndex:
    pages: list[str] = field(default_factory=list)
    chapters: dict = field(default_factory=dict)

class Manga(Extension):

    def __init__(self, bot):
        super().__init__()

        self.manga_index = {}
        self.indexing = []

    async def index_chapter(self, manga: str, chapter_number: float, chapter_url: str) -> list[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(chapter_url) as resp:
                data = await resp.text()

        chapter_soup = bs4.BeautifulSoup(data, 'html.parser')

        self.manga_index[manga].chapters[chapter_number] = len(self.manga_index[manga].pages)

        for page in chapter_soup.find_all('img'):
            if page.get('src') and PAGE_SCHEMA.get(manga)(page.get('src')):
                self.manga_index[manga].pages.append(page.get('src'))


    async def index_manga(self, manga: str = 'spy_family') -> None:
        self.manga_index[manga] = MangaIndex()

        if manga not in self.indexing:
            self.indexing.append(manga)

        async with aiohttp.ClientSession() as session:
            async with session.get(MANGAS.get(manga)) as resp:
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
                self.bot.error(f"Could not parse chapter number `{chapter.text}` for `{manga}`")
                continue

            chapters.append((chapter_number, chapter_url))

        chapters.sort(key=lambda x: x[0])

        for chapter in chapters:
            await self.index_chapter(manga, *chapter)

        self.bot.info(f"Indexed {len(self.manga_index[manga].pages)} manga pages and {len(self.manga_index[manga].chapters)} chapters for the {manga} manga")
        
        if manga in self.indexing:
            self.indexing.remove(manga)

    async def search_chapters(self, manga: str, query: str) -> list[SlashCommandChoice]:
        if manga not in self.manga_index:
            await self.index_manga(manga)

        chapters = []

        for chapter in self.manga_index[manga].chapters:
            if len(chapters) >= 25:
                break
            if query.lower() in str(chapter).lower():
                chapters.append(SlashCommandChoice(f"Chapter {str(chapter).split('.0')[0]}", str(chapter)).to_dict())

        return chapters

        
    async def render_manga_page(self, manga: str, page: int = 0) -> Embed:
        if manga not in self.manga_index:
            await self.index_manga(manga)

        embed = Embed(
            footer=EmbedFooter(text=f"Chapter {await self.get_pages_chapter(manga, page):.0f}/{str(list(self.manga_index[manga].chapters.keys())[-1]).split('.0')[0]} | Page {page + 1}/{len(self.manga_index[manga].pages)}"),
            color=0x2f3136
        )

        embed.set_image(url=self.manga_index[manga].pages[page])

        return embed

    async def get_pages_chapter(self, manga: str, page: int = 0) -> float:
        if manga not in self.manga_index:
            await self.index_manga(manga)

        prospect_chapter = 1

        for chapter,start_page_index in self.manga_index[manga].chapters.items():
            if page >= start_page_index and chapter > prospect_chapter:
                prospect_chapter = chapter

        return prospect_chapter

        
    @listen()
    async def on_ready(self):
        for manga in MANGAS:
            if manga not in self.manga_index and manga not in self.indexing:
                await self.index_manga(manga)
    
    @slash_command(name="manga", description="Fetch a page from a manga")
    @slash_option(
        name="manga",
        opt_type=OptionTypes.STRING,
        description="What manga to read. Defaults to SPYxFAMILY.",
        choices=[
            SlashCommandChoice('SPY x FAMILY', 'spy_family'),
            SlashCommandChoice('Chainsaw Man', 'chainsaw_man'),
        ],
        required=False,
    )
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
    async def manga_command(self, ctx: InteractionContext, manga: str = 'spy_family', chapter: int = None, page: int = None):
        """
        Fetch a page from the SPY X FAMILY manga
        """
        if manga in self.indexing:
            await ctx.send("Indexing manga, please wait", ephemeral=True)
            return

        if page is not None:
            page -= 1

        if not chapter and not page:
            user: models.User = await self.bot.db.fetch_user(ctx.author.id)
            page = user.manga_pages.get(manga, 0)

        if chapter is None and page is None:
            await ctx.send("Please specify a chapter or a page number", ephemeral=True)
            return

        if page is None and chapter is not None:
            page = self.manga_index[manga].chapters[float(chapter)]

        await ctx.send(embed=await self.render_manga_page(manga, page), components=[
            Button(
                label="Back",
                custom_id=f"MANGA:{manga}:{page - 1}:{ctx.author.id}",
                style=2,
                disabled=page == 0
            ),
            Button(
                label="Next",
                custom_id=f"MANGA:{manga}:{page + 1}:{ctx.author.id}",
                style=2,
                disabled=page == len(self.manga_index[manga].pages) - 1
            )
        ], ephemeral=True)

    @manga_command.autocomplete('chapter')
    async def manga_command_autocomplete(self, ctx: InteractionContext, manga: str = 'spy_family', chapter: str = ''):
        if manga in self.indexing:
            await ctx.send(choices=[{'name': 'Indexing manga, please wait', 'value': 'NONE'}])
        else:
            await ctx.send(choices=await self.search_chapters(manga, chapter))

    @listen()
    async def on_component(self, event) -> None:
        event: ComponentContext = event.context

        match event.custom_id.split(':'):
            case ["MANGA", page, user]:
                await event.send("This menu is outdated. Please create a new manga reader.", ephemeral=True)
            case ["MANGA", manga, page, user]:
                if manga in self.indexing:
                    await event.send("Indexing manga, please wait", ephemeral=True)
                    return

                if user != str(event.author.id):
                    await event.send("This is someone else's session!", ephemeral=True)
                    return

                page = int(page)

                await self.bot.db.update_user(event.author.id, {'$set': {'manga_pages.' + manga: page}})
                await event.edit_origin(embed=await self.render_manga_page(manga, page), components=[
                    Button(
                        label="Back",
                        custom_id=f"MANGA:{manga}:{page - 1}:{event.author.id}",
                        style=2,
                        disabled=page == 0
                    ),
                    Button(
                        label="Next",
                        custom_id=f"MANGA:{manga}:{page + 1}:{event.author.id}",
                        style=2,
                        disabled=page == len(self.manga_index[manga].pages) - 1
                    )
                ])
    
def setup(bot):
    Manga(bot)