#!/usr/bin/env python3.6

import os
import sys
import json
import discord

os.chdir(sys.path[0])

with open('tokens.json') as f:
    TOKEN = json.load(f)['mr-mini']

class MrMini(discord.Client):
    async def on_ready(self):
        self.roles = {r.name: r for r in list(self.guilds)[0].roles}

        for member in list(self.guilds)[0].members:
            await member.remove_roles(self.roles['Timeout of Shame'], self.roles['Kinda timeout but not really'])

        await self.logout()

mr_mini = MrMini()
mr_mini.run(TOKEN)
