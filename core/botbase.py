"""
Implements the base class for the bot with some additional methods and attributes. Derived from Pycord's Bot class
"""

# Builtins
from logging import info

# Internal
from .modulebase import ModuleBase

# External
from discord import Bot

class MonikaBot(Bot):

    def __init__(self, description=None, *args, **options):
        super().__init__(description, *args, **options)
        self.__loaded_modules = []

    async def on_ready(self):
        info(f"{self.user} is ready to go!")

    @property
    def loaded_modules(self) -> list[ModuleBase]:
        return self.__loaded_modules

    def load_module(self, module: ModuleBase, *, override = False) -> None:
        super().add_cog(module, override=override)
        self.__loaded_modules.append(module)