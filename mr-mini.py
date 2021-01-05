#!/bin/sh
"exec" "`dirname $0`/venv/bin/python" "$0" "$@"

import json
import pickle
import peewee
import asyncio
import discord
import datetime
import youtube_dl
import collections
from concurrent.futures import CancelledError

with open('tokens.json') as f:
    f = json.load(f)
    TOKEN = f['mr-mini']
    DB_PW = f['mysql']

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

db = peewee.MySQLDatabase('discord', host='ivoah.net', user='discord', password=DB_PW)

class Entry(peewee.Model):
    song = peewee.TextField()
    date = peewee.DateTimeField()

    class Meta:
        table_name = 'music_history'
        database = db

class MrMini(discord.Client):
    async def on_ready(self):
        self.start_time = datetime.datetime.now()
        self.queue = Playlist('queue.pickle')
        self.voice = None
        self.playing = False
        self.repeat = False
        self.skip_cooldown = datetime.datetime.now()

        print(discord.utils.oauth_url(self.user.id))
        self.roles = {r.name: r for r in list(self.guilds)[0].roles}
        self.channels = {c.name: c for c in list(self.guilds)[0].channels}
        print(f'Logged in as {self.user.name}: {self.user.id}')

        if self.queue:
            await self.play_song(self.channels['hades'])

    async def play_song(self, channel, error=None):
        if error:
            print(f'Error: {error}')
            return
        if self.voice is None or not self.voice.is_connected():
            self.voice = await self.channels['music room'].connect()

        self.skip_cooldown = datetime.datetime.now()

        if self.playing:
            if self.repeat:
                self.queue.rotate()
            else:
                self.queue.pop()

        if self.queue:
            song = self.queue.peek()
            self.voice.play(discord.FFmpegPCMAudio(song['url']), after=lambda err: asyncio.run_coroutine_threadsafe(self.play_song(channel, err), self.loop))
            self.playing = True
            await channel.send(f'Playing "{song["title"]}" ({ftime(song["duration"])})')
            await self.change_presence(activity=discord.Activity(name=song['title'], url=song['url'], type=discord.ActivityType.listening))
            with db:
                Entry.create(song=json.dumps(song), date=datetime.datetime.now())
        else:
            self.playing = False
            await self.change_presence()
            await self.voice.disconnect()

    async def on_message(self, message):
        print(f'#{message.channel.name}: {message.content}')
        if message.channel.name == 'acropolis':
            if message.content.startswith('Suggestion: ') and not message.author.bot:
                await message.pin()
            elif message.type == discord.MessageType.pins_add:
                await message.delete()
        if message.author.bot or self.roles['Timeout of Shame'] in message.author.roles or not message.content: return
        cmd = message.content.split()[0]
        args = message.content[len(cmd) + 1:]
        if cmd == '!yt':
            if not args:
                await message.channel.send('```Usage: !yt <url|search term>```')
                return
            with youtube_dl.YoutubeDL({'default_search': 'ytsearch', 'format': 'webm[abr>0]/bestaudio/best'}) as ytdl:
                song = ytdl.extract_info(args, download=False)
                if 'entries' in song:
                    song = song['entries'][0]
                self.queue.add(song)
                await message.channel.send(f'Added "{song["title"]}" to the queue ({ftime(song["duration"])})')
            if not self.playing:
                await self.play_song(self.channels['hades'])
        elif cmd == '!stop':
            if args:
                await message.channel.send('```Usage: !stop```')
                return
            if self.playing:
                self.queue.clear(1, -1)
                self.voice.stop()
            else:
                await message.channel.send('Nothing is playing')
        elif cmd == '!pause':
            if args:
                await message.channel.send('```Usage: !pause```')
                return
            if self.playing:
                self.voice.pause()
            else:
                await message.channel.send('Nothing is playing')
        elif cmd == '!resume':
            if args:
                await message.channel.send('```Usage: !resume```')
                return
            if self.playing:
                self.voice.resume()
            else:
                await message.channel.send('Nothing is playing')
        elif cmd == '!skip':
            if args:
                await message.channel.send('```Usage: !skip```')
                return
            if self.playing:
                if (datetime.datetime.now() - self.skip_cooldown).seconds >= 5:
                    self.voice.stop()
                    self.skip_cooldown = datetime.datetime.now()
            else:
                await message.channel.send('Nothing is playing')
        elif cmd == '!queue':
            args = args.split()
            if args and args[0] == 'clear':
                if len(args) == 1:
                    if self.playing:
                        self.queue.clear(1, -1)
                    else:
                        self.queue.clear()
                    await message.channel.send('Queue cleared')
                elif len(args) == 2:
                    try:
                        n = int(args[1])
                        if 1 < n <= len(self.queue):
                            self.queue.clear(n - 1)
                        else:
                            await message.channel.send('Can\'t delete that item')
                    except ValueError:
                        await message.channel.send('```Usage: !queue [clear [n]]```')
                else:
                    await message.channel.send('```Usage: !queue [clear [n]]```')
            elif not args:
                if self.queue:
                    await message.channel.send('\n'.join(f'{i + 1}: {s["title"]} ({ftime(s["duration"])})' for i, s in enumerate(self.queue)) + f'\n\n{ftime(sum(s["duration"] for s in self.queue))} total')
                else:
                    await message.channel.send('The queue is empty')
            else:
                await message.channel.send('```Usage: !queue [clear [n]]```')
        elif cmd == '!repeat':
            if args.lower() in ['on', 'yes', 'true']:
                self.repeat = True
            elif args.lower() in ['off', 'no', 'false']:
                self.repeat = False
            elif args.lower() in ['toggle']:
                self.repeat = not self.repeat
            elif not args:
                await message.channel.send(f'Repeat is currently {"on" if self.repeat else "off"}')
                return
            else:
                await message.channel.send('```Usage: !repeat [on|off|toggle]```')
                return
            await message.channel.send(f'Repeat set to {self.repeat}')
        elif cmd == '!timeout':
            for member in message.mentions:
                await member.add_roles(self.roles['Kinda timeout but not really'])
        elif cmd == '!outtime':
            if message.channel.permissions_for(message.author).administrator:
                for member in message.mentions:
                    await member.add_roles(self.roles['Timeout of Shame'])
            else:
                message.channel.send('Plebs can\'t use !outtime')
        elif cmd == '!reload':
            if args:
                await message.channel.send('```Usage: !reload```')
                return
            await self.on_load()
        elif cmd == '!uptime':
            if args:
                await message.channel.send('```Usage: !uptime```')
                return

            bot_uptime = datetime.datetime.now() - self.start_time
            try:
                with open('/proc/uptime', 'r') as f:
                    system_uptime = str(datetime.timedelta(seconds = float(f.read().split()[0])))
            except FileNotFoundError:
                system_uptime = None

            if system_uptime:
                await message.channel.send(f'```Bot: {bot_uptime}\nSystem: {system_uptime}```')
            else:
                await message.channel.send(f'```Bot: {bot_uptime}```')
        elif cmd == '!vidya':
            if args:
                await message.channel.send('```Usage: !vidya```')
                return
            
            if self.roles['Vidya Gaems'] in message.author.roles:
                await message.author.remove_roles(self.roles['Vidya Gaems'])
                await message.channel.send(f'Removed {self.roles["Vidya Gaems"].mention} from {message.author.mention}')
            else:
                await message.author.add_roles(self.roles['Vidya Gaems'])
                await message.channel.send(f'Added {self.roles["Vidya Gaems"].mention} to {message.author.mention}')

    async def on_member_update(self, before, after):
        IVOAH = '150801519975989248'
        if after.id == self.user.id:
            for role in after.roles:
                if 'aifu' in role.name.lower():
                    await after.remove_roles(role)

mr_mini = MrMini()
mr_mini.run(TOKEN)
