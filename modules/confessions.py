# Builtins
from logging import info, error

# External
import discord
from discord import slash_command, ApplicationContext, InputTextStyle, Interaction, Embed
from discord.ui import DesignerModal, InputText, Checkbox, Label, TextDisplay

# Internal
from core.singletons import config
from core.modulebase import ModuleBase
from core.botbase import MonikaBot

class ConfessionModal(DesignerModal):

    def __init__(self, bot: MonikaBot, *children, custom_id = None, timeout = None, store = True):
        super().__init__(*children, title="Schránka Důvěry", custom_id=custom_id, timeout=timeout, store=store)

        self.bot = bot
        self.anonymous = Checkbox(default=True)
        self.message = InputText(style=InputTextStyle.long)

        self.add_item(TextDisplay(
            "-# Odešlete zprávu moderátorům serveru. Pokud zprávu označíte jako anonymní, moderátorům nebude odesláno vaše jméno a nezobrazí se ani v záznamech bota."
        ))

        self.add_item(Label("Zpráva",
                            item=self.message))

        self.add_item(Label("Anonymní",
                            description="Chcete odeslat zprávu anonymně?",
                            item=self.anonymous))

    async def callback(self, ctx: Interaction):
        if not ctx.user or self.message.value is None or self.anonymous.value is None:
            await ctx.respond("Při odesílání zprávy došlo k chybě, zkuste to prosím později.", ephemeral=True)
            return
        
        emb = Embed(title="Nová zpráva ve schránce důvěry!")
        
        if self.anonymous.value:
            emb.title = "Nová anonymní zpráva!"
        else:
            icon_url = ctx.user.avatar.url if ctx.user.avatar else None
            emb.set_author(name=ctx.user.display_name, icon_url=icon_url)

        emb.add_field(name="Zpráva", value=self.message.value)

        channel_id = int(config.get_value("channels.confessions"))
        channel = await self.bot.fetch_channel(channel_id)

        if not isinstance(channel, discord.abc.Messageable):
            error("Confessions channel is not messageable, this is probably a configuration error")
            await ctx.respond("Při odesílání zprávy došlo k chybě, zkuste to prosím později.", ephemeral=True)
            return

        await channel.send(embed=emb)
        await ctx.respond("Vaše zpráva byla odeslána administraci.", ephemeral=True)

        if self.anonymous.value:
            info(f"Received anonymous confession. Text: {self.message.value}")
        else:
            info(f"Received confession from {ctx.user.name} (ID: {ctx.user.id}). Text: {self.message.value}")

class ConfessionsModule(ModuleBase):

    def __init__(self, bot: MonikaBot):
        super().__init__()
        self.bot = bot
        self.channel = int(config.get("channels.confessions")) # type: ignore
        self.anonymous = bool(config.get("confessions.anonymous"))
    
    @staticmethod
    def env_override() -> str:
        return "disable_confessions"
    
    @staticmethod
    def name() -> str:
        return "Confessions"
    
    @staticmethod
    def config_required() -> list[str]:
        return ["channels.confessions", "confessions.anonymous"]
    
    def format_config(self) -> list[str]:
        return [f"ID Schránky důvěry: {self.channel}"]

    @slash_command(name='confess', description='Odešle anonymní přiznání')
    async def confession_send(self, ctx: ApplicationContext):
        mod = ConfessionModal(bot=self.bot)
        await ctx.send_modal(mod)