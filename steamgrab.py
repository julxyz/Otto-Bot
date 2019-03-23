import json
import asyncio
import requests
from html.parser import HTMLParser

async def grabSteamNews():
    r = requests.get('http://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/?appid=730&count=1&maxlength=300&format=json')

    decoded = json.loads(r.text)
    htmlparser = HTMLParser()

    data = decoded["appnews"]["newsitems"][0]
    values = [data["url"], data["feedlabel"], data["title"], htmlparser.unescape(data["contents"]), data["gid"]]
    return(values)
    

#print(grabSteamNews())