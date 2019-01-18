#!/usr/bin/env python3.6

# https://www.youtube.com/watch?v=2aMRH_pQQhQ

import json
import peewee
import discord

from getpass import getpass

with open('tokens.json') as f:
    f = json.load(f)
    TOKEN = f['fact']
    DB_PW = f['mysql']

db = peewee.MySQLDatabase('discord', host='ivoah.net', user='discord', password=DB_PW)

class Log(peewee.Model):
    id = peewee.BigIntegerField()
    timestamp = peewee.DateTimeField()
    channel = peewee.BigIntegerField()
    author = peewee.BigIntegerField()
    content = peewee.TextField()
    attachments = peewee.TextField()

    class Meta:
        table_name = 'logs'
        database = db

    @classmethod
    def log(self, message):
        self.create(
            id=message.id,
            timestamp=message.timestamp,
            channel=message.channel.id,
            author=message.author.id,
            content=message.content,
            attachments=json.dumps(message.attachments)
        )

class Channel(peewee.Model):
    id = peewee.BigIntegerField()
    name = peewee.TextField()

    class Meta:
        table_name = 'channels'
        database = db

class Member(peewee.Model):
    id = peewee.BigIntegerField()
    name = peewee.TextField()
    nick = peewee.TextField()
    avatar = peewee.TextField()

    class Meta:
        table_name = 'members'
        database = db

class FactSphere(discord.Client):
    async def on_ready(self):
        with db:
            ΣωΣ = list(self.servers)[0]
            for member in ΣωΣ.members:
                try:
                    Member.create(id=member.id, name=member.name, nick=member.nick, avatar=member.avatar_url or member.default_avatar_url)
                except peewee.IntegrityError:
                    Member.update(nick=member.nick, avatar=member.avatar_url or member.default_avatar_url).where(Member.id == member.id).execute()
            for channel in ΣωΣ.channels:
                if not channel.permissions_for(ΣωΣ.me).read_messages or channel.type != discord.ChannelType.text: continue

                try:
                    Channel.create(id=channel.id, name=channel.name)
                except peewee.IntegrityError:
                    pass

                msg = 0
                async for message in self.logs_from(channel, limit=100):
                    msg += 1
                    print(f'\r#{channel.name}: {msg}', end='')
                    try:
                        Log.log(message)
                    except peewee.IntegrityError:
                        pass
                print()

        print(f'Logged in as {self.user.name}: {self.user.id}')

    async def on_message(self, message):
        with db:
            Log.log(message)

sphere = FactSphere()
sphere.run(TOKEN)
