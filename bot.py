#!/usr/bin/env python3.6

import re
import json
import discord
import inspect

from pprint import pprint

with open('tokens.json') as f:
    TOKEN = json.load(f)['bot-bot']

types = {
    int: r'(\d+)',
    str: r'(\w+)',
    discord.Member: r'(?:<@(\d+)>)'
}

class Bot(discord.Client):
    async def on_ready(self):
        self.commands = {}
        for command, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not command.startswith('cmd'): continue
            params = list(inspect.signature(method).parameters.values())[1:]
            regex = f'!{command[4:]}' + ' ' + ' '.join(types[param.annotation] + ('?' if param.default is not inspect._empty else '') for param in params)
            self.commands[command] = (re.compile(regex.strip()), [param.annotation for param in params], method)

        pprint(self.commands)

        for server in self.servers:
            for channel in server.channels:
                if channel.type == discord.ChannelType.text:
                    await self.send_message(channel, 'Bot-bot started')
                    break

    async def on_message(self, message):
        print(f'#{message.channel.name}: {message.content}')
        if message.author.bot or not message.content: return
        for command in self.commands:
            match = self.commands[command][0].match(message.content)
            if match is not None:
                await self.commands[command][2](message.channel, *(self.commands[command][1][i](p) for i, p in enumerate(match.groups())))
                break

    async def cmd_bot(self, channel):
        await self.send_message(channel, 'Bot!')

    async def cmd_hit(self, channel, user: discord.Member):
        await self.send_message(channel, f'{user.mention} has been hit')

    async def cmd_add(self, channel, v1: int, v2: int, v3: int=0):
        await self.send_message(channel, v1 + v2 + v3)

bot = Bot()
bot.run(TOKEN)
