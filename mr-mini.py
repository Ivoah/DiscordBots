#!/usr/bin/env python3.6

import json
import pickle
import asyncio
import discord
import datetime
import functools
import youtube_dl
import collections
from concurrent.futures import CancelledError

with open('tokens.json') as f:
    TOKEN = json.load(f)['mr-mini']

def ftime(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'

class Playlist():
    def __init__(self, filename):
        self.filename = filename
        try:
            with open(self.filename, 'rb') as f:
                self.queue = pickle.load(f)
        except FileNotFoundError:
            self.queue = []

    def __len__(self):
        return len(self.queue)

    def __iter__(self):
        return iter(self.queue)

    def update(self):
        with open(self.filename, 'wb') as f:
            pickle.dump(self.queue, f)

    def rotate(self):
        if self.queue:
            self.queue.append(self.queue.pop(0))
        self.update()

    def add(self, song):
        self.queue.append(song)
        self.update()

    def clear(self, a=None, b=None):
        if a is None and b is None:
            self.queue = []
        elif b is None:
            del self.queue[a]
        else:
            del self.queue[a:b]
        self.update()

    def peek(self):
        return self.queue[0]

    def pop(self):
        val = self.queue.pop(0)
        self.update()
        return val

class MrMini(discord.Client):
    async def on_ready(self):
        self.start_time = datetime.datetime.now()
        self.queue = Playlist('queue.pickle')
        self.player = None
        self.repeat = False
        self.skip_cooldown = datetime.datetime.now()

        print(discord.utils.oauth_url(self.user.id))
        self.roles = {r.name: r for r in list(self.servers)[0].roles}
        self.channels = {c.name: c for c in list(self.servers)[0].channels}
        print(f'Logged in as {self.user.name}: {self.user.id}')

        if self.queue:
            await self.play_song(self.channels['hades'])

    async def play_song(self, channel):
        if self.is_voice_connected(channel.server):
            voice = self.voice_client_in(channel.server)
        else:
            voice = await self.join_voice_channel(self.channels['music room'])

        self.skip_cooldown = datetime.datetime.now()

        if self.player:
            if self.repeat:
                self.queue.rotate()
            else:
                self.queue.pop()

        if self.queue:
            song = self.queue.peek()
            self.player = voice.create_ffmpeg_player(song['url'], after=functools.partial(asyncio.run_coroutine_threadsafe, self.play_song(channel), self.loop))
            await self.send_message(channel, f'Playing "{song["title"]}" ({ftime(song["duration"])})')
            self.player.start()
        else:
            self.player = None
            await voice.disconnect()

    async def on_message(self, message):
        print(f'#{message.channel.name}: {message.content}')
        if message.channel.name == 'acropolis':
            if message.content.startswith('Suggestion: ') and not message.author.bot:
                await self.pin_message(message)
            elif message.type == discord.MessageType.pins_add:
                await self.delete_message(message)
        if message.author.bot or self.roles['Timeout of Shame'] in message.author.roles or not message.content: return
        cmd = message.content.split()[0]
        args = message.content[len(cmd) + 1:]
        if cmd == '!yt':
            if not args:
                await self.send_message(message.channel, '```Usage: !yt <url|search term>```')
                return
            with youtube_dl.YoutubeDL({'default_search': 'ytsearch', 'format': 'webm[abr>0]/bestaudio/best'}) as ytdl:
                song = ytdl.extract_info(args, download=False)
                if 'entries' in song:
                    song = song['entries'][0]
                self.queue.add(song)
                await self.send_message(message.channel, f'Added "{song["title"]}" to the queue ({ftime(song["duration"])})')
            if self.player is None:
                await self.play_song(self.channels['hades'])
        elif cmd == '!stop':
            if args:
                await self.send_message(message.channel, '```Usage: !stop```')
                return
            if self.player:
                self.queue.clear(1, -1)
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
                if (datetime.datetime.now() - self.skip_cooldown).seconds >= 5:
                    self.player.stop()
                    self.skip_cooldown = datetime.datetime.now()
            else:
                await self.send_message(message.channel, 'Nothing is playing')
        elif cmd == '!queue':
            args = args.split()
            if args and args[0] == 'clear':
                if len(args) == 1:
                    if self.player:
                        self.queue.clear(1, -1)
                    else:
                        self.queue.clear()
                    await self.send_message(message.channel, 'Queue cleared')
                elif len(args) == 2:
                    try:
                        n = int(args[1])
                        if 1 < n <= len(self.queue):
                            self.queue.clear(n - 1)
                        else:
                            await self.send_message(message.channel, 'Can\'t delete that item')
                    except ValueError:
                        await self.send_message(message.channel, '```Usage: !queue [clear [n]]```')
                else:
                    await self.send_message(message.channel, '```Usage: !queue [clear [n]]```')
            elif not args:
                if self.queue:
                    await self.send_message(message.channel, '\n'.join(f'{i + 1}: {s["title"]} ({ftime(s["duration"])})' for i, s in enumerate(self.queue)) + f'\n\n{ftime(sum(s["duration"] for s in self.queue))} total')
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
        elif cmd == '!uptime':
            bot_uptime = datetime.datetime.now() - self.start_time
            try:
                with open('/proc/uptime', 'r') as f:
                    system_uptime = str(timedelta(seconds = float(f.read().split()[0])))
            except FileNotFoundError:
                system_uptime = None

            if system_uptime:
                await self.send_message(message.channel, f'```Bot: {bot_uptime}\nSystem: {system_uptime}```')
            else:
                await self.send_message(message.channel, f'```Bot: {bot_uptime}```')

    async def on_member_update(self, before, after):
        IVOAH = '150801519975989248'
        if after.id == IVOAH and self.roles['Freshie'] in after.roles:
            await self.remove_roles(after, self.roles['Freshie'])
        elif after.id == self.user.id:
            for role in after.roles:
                if 'waifu' in role.name.lower():
                    await self.remove_roles(after, role)

mr_mini = MrMini()
mr_mini.run(TOKEN)
