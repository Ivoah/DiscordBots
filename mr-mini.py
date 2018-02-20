#!/usr/bin/env python3.6

import json
import asyncio
import aiohttp
import discord
import functools
import youtube_dl
import collections
from concurrent.futures import CancelledError

FCC_API = 'http://data.fcc.gov/api/license-view/basicSearch/getLicenses?searchValue={}&pageSize=1&format=json'

with open('tokens.json') as f:
    TOKEN = json.load(f)['mr-mini']

class MrMini(discord.Client):
    queue = []
    player = None
    repeat = False

    async def on_ready(self):
        print(discord.utils.oauth_url(self.user.id))
        self.roles = {r.name: r for r in list(self.servers)[0].roles}
        self.channels = {c.name: c for c in list(self.servers)[0].channels}
        print(f'Logged in as {self.user.name}: {self.user.id}')

    async def play_song(self, message):
        if self.is_voice_connected(message.server):
            voice = self.voice_client_in(message.server)
        else:
            voice = await self.join_voice_channel(self.channels['music room'])

        if self.player:
            if self.repeat:
                self.queue.append(self.queue.pop(0))
            else:
                self.queue.pop(0)

        if self.queue:
            song = self.queue[0]
            self.player = voice.create_ffmpeg_player(song['url'], after=functools.partial(asyncio.run_coroutine_threadsafe, self.play_song(message), self.loop))
            await self.send_message(message.channel, f'Playing "{song["title"]}" for {song["duration"]} seconds')
            self.player.start()
        else:
            self.player = None
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
            with youtube_dl.YoutubeDL({'default_search': 'auto', 'format': 'webm[abr>0]/bestaudio/best'}) as ytdl:
                song = ytdl.extract_info(args, download=False)
                if 'entries' in song:
                    song = song['entries'][0]
                self.queue.append(song)
                await self.send_message(message.channel, f'Added "{song["title"]}" to the queue')
            if self.player is None:
                await self.play_song(message)
        elif cmd == '!stop':
            if args:
                await self.send_message(message.channel, '```Usage: !stop```')
                return
            if self.player:
                del self.queue[1:]
                self.player.stop()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!pause':
            if args:
                await self.send_message(message.channel, '```Usage: !pause```')
                return
            if self.player:
                self.player.pause()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!resume':
            if args:
                await self.send_message(message.channel, '```Usage: !resume```')
                return
            if self.player:
                self.player.resume()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!skip':
            if args:
                await self.send_message(message.channel, '```Usage: !skip```')
                return
            if self.player:
                self.player.stop()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!queue':
            args = args.split()
            if args and args[0] == 'clear':
                if len(args) == 1:
                    if self.player:
                        del self.queue[1:]
                    else:
                        self.queue.clear()
                    await self.send_message(message.channel, 'Queue cleared')
                elif len(args) == 2:
                    try:
                        n = int(args[1])
                        if 1 < n <= len(self.queue):
                            del self.queue[n - 1]
                        else:
                            await self.send_message(message.channel, 'Can\'t delete that item')
                    except ValueError:
                        await self.send_message(message.channel, '```Usage: !queue [clear [n]]```')
                else:
                    await self.send_message(message.channel, '```Usage: !queue [clear [n]]```')
            elif not args:
                if self.queue:
                    await self.send_message(message.channel, '\n'.join(f'{i + 1}: {s["title"]}' for i, s in enumerate(self.queue)))
                else:
                    await self.send_message(message.channel, 'The queue is empty')
            else:
                await self.send_message(message.channel, '```Usage: !queue [clear [n]]```')
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
            for member in message.mentions:
                await self.add_roles(member, self.roles['Kinda timeout but not really'])
        elif cmd == '!outtime':
            if message.author.server_permissions.administrator:
                for member in message.mentions:
                    await self.add_roles(member, self.roles['Timeout of Shame'])
            else:
                self.send_message(message.channel, 'Plebs can\'t use !outtime')
        elif cmd == '!reload':
            if args:
                await self.send_message(message.channel, '```Usage: !reload```')
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
