#!/usr/bin/env python3.6

import json
import discord
import inspect

from pprint import pprint

with open('tokens.json') as f:
    TOKEN = json.load(f)['bot-bot']

types = {
    'int': r'\d+',
    'str': r'\w+',
    'mention': r'<@\d+>'
}

def parse_arg(arg):
    return arg

class Bot(discord.Client):
    async def on_ready(self):
        self.commands = {}
        for command, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if not command.startswith('cmd'): continue
            doc = inspect.getdoc(method)
            regex = doc.split()[1] + ' '
            args = doc.split()[2:]
            regex += ' '.join(parse_arg(arg) for arg in args)

            self.commands[regex] = method

        pprint(self.commands)

        for server in self.servers:
            for channel in server.channels:
                if channel.type == discord.ChannelType.text:
                    #await self.send_message(channel, 'Bot-bot has joined the fray!')
                    break

    async def on_message(self, message):
        print(f'#{message.channel.name}: {message.content}')
        if message.author.bot or not message.content: return
        cmd = message.content.split()[0]
        args = message.content[len(cmd) + 1:]
        if cmd == '!help':
            print('U suck')

    async def cmd_bot(self, channel):
        '''Usage: !bot'''
        await self.send_message(channel, 'Bot!')

    async def cmd_add(self, channel, v1, v2, v3=0):
        '''Usage: !add <v1:int> <v2:int> [v3:int]'''
        await self.send_message(channel, v1 + v2 + v3)

bot = Bot()
bot.run(TOKEN)
