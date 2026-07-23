from core.modulebase import ModuleBase
import discord
from discord.ext.commands import slash_command
from logging import critical, info, warning
from core.models import WDApplication, AntispamTriggerEvent, LostCycle, StarboardPinnedMessage
from constants import PROGRAM_VERSION, CONFIG_LOCKED_KEYS
from core.singletons import config
from utils.textutils import string_to_json_type, JSONNull
from core.botbase import MonikaBot


class BasicModule(ModuleBase):

    @staticmethod
    def env_override():
        return "disable_basic"
    
    @staticmethod
    def name():
        return "Basic Commands"
    
    @staticmethod
    def config_required():
        return ['channels.console', 'roles.admin']

    def print_config(self):
        return [
            f'ID Console kanálu: {self.console_id}',
            f'ID Admin role: {self.admin_role_id}'
        ]

    def __init__(self, bot: MonikaBot):
        super().__init__()
        self.console_id = int(config.get_value('channels.console'))
        self.admin_role_id = int(config.get_value('roles.admin'))
        self.bot = bot

    @discord.default_permissions(administrator=True)
    @slash_command(name="kill", description="Ukončí bota v případě že se zblázní")
    async def kill_process(self, ctx: discord.ApplicationContext):
        critical(f"Received emergency shutdown command from {ctx.user.name} ({ctx.user.id}), exiting immediately")
        await ctx.respond("Bylo mi ctí s vámi sloužit, kapitáne. *střelí se do hlavy*")
        await self.bot.close()
        # We never actually get to the exit() because bot.close() raises an exception somewhere in aiohttp
        # Leaving it in for the aura (loss)
        exit(67)

    @discord.default_permissions(administrator=True)
    @slash_command(name="stats", description="Zobrazí statistiky")
    async def view_stats(self, ctx: discord.ApplicationContext):
        info(f"Sending stats as response to {ctx.user.name} ({ctx.user.id})")
        accepted_count = WDApplication.select().where(WDApplication.accepted).count()
        rejected_count = WDApplication.select().where(~WDApplication.accepted).count()
        external_count = WDApplication.select().where(WDApplication.resolved_externally).count()
        antispam_trigger_count = AntispamTriggerEvent.select().count()
        lost_cycle_count = LostCycle.select().count()
        starboard_pinned_count = StarboardPinnedMessage.select().where(StarboardPinnedMessage.pinned_at.is_null(False)).count()
        starboard_record_count = StarboardPinnedMessage.select().count()
        stats_text = (f"```Monika.aic verze {PROGRAM_VERSION}\n"
                      f"Přijatých žádostí: {accepted_count}\n"
                      f"Zamítnutých žádostí: {rejected_count}\n"
                      f"Nezapočítaných žádostí: {external_count}\n"
                      f"Události detekce spamu: {antispam_trigger_count}\n"
                      f"Cykly ztraceného tlačítka: {lost_cycle_count}\n"
                      f"Připnutých zpráv: {starboard_pinned_count}\n"
                      f"Záznamů ve starboard tabulce: {starboard_record_count}```")
        await ctx.respond(stats_text)

    @discord.default_permissions(administrator=True)
    @slash_command(name="config", description="Zobrazí konfiguraci")
    async def view_config(self, ctx: discord.ApplicationContext):
        # unnghhh I hate global state
        loaded_str = ""
        for mod in self.bot.loaded_modules:
            loaded_str += f'\t{mod.name()}\n'
            for line in mod.print_config():
                loaded_str += f'\t\t{line}\n'
            loaded_str += '\n'
        config_text = f"```Konfigurace Monika.aic verze {PROGRAM_VERSION}\n\n"
        config_text += f"Načtené moduly:\n{loaded_str}```"
        # TODO: Finish this
        await ctx.respond(config_text)

    @discord.default_permissions(administrator=True)
    @slash_command(name="setconfig", description="Změní hodnotu v konfiguraci")
    @discord.option("Název", type=discord.SlashCommandOptionType.string, required=True, description="Klíč v konfiguračním souboru")
    @discord.option("Hodnota", type=discord.SlashCommandOptionType.string, required=True, description="Nová hodnota")
    async def config_set_key(self, ctx: discord.ApplicationContext, key: str, value: str):
        if key in CONFIG_LOCKED_KEYS:
            warning(f"Rejected request to change protected config key \"{key}\" to \"{value}\" by {ctx.user.name} (ID: {ctx.user.id})")
            await ctx.respond("Toto nastavení nelze z bezpečnostních důvodů změnit", ephemeral=True)
            return
        converted_val = string_to_json_type(value)
        if converted_val is None:
            await ctx.respond("Neplatný formát, všechny hodnoty seznamu musí být stejného typu", ephemeral=True)
            info(f"Config key \"{key}\" was not changed to \"{value}\", couldn't parse list")
            return
        if isinstance(converted_val, JSONNull):
            config.set(key, None)
        else:
            config.set(key, converted_val)
        try:
            config.write_to_json()
            info(f"Config key \"{key}\" set to \"{value}\" by {ctx.user.name} (ID: {ctx.user.id})")
            await ctx.respond(f"Konfigurace `{key}` byla nastavena na hodnotu `{converted_val}`")
        except (OSError, IOError):
            await ctx.respond("Konfiguraci nelze zapsat: Chyba I/O", ephemeral=True)

    @discord.default_permissions(administrator=True)
    @slash_command(name="ping", description="Mňau")
    async def ping(self, ctx: discord.ApplicationContext):
        info(f"Sending ping as response to {ctx.user.name} ({ctx.user.id})")
        await ctx.respond("🐈")

    @discord.default_permissions(administrator=True)
    @slash_command(name="synccommands", description="Synchronizuje příkazy s Discordem po aktualizaci, nepoužívat pokud nevíte co to znamená")
    async def cmd_sync(self, ctx: discord.ApplicationContext):
        info(f"Synchronizing commands at request of {ctx.user.name} ({ctx.user.id})")
        await self.bot.sync_commands()
        await ctx.respond("Synchronizace dokončena, pro použití nových příkazů restartujte Discord (CTRL+R)", ephemeral=True)

    @ModuleBase.listener()
    async def on_ready(self):
        if(config.get("overrides.sync_commands_on_startup", "false") == "true"):
            info("Syncing commands")
            await self.bot.sync_commands()
            channel = self.bot.get_channel(self.console_id)
            await channel.send("Nové příkazy synchronizovány s Discord bot API, Čýmsi nezapomeň upravit .env")