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
import datetime
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
    
### Renvoie l'elo lichess dans un embed. 
def embedded_lichess(usrname):
    requete = 'https://lichess.org/api/user/' + usrname
    res = requests.get(requete)
    if res.status_code != 200:
        em = discord.Embed(title = 'Erreur', colour = 0xFF0000)
        em.set_image(url = ('https://http.cat/' + str(res.status_code)))
        return em

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
# supprime aussi les propositions trop vieilles (proposé il y a plus de <timeout> secondes)
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

# incrémente nb_id, et le met à jour dans le fichier de configuration
def incr_nbid():
    global nb_id
    nb_id += 1
    f = open(chessconf_path, 'w')
    f.write(str(nb_id))
    f.close()

def maj_ended():
    f = open(ended_games_path, 'w')
    json.dump(ended_games, f)
    f.close()

# Met à jour la liste des parties courantes dans le fichier respectif
def maj_current():
    timestamp = time.time()
#    for game_id in current_games.keys():
#       if current_games[game_id]['timestamp'] + current_games[game_id]['timeout'] < timestamp :
#           lose_on_time(game_id)       
    f = open(current_games_path, "w")
    json.dump(current_games, f)
    f.close()

# Fonction crééant un challenge/une proposition de partie
def challenge(challenger, challenged, id_server):
    global challenge_list
    timestamp = time.time()
    id_challenge = str(nb_id)
    challenge_list[id_challenge] = dict()
    challenge_list[id_challenge]['str_challenger'] = challenger.name
    challenge_list[id_challenge]['challenged'] = challenged
    challenge_list[id_challenge]['challenger'] = id(challenger)
    challenge_list[id_challenge]['server']     = id_server
    challenge_list[id_challenge]['timestamp']  = timestamp
    incr_nbid()
    maj_challenge()
    return id_challenge

# Fonction appellée lors de la proposition d'un challenge via la commande !challenge
# deux cas : 
#  - la personne a spécifié quelqu'un en particulier dans son message = Seule cette personne peut accepter
#  - La personne a spécifié personne : Tout le monde peut accepter
# Todo : prendre en compte here/everyone
def recv_challenge(challenger, pinged_list, serv_id = 0):
    challenged = 0 if len(pinged_list) == 0 else id(pinged_list[0]) 
    challenged_str = 'quelqu\'un' if challenged == 0 else pinged_list[0].mention
    game_id = challenge(challenger, challenged, serv_id)
    sentence = challenger.name + ' vient de défier ' + challenged_str + ' durant une partie d\'échecs. Pour accepter, tapez !accept ' + str(game_id)
    return sentence

# - challenger correct, id correct
def accept(game_id, id_player, str_j2):
    global challenge_list
    global current_games

    # mise à jour des challenge : Suppression des vieux challenges
    challenge = challenge_list[game_id]
    del challenge_list[game_id]
    maj_challenge()

    str_white = challenge['str_challenger']
    str_black = str_j2
    
    id_white = challenge['challenger']
    id_black = id_player

    # une chance sur deux d'inverser les rôles
    if(random.random() > 0.5):
        str_ = str_white
        str_white = str_black
        str_black = str_

        id_ = id_white
        id_white = id_black
        id_black = id_

    game = pgn.Game()

    new_game = dict()
    new_game['white'] = id_white
    new_game['black'] = id_black
    new_game["white_str"] = str_white
    new_game["black_str"] = str_black
    new_game['toPlay']= 1
    new_game['pgn'] = str(game)
    new_game['timestamp'] = time.time()
    new_game['timeout'] = default_game_timeout
    new_game['prop_draw'] = False
    current_games[game_id] = new_game
    maj_current()
    return (str_white, str_black)

    
def recv_accept(game_id, challenger):
    if not (game_id in challenge_list.keys()): 
        return "Identifiant de la partie non trouvé"

    challenge = challenge_list[game_id]    
    id_challenger = id(challenger)
    str_challenger= challenger.name
    
    if (challenge['challenged'] == 0 or challenge['challenged'] == id_challenger):
        (str_white, str_black) = accept(game_id, id_challenger, str_challenger)

        return "Challenge accepté : \n La partie " + str(game_id) + ' opposant ' + \
            str_white + ' avec les blancs, et ' + str_black + ' avec les noirs peut commencer'
    else:
        return 'Mauvais challenger : toi pas concerné par ce défi'

# id_partie -> plateau de la partie
def fetch_game(game_id):
    game = current_games[game_id]
    pgn_string = io.StringIO(game['pgn'])
    game = pgn.read_game(pgn_string)
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    return board

# Donne la liste des coups, sous notation algébrique classique
def str_move_list(game_id):    
    game = fetch_game(game_id) 
    move_list = game.legal_moves
    str_list  = map((lambda x : game.san(x)), move_list)
    return str_list

# Fonction appelée lors de l'appel à la commande !movelist
def get_movelist(str_command):
    params = str_command.split()
    if(len(params) < 2):
        return 'Identifiant de la partie pas donné'
    game_id  = params[1]
    
    if not game_id in current_games.keys():
        return "La partie donnée en param n'existe pas"

    str_list = str_move_list(game_id)
    return ", ".join(str_list)

            
# rend un embed
def show_board(commande):
    em = discord.Embed(title = 'board img')
    params = commande.split()
    if len(params) < 2:
        em.add_field(name='erreur', value='Pas d\'id de partie spécifié')
        return em
    game_id = params[1]
    if not game_id in current_games.keys():
        em.add_field(name="erreur", value='id de partie incorrect')
        return em
    game = fetch_game(game_id)
    fen = game.fen()
    clean_fen = fen.split()[0].strip()
    # todo : p-^e ajouter des effets graphiques (dernier coup, échec, option pour afficher du pdv des noirs...)
    addr="https://backscattering.de/web-boardimage/board.png?fen=" + clean_fen
    em.set_image(url=addr)
    return em

def end_game(board, game_id, pgngame):
    global current_games
    global ended_games
    if board.is_game_over():
        # mise à jour
        res = board.result()
        new_pgn_game = pgngame.from_board(board)
        new_pgn_game.headers['Result'] = res
        game = current_games[game_id]
        sentence = "Fin de la partie: " + game["white_str"] + ' ' + res + ' ' + \
                game["black_str"]
        
        del current_games[game_id]

        finished_game = dict()
        finished_game["white"] = game["white"]
        finished_game["black"] = game["black"]
        finished_game['res']   = res
        finished_game['pgn']   = game['pgn']

        ended_games[game_id] = finished_game
        maj_ended()
        maj_current()
        return sentence
    else:
        return None
    
def play(message, id_messager):
    global current_games
    parts = message.split(' ')
    if len(parts) <  3:
        return 'message pas correct'
    
    # Tovérifier : seul le bon joueur peut jouer
    game_id = parts[1]
    move = parts[2]
    game = current_games[game_id]   
    pgn_stringIO = io.StringIO(game['pgn'])
    pgn_game = pgn.read_game(pgn_stringIO)
    board = pgn_game.board()
    for m in pgn_game.mainline_moves():
        board.push(m)

    id_player_to_move = game["white"]
    if board.turn == chess.WHITE:
        id_player_to_move = game["black"]
    if(id_messager != id_player_to_move):
        return "Pas le bon joueur qui joue"
    try:
        move_played = board.push_san(move)
        new_pgn_game = pgn_game.from_board(board)
        new_pgn = new_pgn_game.accept(pgn.StringExporter(headers=True))
        current_games[game_id]['pgn'] = new_pgn
        s = end_game(board, game_id, pgn_game)
        if (s != None):
            return s
        
        maj_current()
        return "le coup semble avoir été joué"
    except ValueError:
        return ("Coup invalide : <" + move + ">. !movelist pour avoir la liste des coups")


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
        challenge_str = recv_challenge(msg.author, msg.mentions) # pê pas des fonctions
        await client.send_message(msg.channel, challenge_str)
    elif message.startswith(prefix + 'accept '):
        id_  = (message.split(' ')[1].strip())
        msg_ = recv_accept(id_, msg.author)
        await client.send_message(msg.channel, msg_)
    elif message.startswith(prefix + 'movelist'):
        answer = get_movelist(message)
        await client.send_message(msg.channel, answer)
    elif message.startswith(prefix + 'showboard'):
        em = show_board(message)
        await client.send_message(msg.channel, embed=em)
    elif message.startswith(prefix + 'move '):
        m=play(message, id(msg.author))
        await client.send_message(msg.channel, m)
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
    elif message.startswith(prefix + 'getid'):
        await client.send_message(msg.channel, id(msg.author))
        
client.run(oauth_discord)
