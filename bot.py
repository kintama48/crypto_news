import asyncio
import json
import os
import platform
import sys

import requests
import telegram
from discord.ext import tasks
from discord.ext.commands import Bot
from discord.utils import get
from telegram.ext import Updater
from telegram.utils.helpers import escape_markdown

from utils import *
from db_utils import Database

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

intents = discord.Intents.default()
discord_bot = Bot(command_prefix=config["bot_prefix"], intents=intents)

updater = Updater(token=config["telegram_token"], use_context=True)
telegram_bot = updater.bot

db = Database()


@discord_bot.event
async def on_ready():
    print(f"Logged in as {discord_bot.user.name}")
    print(f"Discord.py API version: {discord.__version__}")
    print(f"Python version: {platform.python_version()}")
    print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
    if not news.is_running():
        news.start()
    updater.start_polling()  # timeout=30


@tasks.loop(minutes=2)
async def news():
    response = requests.get(url=config["news"]).json()['Data'][0]

    channels = []
    for id in config['discord_channel_ids']:
        channels.append(get(discord_bot.get_all_channels(), id=id))

    if int(response['id']) > db.get_news_id():
        print("True:", response)
        embed = news_helper(response)
        for channel in channels:
            await channel.send(embed=embed)
        telegram_bot.send_message(chat_id=config['telegram_channel_id'],
                                  text=escape_markdown(create_telegram_msg(response), version=2),
                                  parse_mode='MarkdownV2')
#         telegram_bot.send_message(chat_id=config['telegram_channel_id'],
#                                   text=create_telegram_msg(response),
#                                   parse_mode='MarkdownV2')
        db.set_news_id(response['id'])
        await asyncio.sleep(120)


discord_bot.run(config["discord_token"])
