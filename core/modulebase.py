from discord import Cog
from logging import info
from core.models import ModelBase
from typing import TypeVar, ClassVar
from fastapi import APIRouter

ModelType = TypeVar('ModelType', bound=ModelBase)

class ModuleBase(Cog):

    _required_models: ClassVar[list[type[ModelBase]]] = []
    _router: ClassVar[APIRouter]

    def __init__(self):
        super().__init__()
        self._router = APIRouter()

    def __init_subclass__(cls):
        # Why are static variables on subclasses a reference to the ones on the parent?
        # That's so stupid
        # Just create the variable on the subclass explicitly
        cls._required_models = []

    @classmethod
    def model(cls, model: type[ModelType]) -> type[ModelType]:
        cls._required_models.append(model)
        return model
    
    @classmethod
    def required_models(cls) -> list[type[ModelBase]]:
        return cls._required_models
    
    @staticmethod
    def env_override() -> str:
        """
        Returns the name of the config variable that will prevent the module from loading if set to 'true'

        Despite the name, this does not have to be an environment variable; It may be present in the config "overrides" section as well.
        """
        return ""
    
    @staticmethod
    def name() -> str:
        """
        Returns the name of the module to be displayed in logs
        """
        return "Base Module"
    
    @staticmethod
    def config_required() -> list[str]:
        """
        Returns a list of config paths which need to exist for the module to be loaded
        """
        return []

    def router(self) -> APIRouter:
        """
        Returns the FastAPI router instance which provides API routes for this module
        """
        return self._router
    
    def format_config(self) -> list[str]:
        """
        Returns the module's configuration as a list of lines to be sent/printed.

        It's done this way so that the formatting can be consistent across all modules, for this reason, the lines shouldn't contain any formatting or newlines.
        """
        return ["Modul neohlásil žádnou konfiguraci"]

    def format_stats(self) -> list[str]:
        """
        Returns a module's internal statistics in the same manner as print_config 
        """
        return []
    
    def __str__(self):
        return f"{self.name()} Module, requires config: [{"".join(self.config_required)}]"
    
    def cog_unload(self) -> None:
        """
        A callback for when the module unloads. This runs before each restart of the bot currently.

        Overrides discord.Cog's cog_unload
        """
        info(f"Module {self.name()} has unloaded")