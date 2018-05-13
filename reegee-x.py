import re
import json
import discord

'''
async def doit(chat, match):
    fr = match.group(1)
    to = match.group(2)
    to = to.replace('\\/', '/')
    try:
        fl = match.group(3)
        if fl == None:
            fl = ''
        fl = fl[1:]
    except IndexError:
        fl = ''

    # Build Python regex flags
    count = 1
    flags = 0
    for f in fl:
        if f == 'i':
            flags |= re.IGNORECASE
        elif f == 'g':
            count = 0
        else:
            await chat.reply('unknown flag: {}'.format(f))
            return

    async def substitute(original, msg):
        try:
            s, i = re.subn(fr, to, original, count=count, flags=flags)
            if i > 0:
                return (await Chat.from_message(bot, msg).reply(s))['result']
        except Exception as e:
            await chat.reply('u dun goofed m8: ' + str(e))

    # Handle replies
    if 'reply_to_message' in chat.message:
        # Try to find the original message text
        message = chat.message['reply_to_message']
        original = find_original(message)
        if not original:
            return

        return await substitute(original, message)

    else:
        # Try matching the last few messages
        for msg in reversed(last_msgs[chat.id]):
            original = find_original(msg)
            if not original:
                continue

            return await substitute(original, msg)


@bot.command(r'^s/((?:\\/|[^/])+)/((?:\\/|[^/])*)(/.*)?')
async def test(chat, match):
    msg = await doit(chat, match)
    if msg:
        last_msgs[chat.id].append(msg)
    pprint(last_msgs[chat.id])


@bot.command(r'(.*)')
@bot.handle('photo')
async def msg(chat, match):
    last_msgs[chat.id].append(chat.message)
'''

with open('tokens.json') as f:
    TOKEN = json.load(f)['reegee-x']

class Reegee(discord.Client):
    async def on_ready(self):
        self.roles = {r.name: r for r in list(self.servers)[0].roles}
        self.channels = {c.name: c for c in list(self.servers)[0].channels}
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
                    await self.send_message(message.channel, f'Unrecognized flag: {flag}')
                    return

            async for msg in self.logs_from(message.channel, limit=25):
                try:
                    if msg.content != message.content and re.search(_from, msg.content):
                        await self.send_message(message.channel, re.sub(_from, to, msg.content, count=count))
                        return
                except Exception as e:
                    await self.send_message(message.channel, f'u dun goofed m8: {e}')

reegee = Reegee()
reegee.run(TOKEN)
