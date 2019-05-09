import discord
import random
import requests
import json
import asyncio

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

async def qst(msg, client):
    await client.send_message(msg.channel, random.choice(answ))
    
async def status(msg, client):
    chan = msg.channel
    s = msg.content
    if s :
        await client.send_message(chan, 'En ligne')
    else:
        await client.send_message(chan, 'Hors ligne')
        
async def codeblock(msg, client):
    str_to_write = msg.content.split(' ', 1)[1] 
    await client.send_message(msg.channel, "```\n" + string_to_write + "```")

### Renvoie un embed contenant une photo de chat au hasard
async def chat(msg, client):
    requete = 'https://api.thecatapi.com/v1/images/search?format=json'
    header = {'x-api-key':api_key_chat, 'Content-Type':'application/json'}
    res = requests.get(requete, headers=header)
    if res.status_code == 200: 
        js = res.json()
        img = js[0]['url']
        em = discord.Embed(title = "Chat.", colour = 0xFF8000)
        em.set_image(url=img)
        await client.send_message(msg.channel, embed = em)
    else:
        print ('chat : code d\'erreur : ' + str(res.status_code))
        requete = 'https://aws.random.cat/meow'
        res = requests.get(requete)
        if res.status_code == 200:
            img = res.json()['file']
            em = discord.Embed(title = "Chat.", colour = 0xFF8000)
            em.set_image(url=img)
            await client.send_message(msg.channel, embed = em)
        else:
            em = discord.Embed(title = 'Erreur', colour = 0xFF0000)
            em.set_image(url = ('https://http.cat/' + str(res.status_code)))
            await client.send_message(msg.channel, embed = em)

    
### même chose que joke
async def thom(msg, client):
    requete = 'https://08ad1pao69.execute-api.us-east-1.amazonaws.com/dev/random_joke'
    res = requests.get(requete)
    js_result = res.json()
    setup = js_result['setup']
    punchline = js_result['punchline']
    em = discord.Embed(title=setup, description=punchline)
    await client.send_message(msg.channel, embed = em)



### Renvoie une blague chuck norris au hasard
async def norris(msg, client):
    requete = 'http://api.icndb.com/jokes/random?firstName=Chuck&amplast&Name=Norris'
    res = requests.get(requete).json()
    str_sent= res['value']['joke'].replace('&quot;', '"')
    await client.send_message(msg.channel, str_sent)


### Renvoie une blague bordi au hasard
async def bordi(msg, client):
    requete = 'http://api.icndb.com/jokes/random?firstName=Kevin&amplast&Name=Norris'
    res = requests.get(requete).json()
    await client.send_message(msg.channel, res['value']['joke'].replace('Norris', 'Bordi'))

### Renvoie une blague blsk au hasard
### TODO : vérification du serveur
async def blsk(msg, client):
    requete ='https://api.chucknorris.io/jokes/random?category=dev'
    res = requests.get(requete).json()
    phrase = res['value'].replace('Norris', 'Balabonski').replace('Chuck', 'Thibaut') + ' <:blsk:498584036638457857>'
    await client.send_message(msg.channel)

### Renvoie un embed contenant une citation de Breaking Bad
async def bbad(msg, client):
    requete = 'https://breaking-bad-quotes.herokuapp.com/v1/quotes/'
    res  = requests.get(requete)
    quote_arr = res.json()
    txt  = quote_arr[0]['quote']
    auth = quote_arr[0]['author']
    embed= discord.Embed(title = txt, description=auth, colour=0xFFF000)
    await client.send_message(msg.channel, embed = embed)



async def choose(msg, client):
    choices = msg.content.split(' ', 1)[1].split('|')
    choix = random.choice(choices)
    await client.send_message(msg.channel, choix)
