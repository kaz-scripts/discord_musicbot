import discord
from discord.ext import tasks
import yt_dlp
import asyncio
import os
import urllib.request, urllib.error
from youtubesearchpython import VideosSearch
import re
import json
from bs4 import BeautifulSoup

TOKEN = 'here'

client = discord.Client(intents=discord.Intents.all())
volume = 0.1
global y
global source
global info
global title
global loop
y = False
source = None
info = ''
title = 'None'
loop = False

async def join_voice_channel(message):
    global volume
    global y
    global source
    global info
    global title
    global loop
    global voice_client
    keyword = message.content.split(maxsplit=1)[1]

    for vc in client.voice_clients:
        if vc.guild == message.guild:
            await vc.disconnect()

    channel = message.author.voice.channel
    voice_client = await channel.connect()

    try:
        f = urllib.request.urlopen(keyword)
        f.close()
        y = False
    except:
        try:
            keyword = "https://www.youtube.com/watch?v=" + VideosSearch(keyword, limit = 1).result()['result'][0]['id']
            y = True
        except:
            try:
                keyword = "https://www.youtube.com/watch?v=" + VideosSearch(re.sub(r'[\s\W]', '', keyword), limit = 1).result()['result'][0]['id']
                y = True
            except:
                info = ''
                await message.channel.send(message.content.split(maxsplit=1)[1]+'は見つかりませんでした')
                return
    
    if y:
        ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio_cache/'+re.search(r"(?<=v=)[a-zA-Z0-9_-]+(?=&|\?|$)", keyword).group(0)+'.mp3',
        }
        f = urllib.request.urlopen("https://noembed.com/embed?url="+keyword)
        info = f.read().decode('utf8')
        f = urllib.request.urlopen(keyword)
        title = BeautifulSoup(f, "html.parser").title.string
        send_message = await message.channel.send(keyword+'\n音楽をダウンロード中')
        if not os.path.isfile('audio_cache/'+re.search(r"(?<=v=)[a-zA-Z0-9_-]+(?=&|\?|$)", keyword).group(0)+'.mp3'):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                dl_info = ydl.extract_info(keyword, download=True)
        source = discord.FFmpegPCMAudio('audio_cache/'+re.search(r"(?<=v=)[a-zA-Z0-9_-]+(?=&|\?|$)", keyword).group(0)+'.mp3')
        await send_message.edit(content=keyword+'\n再生を開始しました')
    else:
        ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio_cache/'+re.search(r'(sm\d+)', keyword).group(0)+'.mp3',
        }
        f = urllib.request.urlopen("https://noembed.com/embed?url="+keyword)
        info = f.read().decode('utf8')
        f = urllib.request.urlopen(keyword)
        title = BeautifulSoup(f, "html.parser").title.string
        send_message = await message.channel.send(keyword+'\n音楽をダウンロード中')
        if not os.path.isfile('audio_cache/'+re.search(r'(sm\d+)', keyword).group(0)+'.mp3'):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                dl_info = ydl.extract_info(keyword , download=True)
        source = discord.FFmpegPCMAudio('audio_cache/'+re.search(r'(sm\d+)', keyword).group(0)+'.mp3')
        await send_message.edit(content=keyword+'\n再生を開始しました')

    voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
    voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
    voice_client.source.volume = volume

    while voice_client.is_playing():
        await asyncio.sleep(1)
    title = 'None'

async def stop_playing(message):
    for vc in client.voice_clients:
        if vc.guild == message.guild:
            vc.stop()

@client.event
async def on_message(message):
    global info
    global volume
    global voice_client
    global loop
    if message.author == client.user:
        return

    if message.content.startswith(('p ','play ')):
        if message.author.voice:
            await join_voice_channel(message)
        else:
            return
    elif message.content.startswith(('v ','vol ','volume ')):
        volume = float(message.content.split(' ')[1]) / 100
        voice_client.source.volume = volume
        send_message = await message.channel.send('音量を'+message.content.split(' ')[1]+'%に変更しました')
        await send_message.delete(delay=15)
        await message.delete(delay=15)

    elif message.content.startswith(('s','stop')):
        await message.channel.send('再生を停止しました')
        await stop_playing(message)
    elif message.content.startswith(('i','info')):
        if not info == '':
            send_message = await message.channel.send(info)
            await send_message.delete(delay=60)
            await message.delete(delay=60)
        else:
            send_message = await message.channel.send('something went wrong lmao')
            await send_message.delete(delay=60)
            await message.delete(delay=60)
    elif message.content.startswith(('l','loop')):
        loop = not loop
        if loop:
            send_message = await message.channel.send('ループを有効にしました')
            await send_message.delete(delay=15)
            await message.delete(delay=15)
        else:
            send_message = await message.channel.send('ループを無効にしました')
            await send_message.delete(delay=15)
            await message.delete(delay=15)
    else:
        return

@tasks.loop(seconds=5)
async def change_status():
    global title
    DIR = './audio_cache'
    audio_sum = str(sum(os.path.isfile(os.path.join(DIR, name)) for name in os.listdir(DIR)))
    await client.change_presence(activity=discord.Game(name='Playing:'+title+', '+audio_sum+' Songs are Saved. MADE BY WAKKA'))

@client.event
async def on_ready():
    print('Botがログインしました')
    change_status.start()

client.run(TOKEN)