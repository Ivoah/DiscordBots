#!/usr/bin/env python3.6

import json
import shlex
import discord
import subprocess

with open('tokens.json') as f:
    TOKEN = json.load(f)['sdr']

class SDR(discord.Client):
    async def on_ready(self):
        print(discord.utils.oauth_url(self.user.id))
        self.roles = {r.name: r for r in list(self.servers)[0].roles}
        self.channels = {c.name: c for c in list(self.servers)[0].channels}
        print(f'Logged in as {self.user.name}: {self.user.id}')

    async def on_message(self, message):
        print(f'#{message.channel.name}: {message.content}')
        if message.author.bot or self.roles['Timeout of Shame'] in message.author.roles or len(message.content) == 0: return
        cmd = message.content.split()[0]
        args = message.content[len(cmd) + 1:]
        if cmd in ['!fm', '!wbfm', '!am', '!usb', '!lsb']:
            mode = cmd[1:]
            freq = args
            voice = await self.join_voice_channel(self.channels['not music'])
            voice.encoder_options(sample_rate=48000, channels=1)
            #rtl_fm = ['rtl_fm', '-M', mode, '-f', freq, '-r', '24k']
            rtl_fm = f'rtl_fm -M {shlex.quote(mode)} -f {shlex.quote(freq)} -r 24k'
            ffmpeg = 'ffmpeg -f s16le -ar 24k -ac 1 -i - -f s16le -ar 48k -ac 1 -'
            p = subprocess.Popen('|'.join((rtl_fm, ffmpeg)), stdout=subprocess.PIPE, shell=True)
            player = discord.voice_client.ProcessPlayer(p, voice, None)
            #player = voice.create_ffmpeg_player('04 Clocktown.mp3')
            player.start()

sdr = SDR()
sdr.run(TOKEN)
