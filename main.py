import os
import asyncio
import discord
from discord.ext import commands
from fbchat import Client
from fbchat.models import *
import aiohttp
import subprocess
from datetime import datetime

# --- Beállítások Secrets-ből ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")
MESSENGER_THREAD_ID = os.getenv("MESSENGER_THREAD_ID")

# --- Discord bot kliens ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Unknown felhasználók számozása
unknown_counter = 0
unknown_map = {}  # {author_id: "Unknown N"}

# --- Cache az utolsó 50 üzenethez szerkesztéshez ---
last_50_messenger = []  # [(msg_id, timestamp)]
last_50_discord = []    # [(msg_id, timestamp)]

# --- Messenger kliens ---
class MessengerListener(Client):
    async def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        global unknown_counter

        if thread_id == MESSENGER_THREAD_ID and author_id != self.uid:
            sender = await self.fetchUserInfo(author_id)

            if author_id in sender:
                user = sender[author_id]
                name = user.name if user.name else None
                avatar_url = user.photo if user.photo else None
            else:
                name = None
                avatar_url = None

            if not name:
                if author_id not in unknown_map:
                    unknown_counter += 1
                    unknown_map[author_id] = f"Unknown {unknown_counter}"
                name = unknown_map[author_id]

            if not avatar_url:
                avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"

            text = message_object.text or ""

            # Csatolmány kezelése
            if message_object.attachments:
                for att in message_object.attachments:
                    if isinstance(att, VideoAttachment):
                        local_file = "input.mp4"
                        converted_file = "output.3gp"
                        await self._download_file(att.url, local_file)
                        cmd = [
                            "ffmpeg", "-i", local_file,
                            "-vf", "scale=288:216", "-r", "30",
                            "-c:v", "h263", "-c:a", "aac",
                            "-ac", "1", "-ar", "48000",
                            converted_file, "-y"
                        ]
                        subprocess.run(cmd, check=True)
                        await send_webhook(DISCORD_WEBHOOK_URL, name, avatar_url, text, file=converted_file)
                    else:
                        await send_webhook(DISCORD_WEBHOOK_URL, name, avatar_url, text, file=att.url)
            else:
                await send_webhook(DISCORD_WEBHOOK_URL, name, avatar_url, text)

            # Cache frissítése
            last_50_messenger.append((message_object.uid, message_object.timestamp))
            if len(last_50_messenger) > 50:
                last_50_messenger.pop(0)

    async def _download_file(self, url, filename):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(filename, "wb") as f:
                    f.write(await resp.read())

# --- Webhook küldő ---
async def send_webhook(webhook_url, username, avatar_url, content, file=None):
    async with aiohttp.ClientSession() as session:
        data = {
            "username": username,
            "avatar_url": avatar_url,
            "content": content
        }
        if file:
            if os.path.exists(file):
                with open(file, "rb") as f:
                    form = aiohttp.FormData()
                    form.add_field("payload_json", str(data), content_type="application/json")
                    form.add_field("file", f, filename=os.path.basename(file))
                    await session.post(webhook_url, data=form)
            else:
                data["content"] = f"{content}\n{file}"
                await session.post(webhook_url, json=data)
        else:
            await session.post(webhook_url, json=data)

# --- Discord oldali üzenet fogadó (Discord → Messenger) ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if str(message.channel.id) == str(DISCORD_CHANNEL_ID):
        fb_client.send(Message(text=message.content), thread_id=MESSENGER_THREAD_ID, thread_type=ThreadType.GROUP)

        # Cache frissítés
        last_50_discord.append((message.id, message.created_at.timestamp()))
        if len(last_50_discord) > 50:
            last_50_discord.pop(0)

# --- Discord üzenet szerkesztés figyelése ---
@bot.event
async def on_message_edit(before, after):
    if str(after.channel.id) == str(DISCORD_CHANNEL_ID):
        # Frissítés Messengerbe
        fb_client.send(Message(text=f"[Edited]: {after.content}"), thread_id=MESSENGER_THREAD_ID, thread_type=ThreadType.GROUP)

# --- Teljes chat szinkronizálás indításkor ---
async def full_sync():
    # Messenger üzenetek visszaolvasása a legelejétől
    messenger_msgs = []
    offset = None
    while True:
        batch = fb_client.fetchThreadMessages(thread_id=MESSENGER_THREAD_ID, limit=100, before=offset)
        if not batch:
            break
        messenger_msgs.extend(batch)
        offset = batch[-1].uid
        if len(batch) < 100:
            break
    messenger_msgs.reverse()  # Időrendbe

    # Discord üzenetek lekérése
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    discord_msgs = [msg async for msg in channel.history(limit=None, oldest_first=True)]

    # --- Szinkronizálás ---
    discord_contents = {m.content: m for m in discord_msgs}
    for m in messenger_msgs:
        text = m.text or ""
        if text not in discord_contents:
            # Küldés Discord webhook
            sender = await fb_client.fetchUserInfo(m.author)
            name = sender[m.author].name if m.author in sender else "Unknown"
            avatar = sender[m.author].photo if m.author in sender else "https://cdn.discordapp.com/embed/avatars/0.png"
            await send_webhook(DISCORD_WEBHOOK_URL, name, avatar, text)

    messenger_contents = {m.content: m for m in messenger_msgs}
    for d in discord_msgs:
        if d.content not in messenger_contents:
            # Küldés Messengerbe
            fb_client.send(Message(text=d.content), thread_id=MESSENGER_THREAD_ID, thread_type=ThreadType.GROUP)

# --- Indítás ---
async def start_bot():
    global fb_client
    fb_client = MessengerListener(FB_EMAIL, FB_PASSWORD)

    await bot.wait_until_ready()
    await full_sync()  # Teljes szinkron induláskor
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(start_bot())