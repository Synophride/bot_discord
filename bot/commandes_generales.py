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


def arg_parsing(content):
    kword_list = content.split(' ')[1:]
    for ind in range(len(kword_list)):
        if not kword_list.startswith('-'):
            continue
        opt_name = 0

        pass 
    
async def train_problems(msg):
    embed_retour = discord.Embed(title = 'Je sais pas quoi mettre en titre')
    # parsing des arguments : à faire plus tard. 
    arg_l = msg.content.split(' ')
    train_type = None
    train_list = None

    requete = 'https://api-ratp.pierre-grimaud.fr/v3/traffic'
    res = requests.get(requete)
    
    if res.status_code == 200:
        donnees = res.json()
        problemes = donnees['result']
        for train_type in problemes.keys():
            for dct_ligne in problemes[train_type]:
                id_ligne = dct_ligne['line']
                if( dct_ligne['slug'] != 'normal' ):
                    resume = dct_ligne['title'] + ': ' + dct_ligne['message']
                    str_ligne = train_type[:-1] + ' ' + id_ligne
                    embed_retour.add_field(name = str_ligne, value = resume)
        if(len(embed_retour.fields) == 0):
            embed_retour.add_field(name = 'BUG', value = "Aucun problème de trains n'a été trouvé. Cela est très probablement dû à un bug")
        await msg.channel.send(embed = embed_retour)
    else:
        await msg.channel.send("Erreur lors de la requête")    
