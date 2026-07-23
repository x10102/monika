from enum import IntEnum

class ExitCode(IntEnum):
    OK = 0,
    KILLED = 67,
    RESTART_REQUEST = 111

PROGRAM_VERSION = "2.1.0"

PM_VERB = ["slajdnout do DMs",
            "střelit PM",
            "hodit message",
            "napsat na Wikidotu"]
TIMEOUTED_VERB = ["Mutenut", 
                  "Timeoutnut", 
                  "Zablokován", 
                  "Odvezen do Brazílie", 
                  "Deportován na Slovensko",
                  "Zavřen do klece",
                  "Zavřen do klece s výbušnými koťátky",
                  "Zavřen do klece se sedmnácti tygry",
                  "Svázán ve sklepě", 
                  "Odsouzen k práci v KFC",
                  "Odsouzen k práci v Mekáči",
                  "Přiřazen ke Keter Duty",
                  "Poslán krmit pstruhadla",
                  "Vymazán z reality",
                  "Zavřen do trouby na 180°"]

MESSAGE_REJECT_DEFAULT = "Vaše žádost byla zamítnuta, pro více informací nás kontaktujte na našem discordu."
MESSAGE_ACCEPT_DEFAULT = "Vaše žádost byla přijata. Vítejte v Nadaci!"

THE_NUMBERS = "4 8 15 16 23 42"

KOTESENI = "<:koteseni:1354216680800391268>"

CONFIG_LOCKED_KEYS = [
    "bot_token",
    "roles.admin",
    "db_file"
]

RESTART_FLAG_NAME = "request.restart"