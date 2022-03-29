from datetime import datetime
from enum import auto
from dis_snek import slash_command, Embed, listen, Scale, InteractionContext, File, slash_option, Button, SlashCommandChoice, Modal, ModalContext, ShortText, ParagraphText
import uuid
import io
from db import Update

from dis_snek.api.events import ModalResponse

class Bin(Scale):
    
    @slash_command(name="paste", description="Discord pastes")
    @slash_option(
        name="view",
        opt_type=3,
        description="View a paste",
        autocomplete=True,
        required=False,
    )
    @slash_option(
        name="edit",
        opt_type=3,
        description="Edit a paste you own",
        autocomplete=True,
        required=False,
    )
    @slash_option(
        name="delete",
        opt_type=3,
        description="Delete a paste you own",
        autocomplete=True,
        required=False,
    )
    async def paste_command(self, ctx: InteractionContext, view: str = None, edit: str = None, delete: str = None):
        """
        Paste or view a file
        """

        if view is None and edit is None and delete is None:
            id = uuid.uuid4()

            modal: Modal = Modal(
                title="Create a new paste",
                components=[
                    ShortText(label="Filename", custom_id="filename", placeholder="Filename including extension", value=f"{id}.txt", required=True),
                    ShortText(label="Description", custom_id="description", placeholder="A short description of the paste", required=False),
                    ParagraphText(label="Content", custom_id="content", placeholder="Paste content", required=True),
                    ShortText(label="Public", custom_id="public", placeholder="yes/no", required=False),
                ],
                custom_id=f"PASTE:{id}",
            )

            await ctx.send_modal(modal)

        elif view is not None and edit is None and delete is None:
            paste = await self.bot.db._fetch("pastes", {"id": view, "$or": [{"author_id": ctx.author.id}, {"public": True}]})

            if paste is None:
                await ctx.send("Paste not found", ephemeral=True)
                return

            await ctx.send(file=File(
                io.BytesIO(paste["content"].encode()),
                file_name=paste["filename"],
            ))

        elif view is None and edit is not None and delete is None:
            paste = await self.bot.db._fetch("pastes", {"id": edit, "author_id": ctx.author.id})

            if paste is None:
                await ctx.send("Paste not found", ephemeral=True)
                return

            modal: Modal = Modal(
                title="Edit paste",
                components=[
                    ShortText(label="Filename", custom_id="filename", placeholder="Filename including extension", value=paste["filename"], required=True),
                    ShortText(label="Description", custom_id="description", placeholder="A short description of the paste", value=paste["description"], required=False),
                    ParagraphText(label="Content", custom_id="content", placeholder="Paste content", value=paste["content"], required=True),
                    ShortText(label="Public", custom_id="public", placeholder="yes/no", value=paste["public"], required=False),
                ],
                custom_id=f"PASTE:{edit}",
            )

            await ctx.send_modal(modal)

        elif view is None and edit is None and delete is not None:
            paste = await self.bot.db._fetch("pastes", {"id": delete, "author_id": ctx.author.id})

            if paste is None:
                await ctx.send("Paste not found", ephemeral=True)
                return

            await self.bot.db._delete("pastes", {"id": delete})
            await ctx.send("Paste deleted")

    @paste_command.autocomplete('view')
    async def paste_command_autocomplete_view(self, ctx: InteractionContext, view: str):
        pastes = await self.bot.db._fetch("pastes", {"$or": [{"author_id": ctx.author.id}, {"public": True}], "filename": {"$regex": f"^{view}", "$options": "i"}}, limit=25)
        await ctx.send(choices=[
            {
                "name": paste["filename"],
                "value": paste["id"],
            } for paste in pastes
        ])

    @paste_command.autocomplete('edit')
    async def paste_command_autocomplete_view(self, ctx: InteractionContext, edit: str):
        pastes = await self.bot.db._fetch("pastes", {"author_id": ctx.author.id, "filename": {"$regex": f"^{edit}", "$options": "i"}}, limit=25)
        await ctx.send(choices=[
            {
                "name": paste["filename"],
                "value": paste["id"],
            } for paste in pastes
        ])

    @paste_command.autocomplete('delete')
    async def paste_command_autocomplete_view(self, ctx: InteractionContext, delete: str):
        pastes = await self.bot.db._fetch("pastes", {"author_id": ctx.author.id, "filename": {"$regex": f"^{delete}", "$options": "i"}}, limit=25)
        await ctx.send(choices=[
            {
                "name": paste["filename"],
                "value": paste["id"],
            } for paste in pastes
        ])

    @listen()
    async def on_modal_response(self, event: ModalResponse) -> None:
        modal: ModalContext = event.context

        if not modal.custom_id.startswith("PASTE:"):
            return

        id = modal.custom_id.split(":")[1]

        paste_object = {
            "id": id,
            "filename": modal.responses.get("filename"),
            "description": modal.responses.get("description"),
            "content": modal.responses.get("content"),
            "public": modal.responses.get("public").lower() in ("yes", "y", "true", "1"),
            "author_id": modal.author.id,
            "author_name": modal.author.username,
            "created_at": datetime.utcnow(),
        }

        await self.bot.db._update("pastes", {"id": id}, {"$set": paste_object}, upsert=True)

        await modal.send("Paste created", file=File(
            io.BytesIO(paste_object.get("content").encode()),
            file_name=paste_object.get("filename")
        ), ephemeral=True)
    
def setup(bot):
    Bin(bot)