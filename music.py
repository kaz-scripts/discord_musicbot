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
import math

TOKEN = 'here'

client = discord.Client(intents=discord.Intents.all())
volume = 0.1
global y
global source
global info
global title
global loop
global stopped
y = False
source = None
info = ''
title = 'None'
loop = False
stopped = True

async def join_voice_channel(message):
    global volume
    global y
    global source
    global info
    global title
    global loop
    global voice_client
    global stopped
    keyword = message.content.split(maxsplit=1)[1]

    for vc in client.voice_clients:
        if not vc.guild == message.guild:
            await vc.disconnect()

    channel = message.author.voice.channel
    if message.guild.voice_client:
        voice_client = message.guild.voice_client
    else:
        voice_client = await channel.connect()

    send_message = await message.channel.send(message.author.mention+'\n音楽を検索中')
    await message.delete(delay=10)
    if "youtube" in keyword:
        y = True
    else:
        y = False
    try:
        f = urllib.request.urlopen(keyword)
        f.close()
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
                await send_message.edit(content=message.author.mention+'\n'+message.content.split(maxsplit=1)[1]+'は見つかりませんでした')
                return
    
    if y:
        ydl_opts = {
        'cookiefile': 'cookies.txt',
        'format': 'bestaudio+worstvideo',
        'outtmpl': 'audio_cache/'+re.search(r"(?<=v=)[a-zA-Z0-9_-]+(?=&|\?|$)", keyword).group(0),
                'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        }
        f = urllib.request.urlopen("https://noembed.com/embed?url="+keyword)
        info = f.read().decode('utf8')
        f = urllib.request.urlopen(keyword)
        title = BeautifulSoup(f, "html.parser").title.string
        await send_message.edit(content=message.author.mention+'\n'+keyword+'\n音楽をダウンロード中')
        if not os.path.isfile('audio_cache/'+re.search(r"(?<=v=)[a-zA-Z0-9_-]+(?=&|\?|$)", keyword).group(0)+'.mp3'):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                dl_info = ydl.extract_info(keyword, download=True)
        file_name = 'audio_cache/'+re.search(r"(?<=v=)[a-zA-Z0-9_-]+(?=&|\?|$)", keyword).group(0)+'.mp3'
        source = discord.FFmpegPCMAudio(file_name)
        await send_message.edit(content=message.author.mention+'\n'+keyword+'\n再生を開始しました')
    else:
        if "nico" in keyword and "sm" in keyword:
            ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio_cache/'+re.search(r'(sm\d+)', keyword).group(0)+'.mp3',
            }
            f = urllib.request.urlopen("https://noembed.com/embed?url="+keyword)
            info = f.read().decode('utf8')
            f = urllib.request.urlopen(keyword)
            title = BeautifulSoup(f, "html.parser").title.string
            await send_message.edit(content=message.author.mention+'\n'+keyword+'\n音楽をダウンロード中')
            if not os.path.isfile('audio_cache/'+re.search(r'(sm\d+)', keyword).group(0)+'.mp3'):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    dl_info = ydl.extract_info(keyword , download=True)
            file_name = 'audio_cache/'+re.search(r'(sm\d+)', keyword).group(0)+'.mp3'
            source = discord.FFmpegPCMAudio(file_name)
        else:
            try:
                file_name = 'audio_cache/'+str(hash(keyword))+'.mp3'
                await send_message.edit(content=message.author.mention+'\n'+keyword+'\n音楽をダウンロード中')
                if not os.path.isfile('audio_cache/'+str(hash(keyword))+'.mp3'):
                    ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': 'audio_cache/'+str(hash(keyword))+'.mp3',
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        dl_info = ydl.extract_info(keyword , download=True)
                    f = urllib.request.urlopen("https://noembed.com/embed?url="+keyword)
                    info = f.read().decode('utf8')
                    f = urllib.request.urlopen(keyword)
                    title = BeautifulSoup(f, "html.parser").title.string
            except Exception as e:
                print(e)
                await send_message.edit(content=message.author.mention+'\n'+keyword+'\nこのURLは対応していません')
                return
            source = discord.FFmpegPCMAudio(file_name)
        await send_message.edit(content=message.author.mention+'\n'+keyword+'\n再生を開始しました')

    if voice_client.is_playing():
        voice_client.stop()

    voice_client.play(source)
    voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
    voice_client.source.volume = volume
    while voice_client.is_playing():
        while voice_client.is_playing() or voice_client.is_paused():
            await asyncio.sleep(1)
        if loop and not stopped:
            voice_client.stop()
            source = discord.FFmpegPCMAudio(file_name)
            voice_client.play(source)
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
            voice_client.source.volume = volume
    if not loop:
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
    global stopped
    if message.author == client.user:
        return
        
    if isinstance(message.channel, discord.DMChannel):
        await message.channel.send('こんにちは！お手伝いできることがあれば教えてください。')
        
    if message.content.startswith(('pause')):
        voice_client.pause()
        send_message = await message.channel.send(message.author.mention+'\n'+'一時停止しました')
        await message.delete(delay=10)
        await send_message.delete(delay=3600)
    elif message.content.startswith(('p ','play ')):
        if message.author.voice:
            await join_voice_channel(message)
            stopped = False
        else:
            send_message = await message.channel.send(message.author.mention+'\n'+'ボイスチャンネルに参加してください')
            await message.delete(delay=10)
            await send_message.delete(delay=10)
            return
    elif message.content.startswith(('v ','vol ','volume ')):
        volume = float(message.content.split(' ')[1]) / 100
        voice_client.source.volume = volume
        send_message = await message.channel.send(message.author.mention+'\n'+'音量を'+message.content.split(' ')[1]+'%に変更しました')
        await message.delete(delay=10)
        await send_message.delete(delay=15)

    elif message.content == 's' or message.content == 'stop':
        await message.channel.send(message.author.mention+'\n'+'再生を停止しました')
        await message.delete(delay=10)
        await stop_playing(message)
        voice_client.stop()
        title = 'None'
        stopped = True
    elif message.content == 'i' or message.content == 'info':
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
            send_message = await message.channel.send(message.author.mention+'\n'+'ループを有効にしました')
            await message.delete(delay=10)
            await send_message.delete(delay=3600)
        else:
            send_message = await message.channel.send(message.author.mention+'\n'+'ループを無効にしました')
            await message.delete(delay=10)
            await send_message.delete(delay=3600)
    elif message.content.startswith(('r','resume')):
        voice_client.resume()
        send_message = await message.channel.send(message.author.mention+'\n'+'再開しました')
        await message.delete(delay=10)
        await send_message.delete(delay=30)
        stopped = False
    elif message.content.startswith(('e','end')):
        try:
            args = message.content.split()[1:]
            if (len(args) != 6):
                await message.channel.send("使用方法: end {x1} {z1} {angle1} {x2} {z2} {angle2}")
                return
            try:
                x1, z1, a1, x2, z2, a2 = map(float, args)
            except Exception as e:
                await message.channel.send(f"`Error: {e}`\n" + "使用方法: end {x1} {z1} {angle1} {x2} {z2} {angle2}")
                return

            a1 = math.radians(-a1)
            a2 = math.radians(-a2)
        
            if a1 == a2:
                await message.channel.send("2つの直線は平行です！もっと離れてください！")
                return

            m1 = math.tan(a1)
            m2 = math.tan(a2)

            b1 = x1 - m1 * z1
            b2 = x2 - m2 * z2

            y = (b2 - b1) / (m1 - m2)
            x = m1 * y + b1

            await message.channel.send(f"X座標: {x:.3f}, Z座標: {y:.3f}")
        except Exception as e:
            await message.channel.send(f"`Error: {e}`\n" + "使用方法: end {x1} {z1} {angle1} {x2} {z2} {angle2}")

@tasks.loop(seconds=60)
async def change_status():
    global title
    DIR = './audio_cache'
    audio_sum = str(sum(os.path.isfile(os.path.join(DIR, name)) for name in os.listdir(DIR)))
    #await client.change_presence(activity=discord.Game(name='Playing:'+title+', '+audio_sum+' Songs are Saved. MADE BY WAKKA'))
    await client.change_presence(activity=discord.Game(name=audio_sum+' Songs are Saved. MADE BY WAKKA'))

@client.event
async def on_ready():
    print('Botがログインしました')
    change_status.start()

client.run(TOKEN)