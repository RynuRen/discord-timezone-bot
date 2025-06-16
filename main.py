import discord
import asyncio
from datetime import datetime
import pytz
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 채널 ID를 여기에 입력
CHANNELS = {
    "SEOUL": {"id": 123456789012345678, "tz": "Asia/Seoul", "emoji": "🇰🇷"},
    "HCMC": {"id": 987654321098765432, "tz": "Asia/Ho_Chi_Minh", "emoji": "🇻🇳"},
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    for name, info in CHANNELS.items():
        channel = client.get_channel(info["id"])
        if channel:
            tz = pytz.timezone(info["tz"])
            now = datetime.now(tz).strftime("%H:%M")
            new_name = f"{info['emoji']} {now}"
            await channel.edit(name=new_name)
            print(f"{name} → {new_name}")
    await client.close()

client.run(TOKEN)
