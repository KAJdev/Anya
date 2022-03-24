from dacite import from_dict
from dis_snek import slash_command, Button, ButtonStyles, listen, Embed, Scale, Modal, ShortText, ParagraphText, InteractionContext, OptionTypes, slash_attachment_option, ModalContext, auto_defer, slash_option
import os
import models

class Core(Scale):
    pass
    
def setup(bot):
    Core(bot)