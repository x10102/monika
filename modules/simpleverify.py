import discord
from typing import cast
from logging import info, error
from core.modulebase import ModuleBase
from core.singletons import config

class SimpleVerifyModule(ModuleBase):
    
    @staticmethod
    def env_override():
        return "disable_simple_verify"
    
    @staticmethod
    def name():
        return "Simple Verification"

    @staticmethod
    def config_required():
        return ['channels.simpleverify', 'simpleverify.reaction', 'roles.verified']

    def format_config(self):
        return [
            f'ID ověřovacího kanálu: {self.channel}',
            f'Reakce: {self.reaction}',
            f'Ověřená role: {self.role}'
        ]
    
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot
        self.channel = config.get_value('channels.simpleverify')
        self.reaction = config.get_value('simpleverify.reaction')
        self.role = config.get_value('roles.verified')

    @discord.default_permissions(administrator=True)
    @discord.slash_command(name='verifycreate', description='Vytvoří zprávu pro verifikaci')
    async def create_verify_command(self, ctx: discord.ApplicationContext):
        entry_channel = cast(discord.abc.Messageable, self.bot.get_channel(self.channel))
        verify_embed = discord.Embed(color=discord.Color.blurple())
        verify_embed.title = "Verify"
        verify_embed.description = f"React {self.reaction} to this message to verify"
        verify_message = await entry_channel.send(embed=verify_embed)
        await verify_message.add_reaction(self.reaction)
        await ctx.respond(f"Zpráva pro ověření byla vytvořena v kanále <#{self.channel}>")

    @ModuleBase.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or not payload.member or payload.member.bot or not payload.emoji:
            # Data missing
            return
        if not payload.channel_id or payload.channel_id != self.channel:
            # Wrong channel
            return
        if not self.bot.user:
            error("Client not connected")
            return
        channel = cast(discord.abc.Messageable, await self.bot.fetch_channel(payload.channel_id))
        message = await channel.fetch_message(payload.message_id)
        if message.author.id != self.bot.user.id:
            return
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            error(f"Guild {payload.guild_id} not found")
            return
        emoji = discord.PartialEmoji.from_str(self.reaction)
        if emoji == payload.emoji:
            role = await guild.fetch_role(self.role)
            member = await guild.fetch_member(payload.user_id)
            await member.add_roles(role)
            info(f"[VERIFY] Added role {role.name} to user {member.name} ({member.id})")
        