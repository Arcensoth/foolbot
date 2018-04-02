import logging
import random
import requests
from discord import Message, Server, User
from discord.ext import commands
from io import BytesIO

log = logging.getLogger(__name__)

BOOPS = ('boop', 'beep')


def random_boop():
    return BOOPS[random.randint(0, len(BOOPS) - 1)]


class FoolBot(commands.Bot):
    def __init__(self, target_user, target_channels, nickname=None, **options):
        super().__init__(command_prefix='\\', **options)
        self.target_user = target_user
        self.target_channels = set(target_channels)
        self.nickname = nickname

    async def on_ready(self):
        log.info('Logged in as {} (id {})'.format(self.user.name, self.user.id))

        user: User = await self.get_user_info(self.target_user)

        channels = (self.get_channel(channel_id) for channel_id in self.target_channels)
        channels_str = ', '.join('#' + str(channel) for channel in channels)

        log.info('Targeting user {} on channels {}'.format(str(user), channels_str))

        nickname = self.nickname or user.name

        log.info('Setting nickname: {}'.format(nickname))
        for server in self.servers:
            server: Server = server
            try:
                await self.http.change_my_nickname(server.id, nickname)
                log.info('  Succeeded in server: {}'.format(str(server)))
            except:
                log.info('  Failed in server: {}'.format(str(server)))

        avatar_url = 'https://cdn.discordapp.com/avatars/{0.id}/{0.avatar}.png?size=256'.format(user)

        log.info('Setting avatar: {}'.format(avatar_url))

        try:
            image_response = requests.get(avatar_url)
            image_data = image_response.content
            await self.edit_profile(avatar=image_data)
        except:
            log.warning('Ignoring invalid avatar')

        log.info('All set!')

    async def on_message(self, message: Message):
        # only listen for messages from target users on target channels
        if (message.author.id == self.target_user) and (message.channel.id in self.target_channels):
            log.info('[{}#{}@{}] {}'.format(message.server, message.channel, message.author, message.content))
            content = message.content + ' ' + random_boop()
            await self.send_message(message.channel, content)
            for attachment in message.attachments:
                attachment_url = attachment.get('url')
                attachment_filename = attachment.get('filename')
                log.info('Found attachment: {}'.format(attachment_filename))
                try:
                    attachment_response = requests.get(attachment_url)
                    attachment_fp = BytesIO(attachment_response.content)
                    await self.send_file(message.channel, attachment_fp, filename=attachment_filename)
                except:
                    log.exception('Failed to send attachment: {}'.format(attachment_filename))
                    await self.send_message(message.channel, attachment_url)
            await self.delete_message(message)
