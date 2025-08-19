import os
import asyncio
import discord
from discord.ext import commands
import aiohttp
from fbchat import Client, Session
from fbchat.models import *
from keep_alive import keep_alive

# =============== CONFIG ===============
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

# Messenger cookies
FB_COOKIE_CUSER = os.environ["FB_COOKIE_CUSER"]
FB_COOKIE_XS = os.environ["FB_COOKIE_XS"]

MESSENGER_THREAD_ID = os.environ["MESSENGER_THREAD_ID"]

# Szinkronban tartott üzenetek száma figyeléskor
SYNC_LIMIT = 50
# ======================================


# ========== DISCORD OLDAL ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ========== MESSENGER OLDAL ==========
class MessengerListener(Client):
    def __init__(self):
        cookies = {
            "c_user": FB_COOKIE_CUSER,
            "xs": FB_COOKIE_XS,
        }
        session = Session.from_cookies(cookies)
        super().__init__(session=session)

    async def send_to_discord(self, author, text):
        async with aiohttp.ClientSession() as session:
            await session.post(DISCORD_WEBHOOK_URL, json={
                "username": author,
                "content": text
            })

    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        if thread_id != MESSENGER_THREAD_ID:
            return

        author_name = str(author_id)
        text = message_object.text or ""

        asyncio.run_coroutine_threadsafe(
            self.send_to_discord(author_name, text), asyncio.get_event_loop()
        )


# ========== SZINKRONIZÁLÁS ==========
async def sync_history(fb_client, discord_channel):
    """Induláskor: teljes Messenger + Discord történet szinkronizálása"""
    print("[SYNC] Messenger üzenetek letöltése...")
    messenger_msgs = []
    batch = fb_client.fetchThreadMessages(thread_id=MESSENGER_THREAD_ID, limit=100)
    while batch:
        messenger_msgs.extend(batch)
        if len(batch) < 100:
            break
        batch = fb_client.fetchThreadMessages(
            thread_id=MESSENGER_THREAD_ID, limit=100, before=messenger_msgs[-1].timestamp
        )
    messenger_msgs.reverse()

    print(f"[SYNC] {len(messenger_msgs)} Messenger üzenet letöltve")

    print("[SYNC] Discord üzenetek letöltése...")
    discord_msgs = [m async for m in discord_channel.history(limit=None)]
    discord_msgs.reverse()
    print(f"[SYNC] {len(discord_msgs)} Discord üzenet letöltve")

    # Példa: itt egyszerűen csak Messengerből → Discordba küldjük a hiányzókat
    # (haladóban ide jöhet egy duplikátumkezelés timestamp alapján)
    existing_discord_texts = {m.content for m in discord_msgs}
    for msg in messenger_msgs:
        if msg.text and msg.text not in existing_discord_texts:
            await fb_client.send_to_discord(str(msg.author), msg.text)

    print("[SYNC] Szinkronizálás kész.")


# ========== INICIALIZÁLÁS ==========
async def start_bot():
    fb_client = MessengerListener()

    @bot.event
    async def on_ready():
        print(f"[DISCORD] Bejelentkezve mint {bot.user}")
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        await sync_history(fb_client, channel)

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        if message.channel.id == DISCORD_CHANNEL_ID:
            fb_client.send(
                Message(text=message.content),
                thread_id=MESSENGER_THREAD_ID,
                thread_type=ThreadType.GROUP
            )

    keep_alive()
    await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(start_bot())
