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
            "console": <CONSOLE CHANNEL ID>
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
    docker run --detach --name monika_bot\
        --volume type=bind,src=/opt/monika/monika.db,dst=/app/monika.db\
        --volume type=bind,src=/opt/monika/log.txt,dst=/app/log.txt

## Using the bot

- Make sure the bot is alive with `/ping`, it should respond with a 🐈
- Use `/reload` to restart the bot after making changes to the configuration
- If a new module is enabled, use `/synccommands` to make the bot synchronize the new commands with Discord. Users may have to restart their client to see them at first.
    - Modules such as `Starboard` or `Confessions` are loaded dynamically based on the configuration values (not) present
- If the bot ever goes insane, use `/kill` to immediately exit/crash the script
- Use `/config` and `/setconfig` to view and change values in the config file
- Use `/stats` to see statistics reported by each module, not all of them may provide a lot of useful info
- Use `/say` to make the bot say freaky things in public channels

## Configuring Starboard
- A "Starboard" is a channel where messages which gather enough reactions from members are reposted
- Create a starboard channel and set `channels.starboard` to its ID
- Insert a list of the reactions you want to use for this into `starboard.emoji`
    - You can create a list with the `/setconfig` command like this: `VALUE1,VALUE2,VALUE3`
    - Built-in Discord emoji can be pasted in as-is, custom server emojis are formatted as `<:NAME:ID>`
- Finally, set `starboard.threshold` to the reaction count threshold which will cause a message to be pinned on the starboard

## Configuring AntiSpam
- This is enabled by default, set `overrides.disable_antispam` to `true` to disable it
- By default, `4` identical messages within `5` minutes will trigger a spam event and mute the user for `12` hours. Use `antispam.window_size`, `antispam.window_minutes` and `antispam.timeout_hours` respectively to customize these values.
- When a spam event is detected, a message will be sent to your console channel with details regarding the incident, along with the options to remove the timeout, delete the messages, or kick the user from the server.

## Configuring Wikidot Applications Proxy
- Set `wikidot.name` to the name of your wiki. For example `scp-wiki` or `wanderers-library` for the official SCP wikis.
- Set `wikidot.user` and `wikidot.password` to the credentials of a Wikidot user who has administrator rights on your wiki.
    - Make sure no one else can read your config file while you're at it
    - Also keep in mind that this *can't* be read through any command, but *can* be changed by administrators. If this is a problem for you, check `constants.py` and you should be able to figure out how to protect specific config keys
- By default, the bot checks for new applications every 30 minutes. The check can also be triggered manually using `/applications`
- Once an application is received, it will be forwarded to your console channel with an option to either reject or accept it

## Configuring Confessions
- This one is simple, set `channels.confessions` to one of your admin channels. Users will then be able to use the `/confess` command to send you a message to that channel.
- The users have an option for their name to be sent as well, or for the confession to remain anonymous. The usernames of users confessing anonymously **will be redacted from the bot's logs as well**.

## Configuring Gatekeeper
**WIP**

## Configuring Image Processing Tools
**WIP**

## Configuring Lost
**WIP**
