import argparse
import logging.config

# parse args and setup logging before anything else
from foolbot.fool_bot import FoolBot

arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('--log', help='Log level', default='WARNING')
arg_parser.add_argument(
    '-c', '--target_channel', action='append', default=[], help='channel ids to listen for messages on (repeatable)')
arg_parser.add_argument(
    '-n', '--nickname', default=None, help='nickname for the bot, defaults to target username')
arg_parser.add_argument('target_user', help='user id to listen for messages from (repeatable)')
arg_parser.add_argument('token', help='bot token to authenticate with')

args = arg_parser.parse_args()

LOG_FMT = '%(asctime)s [%(name)s/%(levelname)s] %(message)s'
RESTART_DELAY = 10

# attempt to use colorlog, if available
try:
    import colorlog
    import sys

    formatter = colorlog.ColoredFormatter(
        fmt='%(log_color)s' + LOG_FMT + '%(reset)s',
        log_colors={
            'DEBUG': 'blue',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'white,bg_red',
        }
    )

    handler = colorlog.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    logging.root.setLevel(args.log)

# otherwise just stick with basic logging
except:
    logging.basicConfig(
        level=args.log,
        format=LOG_FMT)

log = logging.getLogger(__name__)

import asyncio
import time


def _attempt_logout(loop, bot):
    try:
        log.warning('Attempting clean logout...')
        loop.run_until_complete(bot.logout())

        log.info('Gathering leftover tasks...')
        pending = asyncio.Task.all_tasks(loop=loop)
        gathered = asyncio.gather(*pending, loop=loop)

        log.info('Cancelling leftover tasks...')
        gathered.cancel()

        log.info('Allowing cancelled tasks to finish...')
        try:
            loop.run_until_complete(gathered)
        except:
            pass

    except:
        log.exception('Encountered an error while attempting to logout')
        log.critical('Forcibly terminating with system exit')
        exit()


def run():
    loop = asyncio.get_event_loop()

    while True:
        log.info('Starting bot...')
        bot = FoolBot(
            target_user=args.target_user, target_channels=args.target_channel, nickname=args.nickname,
            loop=loop)

        try:
            loop.run_until_complete(bot.start(args.token))

        except KeyboardInterrupt:
            log.info('Keyboard interrupt detected')
            _attempt_logout(loop, bot)
            break

        except:
            log.exception('Encountered a fatal exception')
            _attempt_logout(loop, bot)

        log.info('Closing event loop...')
        loop.close()

        log.warning('Restarting bot in {} seconds...'.format(RESTART_DELAY))
        time.sleep(RESTART_DELAY)

        log.info('Opening a new event loop...')
        loop = asyncio.new_event_loop()

    log.info('Closing event loop for good...')
    loop.close()

    log.warning('Bot successfully terminated')


log.info('Hello!')
run()
log.info('Goodbye!')
