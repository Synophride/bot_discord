import discord
import logging
import asyncio
import requests 
import json
from discord.ext import commands

# permission int = 2048


## Evaluation du fichier de configuration
keys = dict()
fd = open('conf.txt', 'r')
lines = fd.readlines()
for line in lines:
    l = line.strip()
    # commentaires ou lignes vide
    if l == '' or l.startswith('#'):
        pass
    else:
        tab = l.split('=')
        key = tab[0]
        val = tab[1]
        keys[key] = val
fd.close()

###################################
# Initialisation des variables
###################################

oauth_discord = keys['oauth_discord']
id_serveur_m1 = keys['id_serveur_m1']
api_key_chat  = keys['api_key_chat']

# préfixe de la commande
prefix='!'

# utilisé pour les tests de commandes
test_prefix='$'

client= discord.Client()

# Traduction des variantes d'échecs
dico={ 'correspondence' : 'Correspondance', \
       'chess_daily' : 'Correspondance', \
       'chess_rapid' : 'Rapide', \
       'chess_bullet': 'Bullet', \
       'chess_blitz' : 'Blitz' ,\
       'bullet' : 'Bullet' ,\
       'puzzle': 'Tactiques', \
       'ultrabullet': 'Ultra-bullet', \
       'classical' : 'Classique' ,\
       'blitz' : 'Blitz' ,\
       'chess960' : 'Échecs 960' ,\
}

# Liste des commandes du bot +
commandes_desc = \
{ \
  'chat' : 'Envoie une photo de chat choisie aléatoirement', \
  'norris' : 'Génération de Norris facts', \
  'lichess <pseudo(s) lichess>': 'Affiche les elos des principales variantes sur lichess.org du pseudo en paramètre' , \
  'liembed' : 'même chose que lichess, mais en plus beau. A ne pas utiliser pour l\'instant', \
  'lichessall <pseudo lichess>': 'Affiche les elos de toutes les variantes jouées sur lichess.org du pseudo en paramètre', \
  'chesscom <pseudo chess.com>' : 'Affiche les elos de toutes les variantes jouées sur chess.com du pseudo en paramètre', \
  'breakingbad' : 'Affiche une citation aléatoire de Breaking Bad, ainsi que son auteur', \
  'help' : 'Affiche cette aide', \
}

## commande spécifiques au serveur m1
commandes_m1_desc={'duncan thom' : 'Génération de blagues du prof d\'anglais du g2', \
                   'blsk' : 'Découvrez un fait inconnu de la vie de blsk' }

## Traduit une variante d'échecs grâce à dico. si pas d'entrée trouvée, renvoie la chaine en paramètre
def traduction(i):
    if i in dico:
        return dico[i]
    else:
        return i
   
def status(s):
    if s :
        return 'En ligne'
    else:
        return 'Hors ligne'

##################################################################
###
###  Fonctions du bot discord
###
##################################################################

### Renvoie un embed contenant une photo de chat au hasard
def chat():
    requete = 'https://api.thecatapi.com/v1/images/search?format=json'
    header = {'x-api-key':api_key_chat, 'Content-Type':'application/json'}
    res = requests.get(requete, headers=header)
    if res.status_code == 200: 
        js = res.json()
        img = js[0]['url']
        em = discord.Embed(title = "Chat.", colour = 0xFF8000)
        em.set_image(url=img)
        return em
    else:
        print ('chat : code d\'erreur : ' + str(res.status_code))
        requete = 'https://aws.random.cat/meow'
        res = requests.get(requete)
        if res.status_code == 200:
            img = res.json()['file']
            em = discord.Embed(title = "Chat.", colour = 0xFF8000)
            em.set_image(url=img)
            return em
        else:
            em = discord.Embed(title = 'Erreur', colour = 0xFF0000)
            em.set_image(url = ('https://http.cat/' + str(res.status_code)))
            return em

### même chose que joke
def thom():
    requete = 'https://08ad1pao69.execute-api.us-east-1.amazonaws.com/dev/random_joke'
    res = requests.get(requete)
    js_result = res.json()
    setup = js_result['setup']
    punchline = js_result['punchline']
    return discord.Embed(title=setup, description=punchline)
    
### Renvoie une blague bordi au hasard
def bordi():
    requete = 'http://api.icndb.com/jokes/random?firstName=Kevin&amplast&Name=Norris'
    res = requests.get(requete).json()
    return res['value']['joke'].replace('Norris', 'Bordi')

### Renvoie une blague blsk au hasard
def blsk():
    requete ='https://api.chucknorris.io/jokes/random?category=dev'
    res = requests.get(requete).json()
    return res['value'].replace('Norris', 'Balabonski').replace('Chuck', 'Thibault') + ' <:blsk:498584036638457857>'


### Renvoie une blague chuck norris au hasard
def norris():
    requete = 'http://api.icndb.com/jokes/random?firstName=Chuck&amplast&Name=Norris'
    res = requests.get(requete).json()
    return res['value']['joke'].replace('&quot;', '"')

### Affiche l'elo + le nombre de parties de l'utilisateur en paramètre, en classique à bullet + tactiques
def lichess(username):
    requete = 'https://lichess.org/api/user/' + username
    res = requests.get(requete)
    message_retour = ''
    if res.status_code != 200:
        message_retour = 'Erreur : a priori, utilisateur inexistant. Code =' + str(res.status_code) + ')'
    else: # Classique, Bullet, Blitz, Rapide
        json_data = res.json()
        message_retour = '**__' + json_data['username'] + ':__ ** (' + status(json_data['online']) + ')\n'        
        if not ('perfs' in json_data):
            return 'Pas de données sur l\'historique de parties\n'
        else:
            parties = json_data['perfs']
            # Classical
            if 'classical' in parties:
                message_retour = message_retour + '\t**Classique :**' + str(parties['classical']['rating']) + ', ' +  str(parties['classical']['games']) + ' parties \n'
            # Rapid
            if 'rapid' in parties:
                message_retour = message_retour + '\t**Rapide :**' + str(parties['rapid']['rating']) + ', ' +  str(parties['rapid']['games']) + ' parties \n'
            # Blitz
            if 'blitz' in parties:
                message_retour = message_retour + '\t**Blitz :**' + str(parties['blitz']['rating']) + ', ' +  str(parties['blitz']['games']) + ' parties \n'
            # Bullet
            if 'bullet' in parties:
                message_retour = message_retour + '\t**Bullet :**' + str(parties['bullet']['rating']) + ', ' +  str(parties['bullet']['games']) + ' parties \n'
            # Tactiques
            if 'puzzle' in parties:
                message_retour = message_retour + '\t**Tactiques :**' + str(parties['puzzle']['rating']) + ', ' +  str(parties['puzzle']['games']) + ' \n'
    return message_retour


### Affiche l'elo + nombre de parties de l'utilisateur en param dans toutes les variantes sur lichess
def lichesselo(usrname):
    requete = 'https://lichess.org/api/user/' + usrname
    res = requests.get(requete)
    message_retour = ''
    if res.status_code != 200 : 
        message_retour = 'erreur (a priori, mauvais utilisateur. Code de requête = ' + str(res.status_code) + ')'
    else:
        json_res = res.json()
        message_retour = '**' + json_res['username'] + '**'
        if not('perfs' in json_res) :
             return message_retour + "Elo non trouvé"
        for i in json_res['perfs'].keys():
            message_retour = message_retour + '\n ** '+ traduction(i) + ':** ' + str(json_res['perfs'][i]['rating']) + ' elo,  ' + str(json_res['perfs'][i]['games']) + ' parties'
    return message_retour


### Affiche elo du pseudo en param sur chesscom 
def chesscomelo(usrname):
    requete = 'https://api.chess.com/pub/player/' + usrname + '/stats'
    resultat = requests.get(requete)
    message_retour = '__**'+ usrname +':**__'
    if resultat.status_code != 200 : 
        message_retour = 'erreur (a priori, utilisateur inexistant. Code rendu = ' + str(resultat.status_code) + ')'
    else:
        res = resultat.json()
        for i in res.keys():
            elo = str(res[i]['last']['rating'])
            nwin= res[i]['record']['win']
            ndraw= res[i]['record']['draw']
            nlose= res[i]['record']['loss']
            ngames=nwin + ndraw + nlose
        message_retour = message_retour + '\n  **' + traduction(i) + ':** ' + elo + ' elo , ' + str(ngames) + ' parties (' + str(nwin) + '-' + str(ndraw) + '-' + str(nlose) + ')'
    return message_retour

### Renvoie un embed contenant une citation de Breaking Bad
def bbad():
    requete = 'https://breaking-bad-quotes.herokuapp.com/v1/quotes/'
    res  = requests.get(requete)
    quote_arr = res.json()
    txt  = quote_arr[0]['quote']
    auth = quote_arr[0]['author']
    embed= discord.Embed(title = txt, description=auth, colour=0xFFF000)
    return embed
    

### Renvoie l'elo lichess dans un embed. Buggué jusqu'à que j'aie plus la flemme 
def embedded_lichess(usrname):
    requete = 'https://lichess.org/api/user/' + usrname
    res = requests.get(requete)
    
    ### TODO : Vérification que la requête est légale
    json_res = res.json()
    parties = json_res['perfs']
    embed = discord.Embed(title = usrname + ' stats on Lichess', description = '', colour=0xFF0000)
    if 'classical' in parties:
        embed.add_field(name='Classique', \
                        value=(str(parties['classical']['rating']) + ', ' +  str(parties['classical']['games']) + ' parties'), \
        inline=False)
    if 'rapid' in parties:
        embed.add_field(name='Rapide', \
                        value=str(parties['rapid']['rating']) + ', ' +  str(parties['rapid']['games']) + ' parties', \
        inline=False)
    if 'blitz' in parties:
        embed.add_field(name='Blitz', \
                        value=str(parties['blitz']['rating']) + ', ' +  str(parties['blitz']['games']) + ' parties', \
        inline=False)
    if 'bullet' in parties:
        embed.add_field(name='Bullet', \
                        value=str(parties['bullet']['rating']) + ', ' +  str(parties['bullet']['games']) + ' parties', \
        inline=False)
    if 'puzzle' in parties:
        embed.add_field(name='Tactiques', \
                        value=str(parties['puzzle']['rating']) + ', ' +  str(parties['puzzle']['games']) + ' parties', \
        inline=False)
    return embed

## retourne un message "embed" basique. Pour l'exemple
def mk_embed():
    em = discord.Embed(title='My Embed Title', description='My Embed Content.', colour=0xFF0000)
    em.set_author(name='Someone', icon_url=client.user.default_avatar_url)
    return em

### affiche message d'aide
def help_msg():
        ret = discord.Embed(title='Synobot', description='Utilisation : <' + prefix + '[commande] (paramètres)>'  )
        for i in commandes_desc.keys() :
            ret.add_field(name=i, value=commandes_desc[i], inline=True)
        return ret

### affiche message d'aide, avec les commandes spécifiques au serveur m1
def help_msg_m1():
    ret = help_msg()
    for i in commandes_m1_desc.keys():
        ret.add_field(name=i, value = commandes_m1_desc[i], inline=True)
    return ret



#####################################################################
### <<main>>
#####################################################################

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)

@client.event
async def on_message(msg):
    message = msg.content
    msg_ret = ':\n'   
    ## commandes spécifiques au serveur m1
    id_s = msg.server.id
    if id_s == id_serveur_m1:
        if message.startswith(prefix + 'duncan thom'):
            await client.send_message(msg.channel, embed=thom())
            return
        elif message.startswith(prefix + 'blsk'):
            await client.send_message(msg.channel, blsk())
            return
        elif message.startswith(prefix+'help'):
            await client.send_message(msg.channel, embed=help_msg_m1())
            return
    elif message.startswith(prefix + 'help'):
        await client.send_message(msg.channel, embed=help_msg())
        
    if message.startswith(prefix + "lichessall"):
        arglist = message.split(' ')
        for i in range(1, len(arglist)):
            msg_ret = msg_ret + lichesselo(arglist[i]) + '\n\n'
        await client.send_message(msg.channel, msg_ret)
    elif message.startswith(prefix + "lichess"):
        arglist = message.split(' ')
        for i in range(1, len(arglist)):
            msg_ret = msg_ret + lichess(arglist[i]) + '\n\n'
        await client.send_message(msg.channel, msg_ret)
    elif message.startswith(prefix + 'chesscom'):
        arglist = message.split(' ')
        for i in range(1, len(arglist)):
            msg_ret = msg_ret + chesscomelo(arglist[i]) + '\n\n'
        await client.send_message(msg.channel, msg_ret)
    elif message.startswith(prefix + 'helpsyno'):
        await client.send_message(msg.channel, help_msg())
    elif message.startswith(prefix + 'test'):
        await client.send_message(msg.channel, 'test')
    elif message.startswith(prefix + 'embed'):
        await client.send_message(msg.channel, embed=mk_embed())        
    elif message.startswith(prefix + 'liembed'):
        arglist = message.split(' ')
        for i in range(1, len(arglist)):
            await client.send_message(msg.channel, embed=embedded_lichess(arglist[i]))
    elif message.startswith(prefix + 'breakingbad'):
        await client.send_message(msg.channel, embed=bbad())
    elif message.startswith(prefix + 'norris'):
        await client.send_message(msg.channel, norris())
    elif message.startswith(prefix + 'bordi'):
        await client.send_message(msg.channel, bordi())
    elif message.startswith(prefix + 'chat'):
        await client.send_message(msg.channel, embed = chat())
    elif message.startswith(prefix + 'joke'):
        await client.send_message(msg.channel, embed=thom())
    elif message.startswith(prefix + 'status'):
        await client.send_message(msg.channel, 'En ligne')
        
client.run(oauth_discord)
