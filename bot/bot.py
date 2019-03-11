import discord
import logging
import random
import asyncio
import requests 
import json
import setproctitle
import chess
import time
import chess.pgn as pgn
import io
from discord.ext import commands


# permission int = 2048

# Renommage du processus (sera utile lors du script de màj)
setproctitle.setproctitle('synobot-python')

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


# Evaluation des fichiers
current_games_path='current_games.json'
current_games = json.load(open(current_games_path))

ended_games_path = 'ended_games.json'
ended_games   = json.load(open(ended_games_path))

challenge_list_path='proposed_challenges.json'
challenge_list = json.load(open(challenge_list_path))

chessconf_path = 'chessconf.txt'
chessconf_str  = open(chessconf_path).read()
nb_id = int(chessconf_str.strip())

# temps max avant d'accepter une partie
timeout= 3600 * 24 * 2 # deux jours

default_game_timeout = 3600 * 24 * 5 # 5 jours
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

client=discord.Client()

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
  'qst' : 'Répond à une question fermée', \
  'choose' : 'Choisit un des choix parmi une liste, où chaque élément est séparé par le caractère |' , \
}

## commande spécifiques au serveur m1
commandes_m1_desc={'duncan thom' : 'Génération de blagues du prof d\'anglais du g2', \
                   'blsk' : 'Découvrez un fait inconnu de la vie de blsk' }

#yes_answers =  ['Je pense que oui', 'Absolument', 'Très probablement', 'Oui.', 'C\'est bien parti pour']
#no_answers  = ['Peu probable', 'Faut pas rêver', 'Impossible', 'Et la marmotte elle met le chocolat dans le papier alu', 'Non.']
#idk_answers = ['Essaie plus tard', 'Je sais pas', 'Une chance sur deux', 'Retente', 'bite']
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

# contient les pgn des divers puzzle demandés
pgn_dico={}
    
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

def puzzle_solution(channel_id):
    return "La solution était : " + pgn_dico[channel_id]
    
def puzzle_chesscom(channel_id):
    global pgn_dico
    requete = 'https://api.chess.com/pub/puzzle/random'
    em = discord.Embed(title="", colour=0x009000)
    res = requests.get(requete)
    if res.status_code == 200:
        js_result = res.json()
        pgn_sale = js_result['pgn'].split(']')
        pgn_propre = pgn_sale[len(pgn_sale)-1].strip().strip('*')
        pgn_propre_traduit = pgn_propre.replace('R', 'T').replace('N', 'C').replace('B', 'F').replace('K', 'R').replace('Q', 'D')

        titre=js_result['title']
        if pgn_propre_traduit.startswith('1...'):
            titre = titre + ' (trait aux noirs)'
        else :
            titre = titre + ' (trait aux blancs)'
        em = discord.Embed(title=titre)

        img_url = js_result['image']
        pgn_dico[channel_id] = pgn_propre_traduit
        em.set_image(url = img_url)
    else :
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
    return res['value'].replace('Norris', 'Balabonski').replace('Chuck', 'Thibaut') + ' <:blsk:498584036638457857>'


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
def answer():
    return random.choice(answ)
    
### affiche message d'aide, avec les commandes spécifiques au serveur m1
def help_msg_m1():
    ret = help_msg()
    for i in commandes_m1_desc.keys():
        ret.add_field(name=i, value = commandes_m1_desc[i], inline=True)
    return ret

def choose(complet_str):
    new_str = complet_str.replace(prefix+ 'choose', '')
    return random.choice(new_str.split('|')).strip()


##################################################
# 
# Partie jeu d'échecs
# 
##################################################

# Met à jour le fichier des propositions de parties
# supprime aussi les propositions torp vieilles
def maj_challenge():
    global challenge_list
    timestamp = time.time()

    # Enlever les challenges trop vieux 
    for ident in challenge_list.keys():
        if challenge_list[ident]['timestamp'] + timeout < timestamp:
            del challenge_list[ident]
            
    f = open(challenge_list_path, "w")
    json.dump(challenge_list, f)
    f.close() 

# todo
def lose_on_time(game_id):
    global ended_games
    global current_games
    pass

def incr_nbid():
    global nb_id
    nb_id += 1
    f = open(chessconf_path, 'w')
    f.write(str(nb_id))
    f.close()
    
def maj_current():
    timestamp = time.time()
    for game_id in current_games.keys():
        if current_games[game_id]['timestamp'] + current_games[game_id]['timeout'] < timestamp :
            lose_on_time(game_id)       
    f = open(current_games_path, "w")
    json.dump(current_games, f)
    f.close()


def challenge(challenger, challenged, id_server):
    global challenge_list
    timestamp = time.time()
    id_challenge = str(nb_id)
    challenge_list[id_challenge] = dict()
    challenge_list[id_challenge]['challenged'] = challenged
    challenge_list[id_challenge]['challenger'] = challenger
    challenge_list[id_challenge]['server']     = id_server
    challenge_list[id_challenge]['timestamp']  = timestamp
    incr_nbid()
    maj_challenge()
    return id_challenge

def recv_challenge(challenger, pinged_list, serv_id = 0):
    print(len(pinged_list))
    challenged = 0 if len(pinged_list) == 0 else id(pinged_list[0])
    challenged_str = 'quelqu\'un' if challenged == 0 else pinged_list[0].mention
    game_id = challenge(challenger, challenged, serv_id)
    
    sentence = str(challenger) + ' vient de défier ' + challenged_str + ' durant une partie d\'échecs. Pour accepter, tapez !accept ' + str(game_id)
    return sentence

# - challenger correct, id correct
def accept(game_id, id_player):
    global challenge_list
    global current_games
    challenge = challenge_list[game_id]
    del challenge_list[game_id]
    maj_challenge()
    new_game = dict()
    players = [challenge['challenger'], id_player]
    random.shuffle(players)
    new_game['white'] = players[0]
    new_game['black'] = players[1]
    new_game['toPlay']= 1
    new_game['pgn'] = str(pgn.Game()) # todo : ?
    new_game['timestamp'] = time.time()
    new_game['timeout'] = default_game_timeout
    new_game['prop_draw'] = False
    current_games[game_id] = new_game
    maj_current()
    return game_id

    
# vérifier que le challenger a le droit de participer
def recv_accept(game_id, id_challenger):
    print(game_id, ', ', type(game_id))
    for i in (challenge_list.keys()):
        print(i, " / ", type(i))
    if not (game_id in challenge_list.keys()): 
        return "Identifiant de la partie non trouvé"

    challenge = challenge_list[game_id]
    if (challenge['challenged'] == 0 or challenge['challenged'] == id_challenger):
        id_ = accept(game_id, id_challenger)
        return "Challenge accepté : \n La partie " + str(id_) + ' opposant ' + \
            str(current_games[id_]['white']) + ' avec les blancs, et ' + str(current_games[id_]['black']) + ' avec les noirs peut commencer'
    else:
        return 'bite'

def fetch_game(game_id):
    game = current_games[game_id]
    pgn_string = io.StringIO(game['pgn'])
    game = pgn.read_game(pgn_string)
    return game.board()

def str_move_list(game_id):
    game = fetch_game(game_id)
    move_list = game.legal_moves
    str_list  = map((lambda x : game.san(x)), move_list)
    return str_list

def get_movelist(str_command): # TODO : vérifier que l'id donné est pas n'importe quoi
    params = str_command.split()
    if(len(params) < 2):
        return 'Identifiant de la partie pas donné'
    game_id  = params[1]
    str_list = str_move_list(game_id)
    return ", ".join(str_list)
    

#####################################################################
### <<main>>
#####################################################################

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)

@client.event
async def on_message(msg):
    global nb_id
    global current_games
    global challenge_list

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
    elif message.startswith(prefix + 'puzzle'):
        await client.send_message(msg.channel, embed= puzzle_chesscom(msg.channel.id))
    elif message.startswith(prefix + 'soluce'):
        await client.send_message(msg.channel, puzzle_solution(msg.channel.id))
    elif message.startswith(prefix + 'rouletterusse'):
        nb = random.randint(1,8)
        message_ = ''
        if nb == 1 :
            message_ = 'PAN !'
        else:
            message_ = '*clic*'
        await client.send_message(msg.channel, message_)
    elif message.startswith('!qst fils de pute'):
        await client.send_message(msg.channel, 'taggle fils d\'inceste')
    elif message.startswith(prefix + 'qst '):
        await client.send_message(msg.channel, answer())
    elif message.startswith(prefix + 'choose '):
        await client.send_message(msg.channel, choose(message))
        
    ## Commandes échecs
    elif message.startswith(prefix + 'challenge'):
        print("création du challenge ", nb_id)
        challenge_str = recv_challenge(id(msg.author), msg.mentions) # pê pas des fonctions
        await client.send_message(msg.channel, challenge_str)
    elif message.startswith(prefix + 'accept '):
        id_  = (message.split(' ')[1].strip())
        msg_ = recv_accept(id_, id(msg.author))
        await client.send_message(msg.channel, msg_)
    elif message.startswith(prefix + 'movelist'):
        answer = get_movelist(message)
        await client.send_message(msg.channel, answer)
    elif message.startswith(prefix + 'reinit_chessconfig'):
        a = open(current_games_path, 'w')
        a.write('{}')
        a.close()
        b = open(challenge_list_path, 'w')
        b.write('{}')
        b.close()
        c = open(chessconf_path, 'w')
        c.write('0')
        c.close()
        current_games = dict()
        challenge_list = dict()
        nb_id = 0
        await client.send_message(msg.channel, "fait")
    
        
client.run(oauth_discord)
