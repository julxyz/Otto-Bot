from __future__ import print_function

import os
import sys
import json
import urls
import sched
import aiohttp
import discord
import random
import asyncio
import requests
import calendar
import ids as ids
import steamgrab
import lists as lists
import time as time
import dateutil.parser
from httplib2 import Http
from datetime import datetime
from html.parser import HTMLParser
from contextlib import contextmanager
from oauth2client import file, client, tools
from googleapiclient.discovery import build

# just btw frick python ok thx

#timestamps
def st():
    x = datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y %H:%M:%S')
    return x
def nowday():
    x = datetime.fromtimestamp(time.time()).strftime('%d')
    return x
def nowtime():
    x = datetime.fromtimestamp(time.time()).strftime('%H')
    return eval(x)

print("[{0}] loading ...".format(st()))

#stupid variables
TOKEN = os.environ["TOKEN"] #discord token
bot = discord.Client() #yes
bot_prefix = "!" #self explenatory
timeout = 600 #calendar refresh rate (recommended 900 (15mins))
voice = None #yikes
messagexpamount = 1 #amount of xp the user gets per message

class commandclass:
    #has all the commands that can be invoked by a chatmessage
    def __init__(self):
        pass

    class ffaclass:
        #for the ffa command
        def __init__(self):
            pass
        
        async def amount(self, amountRange):
            #how many kills
            if amountRange == 500:
                amount = random.choice([200, 250, 300, 350, 400, 450, 500])
            elif amountRange == 200:
                amount = random.choice([100, 125, 150, 175, 200, 225, 250])
            return amount

        async def gettype(self):
            #ffa type
            types = ["A"] * 30 + ["B"] * 30 + ["C"] * 10 + ["D"] * 10 + ["E"] * 10 + ["F"] * 10
            typesdict = {
                "A": "Kills im FFA mit einer beliebigen Waffe",
                "B": "Kills im __**hso**__ FFA mit einer beliebigen Waffe",
                "C": "FFA Kills (only Pistol, keine Deagle)",
                "D": "__**hso**__ FFA Kills (only Pistol, keine Deagle)",
                "E": "Deagle Kills im FFA",
                "F": "Deagle Kills im __**hso**__ FFA"
            }
            randomtype = random.choice(types)
            #get right amount of kills
            if randomtype == "A" or randomtype == "B":
                randomamount = await self.amount(500)
            else:
                randomamount = await self.amount(200)
            randomtype = typesdict[randomtype]
            return randomamount, randomtype

        async def me(self, message):
            #ffa yourself
            await bot.purge_from(message.channel, limit=1)
            amount, randomtype = await self.gettype()
            await bot.send_message(message.channel, "{0}\n Mach bis morgen um *{1} Uhr* {2} {3}!".format(message.author.mention, nowtime(), amount, randomtype))
            print("[{0}] gave {1} FFA task: {2} {3}".format(st(), message.author, amount, randomtype))

        async def all(self, message):
            #ffa everyone with certain role
            await bot.purge_from(message.channel, limit=1)
            role = 544909084021882880 #get role "Nazbol Hq" by id
            amount, randomtype = await self.gettype()
            await bot.send_message(message.channel, "<@&{0}>\nBis morgen *{1} Uhr* mach jeder {2} {3}!".format(role, nowtime(), amount, randomtype))
            print("[{0}] gave everyone FFA task: {1} {2}".format(st(), amount, randomtype))

    class calendarclass:

        def __init__(self):
            self.scopes = 'https://www.googleapis.com/auth/calendar.readonly'
            
        #google calendar api integration
        async def grabevent(self, amount):
            #grabs event from google calendar
            #
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            cfile = open("calendartoken.json")  
            json.dump(json.loads(os.environ["calendartoken"]), cfile)
            cfile.close()
            #print(os.environ["calendartoken"])
            store = file.Storage("calendartoken.json")
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets(os.environ["credentials"], self.scopes)
                creds = tools.run_flow(flow, store)
            service = build('calendar', 'v3', http=creds.authorize(Http()))

            # Call the Calendar API
            now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
            print('[{0}] calendar: Searching for an upcoming event'.format(st()))
            events_result = service.events().list(calendarId='primary', timeMin=now, maxResults=amount, singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])

            if not events:
                print('[{0}] calendar: No upcoming event found.'.format(st()))
                return 0
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                event_description = event.get('description', 'no description')
                event_end =  dateutil.parser.parse(end)
                event_end = event_end.strftime('%H:%M')
                event_time = dateutil.parser.parse(start)
                event_time = event_time.strftime('%H:%M')
                event_time_day = dateutil.parser.parse(start)
                event_time_day = event_time_day.strftime('%d')
                event_date = dateutil.parser.parse(start)
                event_date = event_date.strftime('%d-%m-%Y')
                calendar_event = [event_date, event_time, event['summary'], event_time_day, event_end, event_description, event['id']]
                print("[{0}] calendar: grabbed event - {1}".format(st(), calendar_event[2]))
                return calendar_event

        async def on_event(self):
            run = True
            while run:
                await bot.wait_until_ready()
                calendar_event = await self.grabevent(1)
                f = open("eventid", "r")
                id = f.readline()
                f.close()
                if (calendar_event[3] != nowday() or calendar_event == 0): #only if event is today
                    print("[{0}] calendar: didn't echo (event not today)".format(st()))
                    await asyncio.sleep(3600)
                elif id == calendar_event[6]:
                    print("[{0}] calendar: already echoed that event".format(st())) #check if event has already been echoed (eventid)
                    await asyncio.sleep(timeout)
                else: #write new calendar id and echo
                    await self.echo_event(calendar_event)
                    f = open("eventid", "w")
                    f.write(calendar_event[6])
                    f.close()
                    print("[{0}] calendar: echoed event from calendar loop".format(st()))
                    await asyncio.sleep(timeout)

        async def echo_event(self, calendar_event):
            #echoes event
            if (nowtime() > 10 and nowtime() < 22): #only between 10am and 10pm
                channel = bot.get_channel(ids.server["calendarChannel"])
                embed=discord.Embed(title="{0}".format(calendar_event[2]), url="http://bit.ly/2RAUFC7", color=0xee0000)
                embed.set_author(name="Your next event:", icon_url=urls.botpp)
                embed.add_field(name=calendar_event[0], value="{0} - {1}".format(calendar_event[1], calendar_event[4]), inline=True)
                embed.add_field(name="‏‏‏ ‏‏‏", value=calendar_event[5], inline=False)
                embed.set_thumbnail(url="https://www.freeiconspng.com/download/19230")
                embed.set_footer(text="brought to you by jul")
                await bot.send_message(channel, "@here", embed=embed)
            else:
                print("[{0}] calendar: didn't echo (I feel so sleepy)".format(st()))
                pass

        async def giveevent(self, message, whotomention):
            #only mentions user/ invoked by command
            calendar_event = await self.grabevent(1)
            embed=discord.Embed(title="{0}".format(calendar_event[2]), url="http://bit.ly/2RAUFC7", color=0xee0000)
            embed.set_author(name="Your next event:", icon_url=urls.botpp)
            embed.add_field(name=calendar_event[0], value="{0} - {1}".format(calendar_event[1], calendar_event[4]), inline=True)
            embed.add_field(name="‏‏‏ ‏‏‏", value=calendar_event[5], inline=False)
            embed.set_thumbnail(url="https://www.freeiconspng.com/download/19230")
            embed.set_footer(text="brought to you by jul")
            await bot.send_message(message.channel, "{0}".format(whotomention), embed=embed)

    class levelsystem:

        def __init__(self):
            self.previousMessageAuthorId = None

        async def addxp(self, message, xpamount):
            #worst code I've ever written
            user = message.author.id
            import csv
            leveldbfile = (open("leveldb.csv"))
            leveldb = csv.reader(leveldbfile)
            leveldb = dict(leveldb)
            try:
                oldxpamount = eval(leveldb.get(user))
            except TypeError:
                leveldb[user] = "0"
                oldxpamount = eval(leveldb.get(user))
            newxpamount = oldxpamount + xpamount
            leveldb[user] = newxpamount
            writelist = []
            for key, value in leveldb.items():
                writelist.append("{0},{1}\n".format(key, value))
            writelist = "".join(writelist)
            leveldbfile.close()
            leveldbfile = open("leveldb.csv", "w")
            leveldbfile.write(writelist)
            leveldbfile.close()

        async def resetPrevious(self):
            run = True
            while run:
                self.previousMessageAuthorId = None
                await asyncio.sleep(30)
            
    class commandfunctions:

        def __init__(self):
            pass

        class Joke:

            def __init__(self, id, contents):
                self.id = id
                self.contents = contents

            def __str__(self):
                return self.contents

        async def searchr34(self, searchterm):
            #r34 api
            import rule34
            loop = asyncio.get_event_loop()
            rule34 = rule34.Rule34(loop)
            url = await rule34.getImageURLS(searchterm)
            try:
                return random.choice(url)
            except TypeError:
                print("[{0}] found nothing".format(st()))
                return 0

        async def getjoke(self):
            r = requests.get('https://icanhazdadjoke.com', headers={"Accept":"application/json"})
            raw_joke = r.json()
            joke = self.Joke(raw_joke['id'], raw_joke['joke'])
            return joke

        async def jokes(self):
            run = True
            while run:
                channel = bot.get_channel(ids.server["jokeChannel"])
                joke = await self.getjoke()
                embed=discord.Embed()
                embed.add_field(name="Here is your joke-to-counter-toxicity™:", value="*{0}*".format(str(joke)), inline=False)
                embed.set_footer(text="brought to you by icanhazdadjoke.com")
                await bot.send_message(channel, embed=embed)
                print("[{0}] sent joke".format(st()))
                await asyncio.sleep(14400)

        async def getperms(self, message):
            authorroles = message.author.roles
            i = 0
            try:
                for role in authorroles:
                    authorroles[i] = role.id
                    i = i+1
            except AttributeError:
                pass
            if ids.server.get("adminRole") in authorroles:
                permlevel = 2
            elif ids.server.get("modRole") in authorroles:
                permlevel = 1
            else:
                permlevel = 0
            return permlevel

        async def steamNews(self):
            values = await steamgrab.grabSteamNews()
            articleLink, publication, title, preview, newsId = values[0], values[1], values[2], values[3], values[4]
            f = open("newsid", "r")
            oldid = f.readline()
            f.close()
            if oldid != newsId:
                channel = bot.get_channel(ids.server["newsChannel"])
                embed=discord.Embed(title=title, url =articleLink, description=preview, color=0x5bffff)
                embed.set_author(name=publication)
                await bot.send_message(channel, "Here is your latest news:", embed=embed)
                f = open("newsid", "w")
                f.write(newsId)
                f.close()
                print("[{0}] sent latest news".format(st()))
                await asyncio.sleep(28800)
            else:
                print("[{0}] no news".format(st()))
                await asyncio.sleep(28800)
        
    async def help(self, message, permlevel):
        #sends message with all commands from lists.py
        await bot.purge_from(message.channel, limit=1)
        await bot.send_message(message.channel, '{0}'.format("".join(lists.helplist)))
        print("[{0}] sent help".format(st()))
    
    async def opinion(self, message, permlevel):
        #random bs
        msg = random.choice(lists.opinions)
        await bot.purge_from(message.channel, limit=1)
        await bot.send_message(message.channel, '{0}'.format(msg))
        print("[{0}] gave opinion".format(st()))
            
    async def ffa(self, message, permlevel):
        #ffa command --> self.ffaclass
        choice = message.content[1:].split(' ', 1)
        await getattr(getffa, choice[1], "me")(message)

    async def stop(self, message, permlevel):
        #stops the bot
        if permlevel == 2:
            await bot.purge_from(message.channel, limit=1)
            await bot.logout()
            print("                      ----------------------------------------\n[{0}] ended\n\n\nplease restart the bot".format(st()))
        else:
            await bot.send_message(message.channel, "{0} You do not have the permissions to use this command".format(message.author.mention))
            await asyncio.sleep(2)
            await bot.purge_from(message.channel, limit=1)
    
    async def r34(self, message, permlevel):
        #r34 command --> searchr34(tag)
        tag = message.content[1:].split(' ', 1)
        await bot.purge_from(message.channel, limit=1)
        url = await functions.searchr34(tag[1])
        if url != 0:
            await bot.send_message(message.channel, content=url)
            print("[{0}] sent r34 for {1}".format(st(), tag[1]))
        else:
            pass

    async def nuke(self, message, permlevel):
        #map strats
        await bot.purge_from(message.channel, limit=1)
        embed=discord.Embed(title="Go here to view your Nuke strats.", url=urls.nukedoc, color=0xfede01)
        embed.set_author(name="Nuke strats", url=urls.nukedoc, icon_url=urls.botpp)
        embed.set_thumbnail(url=urls.nukeicon)
        embed.set_footer(text="brought to you by jul")
        await bot.send_message(message.channel, "{0}".format(message.author.mention), embed=embed)
        print("[{0}] sent nuke strats".format(st()))

    async def mirage(self, message, permlevel):
        #map strats
        await bot.purge_from(message.channel, limit=1)
        embed=discord.Embed(title="Go here to view your Mirage strats.", url=urls.miragedoc, color=0x30e9e4)
        embed.set_author(name="Mirage strats", url=urls.miragedoc, icon_url=urls.botpp)
        embed.set_thumbnail(url=urls.mirageicon)
        embed.set_footer(text="brought to you by jul")
        await bot.send_message(message.channel, "{0}".format(message.author.mention), embed=embed)
        print("[{0}] sent mirage strats".format(st()))

    async def overpass(self, message, permlevel):
        #map strats
        await bot.purge_from(message.channel, limit=1)
        embed=discord.Embed(title="Go here to view your Overpass strats.", url=urls.overpassdoc, color=0x000000)
        embed.set_author(name="Overpass strats", url=urls.overpassdoc, icon_url=urls.botpp)
        embed.set_thumbnail(url=urls.overpassicon)
        embed.set_footer(text="brought to you by jul")
        await bot.send_message(message.channel, "{0}".format(message.author.mention), embed=embed)
        print("[{0}] sent overpass strats".format(st()))

    async def event(self, message, permlevel):
        #giveevent @user
        await bot.purge_from(message.channel, limit=1)
        await calendar.giveevent(message, message.author.mention)
        print("[{0}] sent event @user".format(st()))

    async def echoevent(self, message, permlevel):
        #giveevent @here
        await bot.purge_from(message.channel, limit=1)
        await calendar.giveevent(message, "@here")
        print("[{0}] echoed event (request by user)".format(st()))

    async def clear(self, message, permlevel):
        #clear messages
        if permlevel >= 1:
            amount = message.content.strip('{0}clear'.format(bot_prefix))
            await bot.purge_from(message.channel, limit=1)
            await bot.send_message(message.channel, "Clearing...")
            try:
                amount = int(amount)
                if amount < 51:
                    if amount > 0:
                        try:
                            await bot.purge_from(message.channel, limit=amount+1)
                        except discord.errors.HTTPException:
                            await bot.purge_from(message.channel, limit=1)
                            await bot.send_message(message.channel, "Unable to delete message")
                            await asyncio.sleep(2)
                            await bot.purge_from(message.channel, limit=1)
                        await bot.send_message(message.channel, "Deleted {0} messages".format(amount))
                        print("[{1}] Deleted {0} messages".format(amount, st()))
                        await asyncio.sleep(2)
                        await bot.purge_from(message.channel, limit=1)
                    else:
                        await bot.purge_from(message.channel, limit=1)
                        await bot.send_message(message.channel, "Usage : !clear <number between 1-50>")
                else:
                    await bot.purge_from(message.channel, limit=1)
                    await bot.send_message(message.channel, "Usage : !clear <number between 1-50>")
            except ValueError:
                await bot.purge_from(message.channel, limit=1)
                await bot.send_message(message.channel, "Usage : !clear <number between 1-50>")
        else:
            await bot.send_message(message.channel, "{0} You do not have the permissions to use this command".format(message.author.mention))
            await asyncio.sleep(2)
            await bot.purge_from(message.channel, limit=1)

    async def play(self, message, permlevel):
        #plays youtube video in users voicechannel
        global voice
        url = message.content[1:].split(' ', 1)
        try:
            voice = await bot.join_voice_channel(message.author.voice.voice_channel)
        except discord.errors.ClientException:
            await voice.disconnect()  
            voice = await bot.join_voice_channel(message.author.voice.voice_channel)
        player = await voice.create_ytdl_player(url = url[1])
        player.start()

commands = commandclass()
getffa = commands.ffaclass()
level = commands.levelsystem()
calendar = commands.calendarclass()
functions = commands.commandfunctions()

@bot.event
async def on_ready():
    print("[{0}] bot ready".format(st()))
    await bot.change_presence(game=discord.Game(name="the Kaiserreich™"))
    bot.loop.create_task(calendar.on_event())
    bot.loop.create_task(level.resetPrevious())
    bot.loop.create_task(functions.jokes())
    #bot.loop.create_task(functions.steamNews())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    elif message.channel.is_private:
        return

    if message.content.startswith('{0}'.format(bot_prefix)):
        msgcontent = message.content[1:]
        msgcontent = msgcontent.split(' ', 1)
        authorperms = await functions.getperms(message)
        await getattr(commands, msgcontent[0])(message, authorperms)

    if message.author.id != level.previousMessageAuthorId:
        await level.addxp(message, messagexpamount)
        level.previousMessageAuthorId = message.author.id

@bot.event 
async def on_member_join(member):
    channel = bot.get_channel(ids.server["jokeChannel"])
    await bot.send_message(channel, "Taking over the world™\nWelcome {0}.".format(member.mention))
    print("[{0}] said hi".format(st()))

@bot.event
async def on_member_ban(member):
    channel = bot.get_channel(ids.server["jokeChannel"])
    await channel.send("{0} just got annihilated!! RIP {0}".format(member.mention))
    print("[{0}] said hi".format(st()))

try:
    bot.run(TOKEN)
except aiohttp.errors.ClientOSError:
    print("[{0}] !!! unable to connect to discord !!!".format(st()))

print("done!")