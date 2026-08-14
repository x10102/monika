# Builtins
import os
import sys
import pathlib

# External
from peewee import Model
import logging
from logging import info, warning, critical, error
import nest_asyncio2 # type: ignore[import-untyped]
import discord

# Internal
from core.botbase import MonikaBot
from core.exceptions import MissingConfigError
from core.modulebase import ModuleBase
from core.singletons import config
from core.models import database, get_core_models
from constants import PROGRAM_VERSION, RESTART_FLAG_NAME

# Modules
from modules.basic import BasicModule
from modules.applications import WikidotApplicationsModule
from modules.lost import LostModule
from modules.antispam import AntispamModule
from modules.starboard import StarboardModule
from modules.confessions import ConfessionsModule

bot = MonikaBot(intents=discord.Intents.all())

LOAD_MODULES: list[type[ModuleBase]] = [BasicModule,
                                        LostModule,
                                        AntispamModule,
                                        WikidotApplicationsModule,
                                        StarboardModule,
                                        ConfessionsModule,
                                        GatekeeperModule]

# Set up the logging format and target
# Logs to stdout and "bot.log" by default
def setup_logger(filename="bot.log"):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_format = '[%(levelname).1s][%(asctime)s] %(message)s'
    date_format = '%H-%M-%S %d-%m-%Y'

    formatter = logging.Formatter(log_format, datefmt=date_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
        
@bot.slash_command(name='reload', description='Restartuje bota a znovu načte konfiguraci')
async def reload(ctx: discord.ApplicationContext):
    critical(f"Received restart command from {ctx.user.name} ({ctx.user.id})")
    await ctx.respond("Restartuji...")
    loaded = list(bot.cogs.keys())
    for cog in loaded:
        bot.remove_cog(cog)
    # Create a restart flag so that the reloader knows not to exit yet
    pathlib.Path(os.getcwd(), RESTART_FLAG_NAME).touch()
    await bot.close()
    # Still leaving this in just in case bot.close doesn't crash in the future
    sys.exit(0)

def main():
    config.load_from_json()
    setup_logger(config.get("log_file", "bot.log"))
    info("Logger initialized")
    info(f"Monika.aic version {PROGRAM_VERSION} starting")
    info("Applying nested asyncio patch")
    # This is needed for running the wikidot library alongside pycord as it uses its own asyncio loop
    nest_asyncio2.apply()
    
    info("Initializing database")
    database.init(config.get("db_file", "applications.db"))
    database.connect()
    database.create_tables(get_core_models())

    info("Loading modules")

    overrides = config.scope("overrides")

    for module in LOAD_MODULES:
        if overrides.get(module.env_override()):
            info(f"Not loading module: {module.name()} - due to env override")
            continue
        missing_required = config.keys_missing(module.config_required())
        if len(missing_required) != 0:
            error(f"Not loading module {module.name()} - missing required config: [{', '.join(missing_required)}]")
            continue
        try:
            required_models = module.required_models()
            database.create_tables(required_models)
            bot.load_module(module(bot))
            info(f"Loaded module: {module.name()} (Created {len(required_models)} models)")
        # TODO: This is redundant since we are checking for the required keys now
        except MissingConfigError:
            warning(f"Not loading module: {module.name()} - due to missing configuration")
        except Exception as e:
            warning(f"Error while loading module: {module.name()}: {e!r}")

    token = config.get("bot_token")
    if not token:
        critical("Discord API token is missing, cannot continue")
        sys.exit(2)

    bot.run(token)

main()