#!/usr/bin/env python3.6

import json
import random
import asyncio
import discord
import functools
import collections

with open('../tokens.json') as f:
    TOKEN = json.load(f)['fact']

class FactSphere(discord.Client):
    async def play_file(self, filename):
        try:
            voice = await self.join_voice_channel(self.channels['music room'])
            player = voice.create_ffmpeg_player(filename, after=functools.partial(asyncio.run_coroutine_threadsafe, voice.disconnect(), self.loop))
            player.start()
        except discord.errors.ClientException:
            pass

    async def on_ready(self):
        print(discord.utils.oauth_url(self.user.id))
        self.roles = {r.name: r for r in list(self.servers)[0].roles}
        self.channels = {c.name: c for c in list(self.servers)[0].channels}
        with open('facts.json') as f:
            self.facts = json.load(f)

        self.chain = collections.defaultdict(lambda: [])

        for fact in self.facts:
            for pair in zip(['<start>'] + fact.split(), fact.split() + ['<end>']):
                self.chain[pair[0]].append(pair[1])
        print(f'Logged in as {self.user.name}: {self.user.id}')

    async def on_message(self, message):
        print(message.content)
        if message.author.bot or self.roles['Timeout of Shame'] in message.author.roles or len(message.content) == 0: return
        cmd = message.content.split()[0]
        args = message.content[len(cmd) + 1:]
        #if cmd == '!calm':
        #    await self.send_message(message.channel, f'{args} you need to calm down')
        if cmd == '!exam':
            await self.send_message(message.channel, f'{args} don\'t you have an exam to study for?')
        elif cmd == '!dad':
            await self.play_file('ahh_dad.wav')
        elif cmd == '!soup':
            await self.play_file('soup.m4a')
        elif cmd == '!wine':
            await self.play_file('wine.m4a')
        elif cmd == '!fact':
            if args:
                if args == 'list':
                    await self.send_message(message.channel, 'A list of all facts can be found here: https://theportalwiki.com/wiki/List_of_Fact_Sphere_facts')
                    return
                elif args == 'markov':
                    msg = ''
                    word = random.choice(self.chain['<start>'])
                    while word != '<end>':
                        msg += word + ' '
                        word = random.choice(self.chain[word])
                    await self.send_message(message.channel, msg.strip())
                    return
                else:
                    found = False
                    for fact in self.facts:
                        if not all(word.lower() in fact.lower() for word in args.split()):
                            continue
                        found = True
                        break
                    if not found: fact = 'Fact not found.'
            else:
                fact = random.choice(list(self.facts))
            await self.play_file(self.facts[fact])
            await self.send_message(message.channel, fact)

sphere = FactSphere()
sphere.run(TOKEN)
