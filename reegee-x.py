#!/bin/sh
"exec" "`dirname $0`/venv/bin/python" "$0" "$@"

import re
import json
import discord

# Thanks to Sijmen Schoon for the original regexbot.py code https://github.com/SijmenSchoon/regexbot

with open('tokens.json') as f:
    TOKEN = json.load(f)['reegee-x']

class Reegee(discord.Client):
    async def on_ready(self):
        self.roles = {r.name: r for r in list(self.guilds)[0].roles}
        self.channels = {c.name: c for c in list(self.guilds)[0].channels}
        self.re = re.compile('^`s/((?:\\/|[^/])+?)/((?:\\/|[^/])*?)(?:/(.*))?`')
        print(f'Logged in as {self.user.name}: {self.user.id}')

    async def on_message(self, message):
        print(f'#{message.channel.name}: {message.content}')
        if message.author.bot or self.roles['Timeout of Shame'] in message.author.roles or not message.content: return
        match = self.re.match(message.content)
        if match:
            _from = match[1]
            to = match[2].replace(r'\/', '/')
            flags = match[3] or ''

            count = 1
            re_flags = 0
            for flag in flags:
                if flag == 'i':
                    re_flags |= re.IGNORECASE
                elif flag == 'g':
                    count = 0
                else:
                    await message.reply(f'Unrecognized flag: {flag}')
                    return

            async for msg in message.channel.history(limit=25):
                try:
                    if msg.content != message.content and re.search(_from, msg.content):
                        await msg.reply(re.sub(_from, to, msg.content, count=count, flags=re_flags))
                        return
                except Exception as e:
                    await message.reply(f'u dun goofed m8: {e}')
                    return

reegee = Reegee()
reegee.run(TOKEN)
