# Monika.AIC
A secondary discord bot for the Czech SCP branch (alongside [Thorn](https://github.com/scp-cs/Thorn))

- Forwards Wikidot site applications to the server and allows responding to them directly on Discord
- Detects spam bots / hacked accounts and puts them in timeout until a moderator has the chance to respond, logs incidents
- Runs a [Lost](https://en.wikipedia.org/wiki/Lost_(TV_series)) inspired minigame to keep you up at night
- Reposts popular messages to a Starboard channel
- Allows users to send anonymous confessions or reports to moderators
- More features are work-in-progress

# Usage
## Setup

1. Set up a discord developer account, create a bot and invite it to your server

2. Clone the repo
    ```bash
    git clone https://github.com/x10102/monika.git
    cd monika 
    ```

3. Create a `config.json` file with the following contents:
    ```json
    {
        "bot_token": "<YOUR BOT TOKEN>",
        "log_file": "log.txt",
        "db_file": "monika.db",
        "roles": {
            "admin": <ADMIN ROLE ID>
        },
        "channels": {
            "console" <CONSOLE CHANNEL ID>
        }
    }
    ```
    This is the basic setup required to start the bot and load the `BasicCommands` module, everything after that can be configured using the appropriate slash commands.

    The admin role should be your server's equivalent of an administrator or moderator. Keep in mind that most sensitive commands do not strictly require this role, just Discord's `Administrator` permission.

4. You can now choose to either run the bot in a Docker container or directly using your Python environment. If you're familiar with Docker, it is recommended to use it.

### Direct

5. Create virtual environment, activate it and install requirements
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

> [!IMPORTANT]
> If you require the `/reload` command to restart the bot directly from Discord, make sure to run `reloader.py` instead of `main.py`

6. Run the reloader script
    ```bash
    python3 reloader.py
    ```

### Docker

5. Build the Docker image
    ```bash
    docker build --tag monika .
    ```

> [!IMPORTANT]
> Be sure to mount the database file to a persistent volume or bind mount to prevent a data loss after updating or removing the container

6. Create a container
    ```bash
    # Touch the files on host to make them mount correctly
    touch /opt/monika/monika.db
    touch /opt/monika/log.txt
    docker run --detach --name monika_bot --volume type=bind,src=/opt/monika/monika.db,dst=/app/monika.db --volume type=bind,src=/opt/monika/log.txt,dst=/app/log.txt