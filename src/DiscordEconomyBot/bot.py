import discord
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

TOKEN = "bot token goes here"
STEAMID_CHANNEL_ID = 1267970972917567572
CHAT_CHANNEL_ID = 1268032353234714665
CHAT_FILE = "chat.txt"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

class ChatFileHandler(FileSystemEventHandler):
    def __init__(self, channel):
        self.channel = channel

    def on_modified(self, event):
        if event.src_path == os.path.abspath(CHAT_FILE):
            print(f"{CHAT_FILE} has been modified.")
            with open(CHAT_FILE, "r") as f:
                content = f.read().strip()
            if content:
                print(f"New content detected: {content}")
                client.loop.create_task(self.channel.send(content))

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    steamid_channel = client.get_channel(STEAMID_CHANNEL_ID)
    chat_channel = client.get_channel(CHAT_CHANNEL_ID)

    await post_steamid_connections(steamid_channel)

    event_handler = ChatFileHandler(chat_channel)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    print("Observer has started monitoring the chat file.")

    # Keep the observer running in the background
    asyncio.get_event_loop().create_task(keep_observer_running(observer))

async def keep_observer_running(observer):
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        observer.stop()
        observer.join()

async def post_steamid_connections(channel):
    if os.path.exists("steamid_connections.txt"):
        with open("steamid_connections.txt", "r") as f:
            connections = f.readlines()

        if connections:
            max_message_length = 2000
            code_block = "```"
            message = code_block

            for connection in connections:
                if len(message) + len(connection) + len(code_block) > max_message_length:
                    message += code_block
                    await channel.send(message)
                    message = code_block  # Reset message with opening code block
                message += connection

            if message != code_block:
                message += code_block
                await channel.send(message)

client.run(TOKEN)