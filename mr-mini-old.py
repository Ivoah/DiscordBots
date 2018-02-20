#!/usr/bin/env python3.6

import json
import asyncio
import aiohttp
import discord
import collections
from concurrent.futures import CancelledError

FCC_API = 'http://data.fcc.gov/api/license-view/basicSearch/getLicenses?searchValue={}&pageSize=1&format=json'

with open('tokens.json') as f:
    TOKEN = json.load(f)['mr-mini']

class MrMini(discord.Client):
    queue = collections.deque()
    playing = False
    repeat = False
    skip = False
    music_task = None

    async def on_ready(self):
        print(discord.utils.oauth_url(self.user.id))
        self.roles = {r.name: r for r in list(self.servers)[0].roles}
        self.channels = {c.name: c for c in list(self.servers)[0].channels}
        print(f'Logged in as {self.user.name}: {self.user.id}')

    async def play_queue(self, message):
        self.music_task = asyncio.Task.current_task()
        self.playing = True

        voice = await self.join_voice_channel(self.channels['music room'])
        while self.queue:
            try:
                song = self.queue[0]
                player = await voice.create_ytdl_player(song, ytdl_options = {'default_search': 'auto'})
                await self.send_message(message.channel, f'Playing "{player.title}" for {player.duration} seconds')
                player.start()
                await asyncio.sleep(player.duration)
                if self.queue:
                    song = self.queue.popleft()
                    if self.repeat: self.queue.append(song)
            except CancelledError:
                player.stop()
                song = self.queue.popleft()
                if self.repeat: self.queue.append(song)
                if self.skip:
                    self.skip = False
                else:
                    break
        self.playing = False
        await voice.disconnect()

    async def on_message(self, message):
        print(message.content)
        if message.author.bot or self.roles['Timeout of Shame'] in message.author.roles or len(message.content) == 0: return
        cmd = message.content.split()[0]
        args = message.content[len(cmd) + 1:]
        if cmd == '!help':
            if args:
                await self.send_message(message.channel, '```Usage: !help```')
            else:
                with open(__file__) as f:
                    await self.send_message(message.channel, f'You suck {message.author.mention}')
        elif cmd == '!yt':
            if not args:
                await self.send_message(message.channel, '```Usage: !yt <url|search term>```')
                return
            self.queue.append(args)
            await self.send_message(message.channel, f'Added "{args}" to the queue')
            if not self.playing:
                await self.play_queue(message)
        elif cmd == '!stop':
            if args:
                await self.send_message(message.channel, '```Usage: !stop```')
                return
            if self.playing:
                self.queue.clear()
                self.queue.append(None)
                self.music_task.cancel()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!pause':
            if args:
                await self.send_message(message.channel, '```Usage: !pause```')
                return
            if self.playing:
                self.music_task.cancel()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!resume':
            if args:
                await self.send_message(message.channel, '```Usage: !resume```')
                return
            if self.playing:
                await self.send_message(message.channel, 'Music is already playing')
                return
            if not self.queue:
                await self.send_message(message.channel, 'The queue is empty')
                return
            await self.play_queue(message)
        elif cmd == '!skip':
            if args:
                await self.send_message(message.channel, '```Usage: !skip```')
                return
            if self.playing:
                self.skip = True
                self.music_task.cancel()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!queue':
            if args == 'clear':
                self.queue.clear()
                await self.send_message(message.channel, 'Queue cleared')
            elif not args:
                if self.queue:
                    await self.send_message(message.channel, '\n'.join(f'{i + 1}: {s}' for i, s in enumerate(self.queue)))
                else:
                    await self.send_message(message.channel, 'The queue is empty')
            else:
                await self.send_message(message.channel, '```Usage: !queue [clear]```')
        elif cmd == '!repeat':
            if args.lower() in ['on', 'yes', 'true']:
                self.repeat = True
            elif args.lower() in ['off', 'no', 'false']:
                self.repeat = False
            elif args.lower() in ['toggle']:
                self.repeat = not self.repeat
            elif not args:
                await self.send_message(message.channel, f'Repeat is currently {"on" if self.repeat else "off"}')
                return
            else:
                await self.send_message(message.channel, '```Usage: !repeat [on|off|toggle]```')
                return
            await self.send_message(message.channel, f'Repeat set to {self.repeat}')
        elif cmd == '!timeout':
            role = self.roles['Timeout of Shame'] if message.author.server_permissions.administrator else self.roles['Kinda timeout but not really']
            for member in message.mentions:
                await self.add_roles(member, role)
            await asyncio.sleep(60*60*5)
            for member in message.mentions:
                await self.remove_roles(member, role)
        elif cmd == '!reload':
            if args:
                await self.send_message(message.channel, '```Usage: !timeout```')
                return
            await self.on_load()
        elif cmd == '!callsign':
            args = args.split()
            if len(args) != 1:
                await self.send_message(message.channel, '```Usage: !callsign <callsign>```')
                return
            callsign = args[0]
            async with aiohttp.get(FCC_API.format(callsign)) as response:
                json = await response.json()
                try:
                    license = json['Licenses']['License'][0]
                    embed = discord.Embed(title=license['licName'], url=license['licDetailURL'])
                    del license['licName']
                    del license['licDetailURL']
                    for key, value in license.items():
                        embed.add_field(name=key, value=value)
                    await self.send_message(message.channel, embed=embed)
                except KeyError:
                    await self.send_message(message.channel, f'Could not find callsign "{callsign}"')

mr_mini = MrMini()
mr_mini.run(TOKEN)
