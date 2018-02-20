#!/usr/bin/env python3.6

import os
import pty
import pyte
import json
import psutil
import random
import asyncio
import discord
import functools

client = discord.Client()

LYDIA = '371130000474112021'

with open('tokens.json') as f:
    TOKEN = json.load(f)['jeb']

@client.event
async def on_ready():
    global music_room
    print(discord.utils.oauth_url(client.user.id))
    print(f'Logged in as {client.user.name}: {client.user.id}')
    music_room = discord.utils.find(lambda ch: ch.name == 'music room', client.get_all_channels())

@client.event
async def on_message(message):
    if message.author.bot or len(message.content) == 0: return
    cmd = message.content.split()[0]
    if cmd == '!calm':
        await client.send_message(message.channel, f'{message.content[6:]} you need to calm down'.strip())
    elif cmd == '!exam':
        await client.send_message(message.channel, f'{message.content[6:]} don\'t you have an exam to study for?'.strip())
    elif cmd == '!dad':
        try:
            voice = await client.join_voice_channel(music_room)
            player = voice.create_ffmpeg_player('ahh_dad.wav', after=functools.partial(asyncio.run_coroutine_threadsafe, voice.disconnect(), client.loop))
            player.start()
        except discord.errors.ClientException:
            pass
    elif cmd == '!sl':
        screen = pyte.Screen(25, 22)
        stream = pyte.ByteStream(screen)
        msg = await client.send_message(message.channel, '```' + '\n'.join(screen.display) + '```')
        pid, fd = pty.fork()
        if pid == 0:
            os.execle('/usr/games/sl', '/usr/games/sl', {'TERM': 'linux', 'COLUMNS': '25', 'LINES': '22'})
        else:
            sl = psutil.Process(pid)
            try:
                while True:
                    stream.feed(os.read(fd, 2**16))
                    await client.edit_message(msg, '```' + '\n'.join(screen.display) + '```')
            except OSError: pass

client.run(TOKEN)
