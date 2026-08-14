# Builtins
from logging import info
from enum import IntEnum
from typing import cast, Any, ClassVar

# External
from discord import slash_command, ApplicationContext, InputTextStyle, Interaction, Embed, Member
from discord.ui import DesignerModal, InputText, Checkbox, Label, TextDisplay

# Internal
from core.singletons import config
from core.modulebase import ModuleBase
from core.botbase import MonikaBot

class ModalLanguage(IntEnum):
    CS = 0
    EN = 1

class GatekeeperFormModal(DesignerModal):

    LOC: ClassVar[dict[str, Any]] = {
        "cs": {
            "modal_title": "Ověření",
            "message": "-# Sdělte nám prosím svůj věk a důvod příchodu.",
            "lbl_age": "Věk",
            "lbl_reason": "Důvod příchodu",
            "lbl_int": "Mezinárodní člen",
            "desc_int": "Přicházím z mezinárodní větve SCP jiné než -CS",
            "resp_error": "Při odesílání zprávy došlo k chybě, zkuste to prosím později.",
            "resp_age_format": "Zadaný věk musí být číslo, zkuste to prosím znovu",
            "resp_underage": "Vaše ověření bylo zaznamenáno, počkejte prosím na zprávu od moderátora",
            "resp_err_tag_mod": "Došlo k chybě, označte prosím ve zprávě moderátora a počkejte",
            "resp_verified": "Byl vám udělen přístup na server! Pojďte dál"
        },
        "default": {
            "modal_title": "Verify",
            "message": "-# Please tell us your age and the reason for joining",
            "lbl_age": "Age",
            "lbl_reason": "Reason",
            "lbl_int": "International",
            "desc_int": "I come from an international SCP branch other than -CS",
            "resp_error": "There was an error processing your verification, please try again",
            "resp_age_format": "The age entered must be a number, try again",
            "resp_underage": "Your verification was recorded, please wait for a moderator to message you",
            "resp_err_tag_mod": "The bot has encountered an error, please tag a moderator and wait",
            "resp_verified": "You have been granted access to the server, welcome!"
        }
    }

    def __init__(self, bot: MonikaBot, *children, lang: ModalLanguage = ModalLanguage.CS, custom_id = None, timeout = None, store = True):
        l = GatekeeperFormModal.LOC['cs'] if lang == ModalLanguage.CS else GatekeeperFormModal.LOC['default']
        super().__init__(*children, title=l['modal_title'], custom_id=custom_id, timeout=timeout, store=store)

        self.bot = bot
        self.international = Checkbox(default=False)
        self.age = InputText(style=InputTextStyle.short, min_length=1, max_length=2)
        self.message = InputText(style=InputTextStyle.long)

        self.add_item(TextDisplay(l['message']))

        self.add_item(Label(l['lbl_age'],
                            item=self.age))

        self.add_item(Label(l['lbl_reason'],
                            item=self.message))

        self.add_item(Label(l['lbl_int'],
                            description=l['desc_int'],
                            item=self.international))

    async def callback(self, ctx: Interaction):
        l = GatekeeperFormModal.LOC['cs'] if ctx.locale == 'cs' else GatekeeperFormModal.LOC['default']
        if not ctx.user or not ctx.guild or self.message.value is None or self.age.value is None:
            await ctx.respond(l['resp_error'], ephemeral=True)
            return

        try:
            age = int(self.age.value)
        except ValueError:
            await ctx.respond(l['resp_age_format'], ephemeral=True)
            return

        if age < config.get_value("gatekeeper.age_limit"):
            await ctx.respond(l['resp_underage'], ephemeral=True)
            return

        role_id = config.get_value('roles.verified') if not self.international.value else config.get_value('roles.verified_int')
        role = ctx.guild.get_role(role_id)

        if not role:
            await ctx.respond(l['resp_err_tag_mod'])
            return

        user = cast(Member, ctx.user)
        await user.add_roles(role, reason="Uživatel ověřen")
        
        info(f"Gatekeeper confirm - Age {self.age.value}; Reason: {self.message.value}; International: {"Yes" if self.international.value else "No"}")
        await ctx.respond(l['resp_verified'], ephemeral=True)

class GatekeeperModule(ModuleBase):

    def __init__(self, bot: MonikaBot):
        super().__init__()
        self.bot = bot
        self.channel = int(config.get("channels.gatekeeper")) # type: ignore
    
    @staticmethod
    def env_override() -> str:
        return "disable_gatekeeper"
    
    @staticmethod
    def name() -> str:
        return "Gatekeeper"
    
    @staticmethod
    def config_required() -> list[str]:
        return ["channels.gatekeeper", "gatekeeper.age_limit", "roles.verified", "roles.verified_int"]

    @slash_command(name='confirm', description='Verify and get access to the server',
                   description_localizations={"cs": "Ověřte se a získejte přístup na server"})
    async def confession_send(self, ctx: ApplicationContext):
        if ctx.channel_id != self.channel:
            await ctx.respond("Tento příkaz zde nemůžete použít", ephemeral=True)
            return
        mod = GatekeeperFormModal(bot=self.bot, lang=ModalLanguage.CS if ctx.locale == 'cs' else ModalLanguage.EN)
        await ctx.send_modal(mod)