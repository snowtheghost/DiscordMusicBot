# Mini Music Bot Player for Discord
from __future__ import unicode_literals

import asyncio
import os
from typing import Optional

import discord
import youtube_dl
from dotenv import load_dotenv
from youtube_search import YoutubeSearch

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

ydl_opts = {'format': 'bestaudio/best', 'outtmpl': './.requested'}
client = discord.Client()


def clean_files() -> None:
    try:
        os.remove(".requested")
    except FileNotFoundError:
        return


async def disconnect(guild) -> None:
    for vc in client.voice_clients:
        if vc.guild == guild:
            await vc.disconnect()


async def load_audio(message) -> Optional[dict]:
    info = YoutubeSearch(message.content[8:], max_results=1).to_dict()
    if len(info) == 0:
        await message.channel.send("Your query yielded no results.")
        await disconnect(message.guild)
        return
    else:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(['http://www.youtube.com' + info[0]["url_suffix"]])
        return info[0]


async def commence_playback(vc, channel, info) -> None:
    await channel.send(f'Now Playing: {info["title"]}')
    vc.play(discord.FFmpegPCMAudio('.requested'), after=lambda e: print('done', e))

    while vc.is_playing():
        await asyncio.sleep(1)


async def start(message, voice_channel) -> None:
    await disconnect(message.guild)
    vc = await voice_channel.connect()

    info = await load_audio(message)
    if info is None:
        return

    await commence_playback(vc, message.channel, info)
    await disconnect(message.guild)
    clean_files()


async def stop(message) -> None:
    for vc in client.voice_clients:
        if vc.guild == message.guild:
            await message.channel.send("Playback stopped.")
            await disconnect(message.guild)
            clean_files()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    try:
        voice_channel = message.author.voice.channel
    except AttributeError:
        await message.channel.send("You need to be in a voice channel to use this bot.")
        return

    if message.content[0:2] == "mm":
        command = message.content[3:7]
        if command == "play":
            await start(message, voice_channel)
        elif command == "stop":
            await stop(message)
        # TODO help, pause, resume
        else:
            await message.channel.send("The command was not recognized. Type *mm help* for a list of commands.")
        return


clean_files()
client.run(TOKEN)


