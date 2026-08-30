# Builtins
from typing import cast
from logging import info, error, warning
from datetime import datetime, timedelta

# External
import discord
from discord.ext import tasks
from discord.utils import MISSING
from peewee import (AutoField, CharField, TimestampField, IntegerField)

# Internal
from core.modulebase import ModuleBase
from core.models import ModelBase
from core.singletons import config
from core.botbase import MonikaBot
from utils.discordutils import get_message_url

class StarboardModule(ModuleBase):

    @staticmethod
    def env_override():
        return "disable_starboard"
    
    @staticmethod
    def name():
        return "Starboard"
    
    @staticmethod
    def config_required():
        return ['channels.starboard', 'channels.console', 'starboard.threshold', 'starboard.emoji']
    
    def format_config(self):
        emoji = [str(e.name) for e in self.emoji]
        excluded = [str(e) for e in self.excluded]
        return [
            f'ID Starboard kanálu: {self.channel}',
            f'Hranice pro pin: {self.threshold}',
            f'Sledované reakce: {", ".join(emoji)}',
            f'Ignorované kanály: {", ".join(excluded)}'
        ]

    def format_stats(self):
        pinned_count = StarboardPinnedMessage.select().where(StarboardPinnedMessage.pinned_at.is_null(False)).count()
        record_count = StarboardPinnedMessage.select().count()
        return [
            f"Připnutých zpráv: {pinned_count}",
            f"Záznamů ve starboard tabulce: {record_count}"
        ]

    def __init__(self, bot: MonikaBot):
        self.bot: MonikaBot = bot
        self.threshold: int = config.get_value('starboard.threshold')
        self.channel: int = config.get_value('channels.starboard')
        self.console: int = config.get_value('channels.console')
        self.excluded: set[int] = set(config.get('starboard.excluded_channels') or {})
        self.emoji: set[discord.PartialEmoji] = {discord.PartialEmoji.from_str(e) for e in config.get_value('starboard.emoji')}

        purge_days = config.get('starboard.db_purge_days')
        if purge_days:
            self.purge_hours = int(purge_days) * 24
            # Just create the Loop object manually, putting a dynamic value in a decorator is weird
            self.purge_loop_handle = tasks.Loop(self.purge_old_messages,
                                                MISSING,
                                                self.purge_hours,
                                                MISSING,
                                                MISSING,
                                                None,
                                                True,
                                                MISSING,
                                                False)
            self.purge_loop_handle.start()
            tasks.loop()
            info(f"Scheduled DB purge for starboard messsages older than {purge_days} days")
        else:
            warning("Expiration time for starboard records is not set, this might make the database grow very fast in large servers!")

    async def edit_starboard_pin(self, msg: StarboardPinnedMessage):
        if not msg.starboard_id:
            raise RuntimeError("Editing message record with no ID")

        starboard_channel = cast(discord.TextChannel, await self.bot.fetch_channel(self.channel))
        message = await starboard_channel.fetch_message(msg.starboard_id)

        info(f"Edit starboard embed ID {msg.starboard_id} for message {msg.message_id} with {msg.reaction_count} reactions")

        # We'd have to store the channel ID or pass it to the function to get the original channel
        # So we just do a bit of awful string splicing instead
        content_slice = message.content[message.content.find('x'):]
        new_content = f"**{msg.reaction_count}" + content_slice

        await message.edit(embeds=message.embeds, content=new_content)

    @ModuleBase.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # Ignore emojis not used for stars, ignore the starboard channel and also all excluded channels
        if payload.emoji not in self.emoji:
            return
        if payload.channel_id == self.channel:
            return
        if payload.channel_id in self.excluded:
            return

        # Check if the message is already pinned on the starboard with any emoji
        already_pinned = StarboardPinnedMessage.select().where((StarboardPinnedMessage.pinned_at.is_null(False))\
                                                               & (StarboardPinnedMessage.message_id == payload.message_id)).exists()
        if already_pinned:
            msg = StarboardPinnedMessage.get_or_none(message_id = payload.message_id,
                                        emoji = payload.emoji)
            
            if not msg or msg.pinned_at.is_null(True):
                # The reaction has a different emoji than the starboard pin
                # Just ignore it so I can keep my sanity
                return
            
            msg.reaction_count += 1

            # If this is the new highest reaction count, edit the starboard message for it
            # We have to do this check since someone could spam add/remove reactions and overload the API with constant edits
            
            if msg.reaction_count > msg.max_reaction_count:
                await self.edit_starboard_pin(msg)
                msg.max_reaction_count = msg.reaction_count

            # Then save it and return

            msg.save()
            return

        # Retrieve the row, add one reaction, update the max count
        message_model: StarboardPinnedMessage = \
            StarboardPinnedMessage.get_or_create(message_id = payload.message_id,
                                                emoji = payload.emoji)[0]
        
        message_model.reaction_count += 1
        message_model.max_reaction_count = max(message_model.max_reaction_count, message_model.reaction_count)

        # TODO: This is probably redundant
        if message_model.pinned_at is not None:
            return

        if message_model.reaction_count < self.threshold:
            # Still under the threshold, keep the count and wait
            message_model.save()
            return

        # Over the threshold
        message_model.pinned_at = datetime.now()

        # Make sure that the starboard channel is a text channel
        # And that the source channel is either a text channel or a thread
        # I'm not quite sure what happens when we get here with one of the voice-attached text channels
        # But nobody uses those anyway
        channel = await self.bot.fetch_channel(payload.channel_id)
        starboard_channel = await self.bot.fetch_channel(self.channel)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)) or not isinstance(starboard_channel, discord.TextChannel):
            error(f"Attempted to fetch message from invalid channel type, channel ID is {payload.channel_id}")
            console = cast(discord.abc.Messageable, self.bot.get_channel(self.console))
            await console.send("Pokus o načtení špatného typu kanálu v on_raw_reaction_add (TOHLE JE DEFINITIVNĚ BUG)")
            return

        # Grab the message and log it
        message = await channel.fetch_message(payload.message_id)
        info(f"Pin message {payload.message_id} to starboard with {message_model.reaction_count} reactions")

        # Build the embed, fuck around with any potential attachments for a little
        star_embed = discord.Embed()
        star_embed.set_author(name=f"{message.author.display_name}", icon_url=message.author.display_avatar.url)
        star_embed.add_field(name="",
                             value=message.content,
                             inline=False)
        star_embed.add_field(name="", 
                             value=f"**[Skočit na zprávu]({get_message_url(message)})**",
                             inline=False)
        star_embed.set_footer(text=message.created_at.astimezone().strftime("%d.%m.%Y %H:%M:%S"))

        # We can only send a single image in an embed, so we loop over all of them and grab the first one
        if len(message.attachments) > 0:
            for att in message.attachments:
                # Just check the MIME type for 'image', discord doesn't directly tell us if the file is embedded as image
                if not att.content_type:
                    continue
                if att.content_type.startswith("image"):
                    star_embed.set_image(url=att.proxy_url)
                    break
                if att.content_type.startswith("video"):
                    star_embed.add_field(name="",
                                         value=f"{att.proxy_url}")
                    continue

        # Do the same for embeds
        if len(message.embeds) > 0:
            for embed in message.embeds:
                if embed.image:
                    star_embed.set_image(url=embed.image.proxy_url)
                    break
                if embed.thumbnail:
                    star_embed.set_image(url=embed.thumbnail.url)
                    break

        # Finally make the text content for the embed, send the message, and save everything to the database
        channel_and_count = f"**{self.threshold}x {payload.emoji} v <#{message.channel.id}>**"

        starboard_id = (await starboard_channel.send(embed=star_embed, content=channel_and_count)).id
        message_model.starboard_id = starboard_id
        message_model.save()

    @ModuleBase.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.emoji not in self.emoji:
            return
        if payload.channel_id == self.channel:
            return
        if payload.channel_id in self.excluded:
            return
        message_model: StarboardPinnedMessage | None = \
            StarboardPinnedMessage.get_or_none((StarboardPinnedMessage.message_id == payload.message_id)
                                                & (StarboardPinnedMessage.emoji == payload.emoji))
        if not message_model:
            return
        if message_model.reaction_count == 0:
            return
        message_model.reaction_count -= 1
        message_model.save()

    async def purge_old_messages(self):
        cutoff = datetime.now() - timedelta(hours=self.purge_hours)

        query = StarboardPinnedMessage.delete()\
            .where(
                (StarboardPinnedMessage.created_at < cutoff) &
                (StarboardPinnedMessage.pinned_at.is_null()))
        
        deleted_count = query.execute()

        info(f"Purged {deleted_count} expired starboard records")

# ===== Models =====

@StarboardModule.model
class StarboardPinnedMessage(ModelBase):
    id = AutoField()
    message_id = CharField(15) # 15 chars should be enough for the forseeable future
    emoji = CharField(64)
    pinned_at = TimestampField(null=True, default=None)
    reaction_count = IntegerField(default=0)
    max_reaction_count = IntegerField(default=0)
    created_at = TimestampField(default=datetime.now)
    starboard_id = CharField(15, null=True, default=None)