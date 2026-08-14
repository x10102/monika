# Builtins
import os
import sys
import pathlib
import asyncio

# External
from peewee import Model
import logging
from logging import info, warning, critical, error
import nest_asyncio2 # type: ignore[import-untyped]
import discord
from fastapi import FastAPI
import uvicorn

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
                                        ConfessionsModule]

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

async def main():
    # Load the config, set up our logger and spew out some log spam to make it feel cool
    config.load_from_json()
    setup_logger(config.get("log_file", "bot.log"))
    info("Logger initialized")
    info(f"Monika.aic version {PROGRAM_VERSION} starting")
    
    # This is needed for running the wikidot library alongside pycord as it uses its own asyncio loop
    info("Applying nested asyncio patch")
    nest_asyncio2.apply()
    # Init our database and create just the core tables    
    info("Initializing database")
    database.init(config.get("db_file", "applications.db"))
    database.connect()
    database.create_tables(get_core_models())

    # Check that we can enable the API, configure Uvicorn and create a server, but don't start it yet
    server: uvicorn.Server | None = None

    if not config.keys_missing(["api.host", "api.port"]):
        info("Initializing Uvicorn server")
        uvi_cfg = uvicorn.Config(bot.api, host=config.get_value('api.host'), port=config.get_value('api.port'))
        server = uvicorn.Server(uvi_cfg)
        bot.api_enabled = True
    else:
        info("API configuration missing, server will not be started")

    info("Loading modules")

    overrides = config.scope("overrides")

    # Loop over the list of all modules
    # Check that it's not forced-disabled, that we have the required config and that it initializes with no error
    for module in LOAD_MODULES:
        if overrides.get(module.env_override()):
            info(f"Not loading module: {module.name()} - due to env override")
            continue
        missing_required = config.keys_missing(module.config_required())
        if len(missing_required) != 0:
            error(f"Not loading module {module.name()} - missing required config: [{', '.join(missing_required)}]")
            continue
        try:
            # Create the models that the module requests
            required_models = module.required_models()
            database.create_tables(required_models)
            inst = module(bot)
            bot.load_module(inst)
            info(f"Loaded module: {module.name()} (Created {len(required_models)} models)")
            module_router = inst.router()
            if len(module_router.routes) > 0:
                bot.api.include_router(module_router)
                info(f"Registered API router for: {module.name()}")
        # TODO: This is redundant since we are checking for the required keys now
        except MissingConfigError:
            warning(f"Not loading module: {module.name()} - due to missing configuration")
        except Exception as e:
            warning(f"Error while loading module: {module.name()}: {e!r}")

    # And after all this we just find out that we have no token and exit, lmao
    token = config.get("bot_token")
    if not token:
        critical("Discord API token is missing, cannot continue")
        sys.exit(2)
    
    if server:
        # The context manager here is to clean up the bot state on exit
        # bot.start() doesn't do it automatically unlike bot.run()
        # asyncio.gather() just schedules both coroutines in the event loop
        async with bot:
            await asyncio.gather(
                bot.start(token),
                server.serve()
            )
    else:
        bot.run(token)

if __name__ == '__main__':
    # Kick off the asyncio event loop by running main()
    asyncio.run(main())