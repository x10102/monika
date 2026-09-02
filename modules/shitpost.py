# External
from discord import slash_command, ApplicationContext, default_permissions
from discord.ext.commands import CooldownMapping, BucketType

# Internal
from core.modulebase import ModuleBase
from core.botbase import MonikaBot

KABELE_STR = """
V Pondělí ráno když jsem přišel do práce, seděl na svém místě Tomáš Kabele, něco si psal do notýsku, když jsi mě všiml, usmál se a pokračoval ve psaní. ve 12:30 se zvedl a šel si pro kávu. Na místě ji vypil, sedl jsi zpátky ke svému stolu. Přesně v 16:00 se zvedl a odešel z místnosti. V 16:03 se vrátil s obědem. sedl si zpět na místo a začal jíst. V 16:05 dojedl a vložil krabičku do šuplíku šuplík zavřel. 17:00 se pak zvedl, a odešel.
V Úterý ráno opět seděl na svém místě a opět si něco psal do notýsku, na tu samou stranu. Když jsi mě všiml, usmál se a pokračoval ve psaní. Ve 12:30 se zvedl a odešel z místnosti. V 13:03 se vrátil s obědem. Sedl si zpět na místo a začal jíst. Přesně v 16:00 dojedl a vložil krabičku do šuplíku, šuplík se pokusil neúspěšně zavřít. V 16:05 se zvedl a šel si pro kávu. Na místě ji vypil a sedl jsi zpátky ke svému stolu. 17:00 se pak zvedl, a odešel.
Ve Středu ráno neseděl na svém místě. Přišel o hodinu později a sedl si ke stolu. Hodinu a půl koukal do zdi. Následně se zvedl a odešel. V 16:55 se vrátil a sednul si opět za stůl. Tentokrát koukal do vypnutého počítače.
Ve Čtvrtek ráno pil kafé za stolem v tom samém oblečeni jako den předešlí. Opět mě pozdravil. Následně koukal na vypnutou obrazovku. Ve 12:00 jí zapnul. Něco napsal a následně vypojil celý počítač z elektřiny a odešel.
Dnes ráno když jsem přišel do práce, seděl na svém místě Tomáš Kabele. Prosím okamžitě pošlete ochranku aby jej zatkla.
"""

class ShitpostModule(ModuleBase):

    @staticmethod
    def env_override():
        return "disable_shitposts"
    
    @staticmethod
    def name():
        return "Amogus"

    def __init__(self, bot: MonikaBot):
        super().__init__()
        self.bot = bot

    @default_permissions(administrator=True)
    @slash_command(name='kabele',
                   description="Arrest him",
                   description_localizations={'cs': "Zatkněte ho"},
                   cooldown=CooldownMapping.from_cooldown(1, 60, BucketType.user))
    async def kabele(self, ctx: ApplicationContext):
        await ctx.respond(KABELE_STR)
    