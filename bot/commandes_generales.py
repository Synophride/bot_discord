import discord
import random
import requests
import json
import asyncio

api_key_chat = None

def init(keys):
    global api_key_chat
    api_key_chat = keys['api_key_chat']
    
# Réponses possibles à la commande qst
answ = ['Je pense que oui',
        'Absolument',
        'Très probablement',
        'Oui.',
        'C\'est bien parti pour',
        'Peu probable',
        'Faut pas rêver',
        'Impossible',
        'Et la marmotte elle met le chocolat dans le papier alu',
        'Non.',
        'Essaie plus tard',
        'Je sais pas',
        'Une chance sur deux',
        'Retente',
        'bite',
        'Et mon cul c\'est du poulet ?']

async def qst(msg):
    await msg.channel.send( random.choice(answ))
    
async def status(msg):
    chan = msg.channel
    s = msg.content
    if s :
        await msg.channel.send('En ligne')
    else :
        await msg.channel.send('Hors ligne')
        
async def codeblock(msg):
    str_to_write = msg.content.split(' ', 1)[1] 
    await msg.channel.send( "```\n" + str_to_write + "```")

### Renvoie un embed contenant une photo de chat au hasard
async def chat(msg):
    requete = 'https://api.thecatapi.com/v1/images/search?format=json'
    header = {'x-api-key':api_key_chat, 'Content-Type':'application/json'}
    res = requests.get(requete, headers=header)
    if res.status_code == 200: 
        js = res.json()
        img = js[0]['url']
        em = discord.Embed(title = "Chat.", colour = 0xFF8000)
        em.set_image(url=img)
        await msg.channel.send( embed = em)
    else:
        print ('chat : code d\'erreur : ' + str(res.status_code))
        requete = 'https://aws.random.cat/meow'
        res = requests.get(requete)
        if res.status_code == 200:
            img = res.json()['file']
            em = discord.Embed(title = "Chat.", colour = 0xFF8000)
            em.set_image(url=img)
            await msg.channel.send( embed = em)
        else:
            em = discord.Embed(title = 'Erreur', colour = 0xFF0000)
            em.set_image(url = ('https://http.cat/' + str(res.status_code)))
            await msg.channel.send( embed = em)

    
### même chose que joke
async def thom(msg):
    requete = 'https://08ad1pao69.execute-api.us-east-1.amazonaws.com/dev/random_joke'
    res = requests.get(requete)
    js_result = res.json()
    setup = js_result['setup']
    punchline = js_result['punchline']
    em = discord.Embed(title=setup, description=punchline)
    await msg.channel.send( embed = em)



### Renvoie une blague chuck norris au hasard
async def norris(msg):
    requete = 'http://api.icndb.com/jokes/random?firstName=Chuck&amplast&Name=Norris'
    res = requests.get(requete).json()
    str_sent= res['value']['joke'].replace('&quot;', '"')
    await msg.channel.send( str_sent)


### Renvoie une blague bordi au hasard
async def bordi(msg):
    requete = 'http://api.icndb.com/jokes/random?firstName=Kevin&amplast&Name=Norris'
    res = requests.get(requete).json()
    await msg.channel.send( res['value']['joke'].replace('Norris', 'Bordi'))

### Renvoie un embed contenant une citation de Breaking Bad
async def bbad(msg):
    requete = 'https://breaking-bad-quotes.herokuapp.com/v1/quotes/'
    res  = requests.get(requete)
    quote_arr = res.json()
    txt  = quote_arr[0]['quote']
    auth = quote_arr[0]['author']
    embed= discord.Embed(title = txt, description=auth, colour=0xFFF000)
    await msg.channel.send( embed = embed)



async def choose(msg):
    choices = msg.content.split(' ', 1)[1].split('|')
    choix = random.choice(choices)
    await msg.channel.send(choix)
