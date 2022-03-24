from datetime import datetime, timezone
import random
from typing import Optional
from dis_snek import Embed, MISSING
import constants

emojis = {
    'red': "<:red:936440958617280512>",
    'green': "<:green:936441030922862632>",
    'purple': "<:purple:936441055778316438>",
    'grey': "<:grey:936440994554073109>",
    'yellow': "<:yellow:936445335780352121>"
}

embed_colors = {
    'red': 0xFF0000,
    'green': 0x00FF00,
    'purple': 0xFF00FF,
    'grey': 0x808080,
    'yellow': 0xFFFF00
}

emoji_name_filter = {
    'investigating': 'yellow',
    'identified': 'red',
    'monitoring': 'purple',
    'resolved': 'green',
    'update': 'grey',
}

def emoji(name: str, url: bool = False) -> str:
    if url:
        return f"https://cdn.discordapp.com/emojis/{emoji(name).strip('<>').split(':')[2]}.webp?size=96&quality=lossless"
    else:
        return emojis.get(emoji_name_filter.get(name.lower(), name).lower(), "")

def tryint(s: str) -> int | str:
    try:
        return int(s)
    except ValueError:
        return s

def color(name: str) -> int:
    return embed_colors.get(emoji_name_filter.get(name.lower(), name).lower(), 0x808080)

def time(time: datetime, type: str = 'd') -> str:
    return f"<t:{time.replace(tzinfo=timezone.utc).timestamp():.0f}:{type}>"

def concat(*args) -> str:
    return '\n'.join(args)

def embed(title: Optional[str] = MISSING, description: Optional[str] = MISSING, error: bool = False) -> Embed:
    return Embed(
        title=title,
        description=description,
        color=0x5765f2 if not error else 0xFF0000
    )

def progress(value: int, max: int) -> str:
    return f"{'▰' * value}{'▱' * (max - value)}"

def death_string(type: str) -> str:
    return random.choice(constants.DEATH_STRINGS.get(type, constants.DEATH_STRINGS['default']))