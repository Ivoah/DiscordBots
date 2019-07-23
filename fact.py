#!/usr/bin/env python3.6

import io
import json
import bash
import random
import aiohttp
import asyncio
import discord
import functools
import collections

import stackie

FCC_API = 'http://data.fcc.gov/api/license-view/basicSearch/getLicenses?searchValue={}&pageSize=1&format=json'
WA_API = 'https://api.wolframalpha.com/v2/result'

with open('tokens.json') as f:
    f = json.load(f)
    TOKEN = f['fact']
    WA_APPID = f['wolfram_alpha']

class FactSphere(discord.Client):
    async def play_file(self, filename):
        try:
            voice = await self.join_voice_channel(self.channels['music room'])
            player = voice.create_ffmpeg_player(f'Audio/{filename}', after=functools.partial(asyncio.run_coroutine_threadsafe, voice.disconnect(), self.loop))
            player.start()
        except discord.errors.ClientException:
            pass

    async def on_ready(self):
        print(discord.utils.oauth_url(self.user.id))
        self.roles = {r.name: r for r in list(self.servers)[0].roles}
        self.channels = {c.name: c for c in list(self.servers)[0].channels}

        with open('facts.json') as f:
            self.facts = json.load(f)

        with open('xkcd.json') as f:
            self.comics = json.load(f)

        self.chain = collections.defaultdict(lambda: [])

        for fact in self.facts:
            for pair in zip(['<start>'] + fact.split(), fact.split() + ['<end>']):
                self.chain[pair[0]].append(pair[1])
        print(f'Logged in as {self.user.name}: {self.user.id}')

    async def on_message(self, message):
        print(f'#{message.channel.name}: {message.content}')
        if message.author.bot or self.roles['Timeout of Shame'] in message.author.roles or len(message.content) == 0: return
        cmd = message.content.split()[0]
        args = message.content[len(cmd) + 1:]
        #if cmd == '!calm':
        #    await self.send_message(message.channel, f'{args} you need to calm down')
        if message.content == 'git gud':
            await self.send_message(message.channel, '```git: \'gud\' is not a git command. See \'git --help\'.\n\nThe most similar command is\n    gui```')
        elif cmd == '!img':
            if not args or args == 'help':
                await self.send_message(message.channel, 'https://github.com/Lerc/stackie/blob/master/README.md')
            else:
                try:
                    args = args.replace('`', '')
                    img = io.BytesIO()
                    stackie.gen_image(args).save(img, 'png')
                    img.seek(0)
                    await self.send_file(message.channel, img, filename=f'{args}.png')
                except RuntimeError:
                    await self.send_message(message.channel, '```There was an error running your code```')
        #elif cmd == '!exam':
        #    await self.send_message(message.channel, f'{args} don\'t you have an exam to study for?')
        elif cmd == '!dad':
            await self.play_file('ahh_dad.wav')
        elif cmd == '!soup':
            await self.play_file('soup.m4a')
        elif cmd == '!wine':
            await self.play_file('wine.m4a')
        elif cmd == '!':
            await self.play_file('chime.m4a')
        elif cmd == '!bash':
            print(args, args.split())
            if args == '':
                await self.send_message(message.channel, f'```{bash.random()}```')
            elif args.split()[0] == 'lucky':
                results = bash.search(' '.join(args.split()[1:]))
                if results:
                    quote = bash.get_quote(results[0])
                else:
                    quote = 'No results found'
                await self.send_message(message.channel, f'```{quote}```')
            else:
                try:
                    quote = bash.get_quote(int(args))
                    await self.send_message(message.channel, f'```{quote}```')
                except ValueError:
                    results = bash.search(args)
                    if len(results) == 1:
                        quote = bash.get_quote(int(results[0]))
                        await self.send_message(message.channel, f'```{quote}```')
                    else
                        await self.send_message(message.channel, f'Search results:\n```{", ".join(results) or "No results found"}```')
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
        elif cmd == '!wa':
            async with aiohttp.get(WA_API, params={'appid': WA_APPID, 'input': args}) as response:
                answer = await response.text()
                await self.send_message(message.channel, f'```{answer}```')
        elif cmd == '!xkcd':
            if args == 'update':
                with open('xkcd.json') as f:
                    self.comics = json.load(f)
            elif args in self.comics.keys():
                await self.send_message(message.channel, f'https://xkcd.com/{args}/')
            else:
                results = []
                await self.send_typing(message.channel)
                for comic in self.comics.values():
                    if args.lower() == comic['title'].lower():
                        await self.send_message(message.channel, f'https://xkcd.com/{comic["num"]}/')
                        return
                    for word in args.lower().split():
                        if word not in ' '.join([str(v) for v in comic.values()]).lower():
                            break
                    else:
                        results.append(comic)
                        if len(results) == 10:
                            break
                if len(results) == 1:
                    await self.send_message(message.channel, f'https://xkcd.com/{results[0]["num"]}/')
                else:
                    await self.send_message(message.channel, f'''```Results:\n\n{chr(10).join(f'{comic["num"]}: {comic["title"]}' for comic in results)}```''')
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
            if self.facts[fact] is not None:
                await self.play_file(self.facts[fact])
            await self.send_message(message.channel, fact)

sphere = FactSphere()
sphere.run(TOKEN)
