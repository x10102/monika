from discord import Cog
from logging import info

class ModuleBase(Cog):

    def __init__(self):
        super().__init__()
    
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
    
    def print_config(self) -> list[str]:
        """
        Returns the module's configuration as a list of lines to be sent/printed.

        It's done this way so that the formatting can be consistent across all modules, for this reason, the lines shouldn't contain any formatting or newlines.
        """
        return ["Modul neohlásil žádnou konfiguraci"]
    
    def __str__(self):
        return f"{self.name()} Module, requires config: [{"".join(self.config_required)}]"
    
    def cog_unload(self) -> None:
        """
        A callback for when the module unloads. This runs before each restart of the bot currently.

        Overrides discord.Cog's cog_unload
        """
        info(f"Module {self.name()} has unloaded")