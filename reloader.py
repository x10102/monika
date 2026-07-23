"""
This file runs an infinite loop which restarts the bot process if it exits with a specific code.

Used for the 'reload' command
"""

# Builtins
import subprocess
import sys
import logging
from os import path, getcwd, unlink

def setup_logger(filename="bot.log"):

    logger = logging.getLogger("reloader")
    logger.setLevel(logging.INFO)

    log_format = '[RELOADER][%(asctime)s] %(message)s'
    date_format = '%H-%M-%S %d-%m-%Y'

    formatter = logging.Formatter(log_format, datefmt=date_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

if __name__ == '__main__':
    log = setup_logger()
    log.info("Reloader running, starting bot process...")
    main_path = path.join(getcwd(), 'main.py')
    restart_flag = path.join(getcwd(), 'request.restart')
    while True:
        bot_process = subprocess.Popen([sys.executable, main_path])
        retcode = bot_process.wait()
        if path.exists(restart_flag):
            unlink(restart_flag)
        else:
            log.info(f"Bot process exited with code {retcode}, exiting...")
            break
        log.info("Bot process exited with restart flag, restarting...")