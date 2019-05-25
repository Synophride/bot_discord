import io
import discord
import asyncio
import logging
import requests
import random
import chess
from ast import literal_eval as make_tuple
import chess.pgn as pgn
import psycopg2

log_path = './echecs.log'
def write_log(message):
    fd = open(log_path, 'a')
    fd.write(message + '\n')
    fd.close()

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

password = None

def init(keys):
    global password
    password=keys['password']


def status(b):
    if b:
        return "En ligne"
    else:
        return "Hors ligne"

params_db = {'dbname' : 'synobot_db', 'user' : "synobot", 'password' : password}

# contient les pgn des divers puzzle demandés
pgn_dico={}

# Traduit une variante d'échecs grâce à dico. si pas d'entrée trouvée, renvoie la chaine en paramètre
def traduction(i):
    if i in dico:
        return dico[i]
    else:
        return i

async def puzzle_solution(msg):
    channel_id = (msg.channel.id)
    await msg.channel.send( "La solution était : " + pgn_dico[channel_id] )

# TODO : mettre à jour 
async def puzzle_chesscom(msg):
    global pgn_dico
    channel_id = msg.channel.id
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
        print("url image\t", img_url)
        pgn_dico[channel_id] = pgn_propre_traduit
        em.set_image(url = img_url)
    else :
        em = discord.Embed(title = 'Erreur', colour = 0xFF0000)
        em.set_image(url = ('https://http.cat/' + str(res.status_code)))
    await msg.channel.send(embed = em)

### Affiche l'elo + le nombre de parties de l'utilisateur en paramètre, en classique à bullet + tactiques
async def lichess(msg):
    username = msg.content.split(' ')[1]
    requete = 'https://lichess.org/api/user/' + username
    res = requests.get(requete)
    message_retour = ''
    if res.status_code != 200:
        message_retour = 'Erreur : a priori, utilisateur inexistant. Code =' + str(res.status_code) + ')'
        await msg.channel.send(message_retour)
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
    await msg.channel.send(message_retour)

### Affiche elo du pseudo en param sur chesscom 
async def chesscomelo(msg):
    usrname = msg.content.split(' ', 1)[1]
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
    await msg.channel.send(message_retour)

### Renvoie l'elo lichess dans un embed. 
async def embedded_lichess(msg):
    usrname = msg.content.split(' ')[1]
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
    await msg.channel.send(embed = embed)

####################
### Partie d'échecs
####################

# Met à jour le fichier des propositions de parties
# supprime aussi les propositions trop vieilles (proposé il y a plus de <timeout> secondes)
async def maj_challenge():
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
async def incr_nbid():
    global nb_id
    nb_id += 1
    f = open(chessconf_path, 'w')
    f.write(str(nb_id))
    f.close()

async def maj_ended():
    f = open(ended_games_path, 'w')
    json.dump(ended_games, f)
    f.close()

    
# Met à jour la liste des parties courantes dans le fichier respectif
async def maj_current():
    timestamp = time.time()
#    for game_id in current_games.keys():
#       if current_games[game_id]['timestamp'] + current_games[game_id]['timeout'] < timestamp :
#           lose_on_time(game_id)       
    f = open(current_games_path, "w")
    json.dump(current_games, f)
    f.close()


    
# Fonction crééant un challenge/une proposition de partie
async def challenge(challenger, challenged, id_server):
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
async def recv_challenge(challenger, pinged_list, serv_id = 0):
    challenged = 0 if len(pinged_list) == 0 else id(pinged_list[0]) 
    challenged_str = 'quelqu\'un' if challenged == 0 else pinged_list[0].mention
    game_id = challenge(challenger, challenged, serv_id)
    sentence = challenger.name + ' vient de défier ' + challenged_str + ' durant une partie d\'échecs. Pour accepter, tapez !accept ' + str(game_id)
    return sentence

# - challenger correct, id correct
async def accept(game_id, id_player, str_j2):
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

    
async def recv_accept(game_id, challenger):
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
async def fetch_game(game_id):
    game = current_games[game_id]
    pgn_string = io.StringIO(game['pgn'])
    game = pgn.read_game(pgn_string)
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    return board

# Donne la liste des coups, sous notation algébrique classique
async def str_move_list(game_id):    
    game = fetch_game(game_id) 
    move_list = game.legal_moves
    str_list  = map((lambda x : game.san(x)), move_list)
    return str_list

# Fonction appelée lors de l'appel à la commande !movelist
async def get_movelist(str_command):
    params = str_command.split()
    if(len(params) < 2):
        return 'Identifiant de la partie pas donné'
    game_id  = params[1]
    
    if not game_id in current_games.keys():
        return "La partie donnée en param n'existe pas"

    str_list = str_move_list(game_id)
    return ", ".join(str_list)
            
# rend un embed
async def show_board(commande):
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

async def end_game(board, game_id, pgngame):
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
    
async def play(message, id_messager):
    global current_games
    parts = message.split(' ')
    if len(parts) <  3:
        return 'message pas correct'
    
    game_id = parts[1]
    move = parts[2]
    game = current_games[game_id]   
    pgn_stringIO = io.StringIO(game['pgn'])
    pgn_game = pgn.read_game(pgn_stringIO)
    board = pgn_game.board()
    for m in pgn_game.mainline_moves():
        board.push(m)

    id_player_to_move = game["white"]
    if board.turn == chess.BLACK:
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

##########################################
## Parties d'échecs avec base de données #
##########################################


async def challenge_bd(msg):
    id_j1 = "'" + msg.author.id +"'"
    id_j2 = "''"
    mention = False
    if(len(msg.mentions) == 1):
        mention = true
        id_j2 = msg.mentions[0].id
    elif len(msg.mentions) > 1:
        await msg.channel.send("Impossible, pour l'instant, de ping plusieurs joueurs en même temps")
    requete = "INSERT INTO challenges (id_j1, id_j2) VALUES ({0}, {1});".format(id_j1, id_j2)
    # Manipulation de la BD
    #    conn_desc = psycopg2.connect(**params_db)
    conn_desc = psycopg2.connect(dbname = 'synobot_db', user = 'synobot', password = password)
    curseur = conn_desc.cursor()
    curseur.execute(requete)
    curseur.execute("SELECT currval('seq_challenge');")
    currval = curseur.fetchone()
    conn_desc.commit()
    curseur.close()
    conn_desc.close()
    str_j1 = str(msg.author)
    str_j2 = "quelqu'un"
    if len(msg.mentions)>0:
        str_j2 = str(msg.mentions[0])
    msg_ = "Le joueur {0} a défié {1} pour une partie d'échecs. Tapez <préfixe du serveur>accept {2} pour accepter et commencer la partie"
    msg_retour = msg_.format(str_j1, str_j2, currval)
    
    await msg.channel.send(msg_retour)


async def acceptation_bd(msg):
    id_acceptant = msg.author.id
    contents = msg.content.split(' ')
    if(len(contents) ==1):
        await msg.channel.send("Erreur : L'identifiant de la partie n'a pas été donné")
        return
    id_partie_acceptee = 0
    try:
        id_partie_acceptee = int(contents[1])
    except ValueError:
        msg_retour = "Erreur : la chaîne {0} n'est pas un identifiant de partie valide"
        await msg.channel.send(msg_retour.format(contents[1]))
        return

    # Manipulation de la BD
    cdesc = psycopg2.connect(**params_db)

    curs = cdesc.cursor()
    
    # chercher dans challenge la partie avec l'identifiant donné + vérifier que l'id acceptant est acceptable
    modele_req = "SELECT (id_j1, id_j2, id_challenge) FROM challenges WHERE (id_j2='{0}' OR id_j2 = '') AND id_challenge = {1};"
    req = modele_req.format(id_acceptant, str(id_partie_acceptee))

    curs.execute(req)
    res_tuple = curs.fetchone()
    if(res_tuple == None):
        await msg.channel.send("Identifiant de la partie non trouvé")
        return
    
    (idj1, idj2, idpartie) = make_tuple(res_tuple[0])

    print("id_j1", idj1)
    print("id_j2", idj2)
    print("idpartie", idpartie)
    print()
    print()
    id_white = idj1
    id_black = idj2
    if(random.random() < 0.5):
        id_white = idj2
        id_black = idj2

    pgn_game = pgn.Game()

    requete_deletion_challenge = "DELETE FROM challenges WHERE id_challenge = {0};"
    requete_ajout_games = "INSERT INTO games (pgn, id_blanc, id_noir, id_partie) VALUES ('{0}', '{1}', '{2}', {3});"

    requete_del = requete_deletion_challenge.format(idpartie)
    requete_ajout = requete_ajout_games.format(pgn_game, id_white, id_black, idpartie)

    curs.execute(requete_del)
    curs.execute(requete_ajout)

    cdesc.commit()
    
    curs.close()
    cdesc.close()

    message_retour = "La partie opposant {0} avec les blancs, et {1} avec les noirs peut commencer" 
    await msg.channel.send(message_retour.format(id_white, id_black))


## TODO : ajouter l'id dans la table archive
## Renommer la table
async def fin_de_partie_bd(msg, result, pgn, game_id, id_blanc, id_noir, cursor):

    requete_remove = "DELETE FROM games WHERE id_partie = {0};"
    req1 = requete_remove.format(game_id)

    requete_add = "INSERT INTO archive (pgn, resultat, id_j1, id_j2) VALUES ({0},{1},{2},{3});"
    req2 = requete_add.format(pgn, result, id_blanc, id_noir)

    cursor.execute(req1)
    cursor.execute(req2)

    msg_retour = "Fin de la partie. résultat : {0} {1} {2}" 
    await msg.channel.send(msg_retour.format(id_blanc, result, id_noir))


async def move_bd(msg):
    parts = msg.content.split(' ')
    if(len(parts) != 3):
        await msg.channel.send("Erreur dans la lecture des données : mauvais nombre d'arguments")
        return
    game_id = 0
    
    try:
        game_id = int(parts[1])
    except ValueError:
        await msg.channel.send("Erreur : Le second argument n'est pas un identifiant valide")
        return
    move = parts[2]
    
    cdesc = psycopg2.connect(**params_db)
    curs = cdesc.cursor()
    requete_modele = "SELECT pgn, id_blanc, id_noir, joueur_jouant FROM games WHERE id_partie = {0};"
    req = requete_modele.format(str(game_id))

    curs.execute(req)
    l = curs.fetchone()
    if(l == None):
        await msg.channel.send("Identifiant de la partie non trouvé")
        curs.close()
        cdesc.close()
        return
    (game_pgn, id_blanc, id_noir, joueur_jouant) = l
    board = chess.Board()
    pgn_ = io.StringIO(game_pgn)
    game = pgn.read_game(pgn_)
    for m in game.mainline_moves():
        board.push(m)

    id_messager = msg.author.id
    id_player_to_move = id_blanc if board.turn == chess.WHITE else id_noir
    if(id_messager != id_player_to_move):
        await msg.channel.send("Le mauvais joueur tente de jouer")
        curs.close()
        cdesc.close()
        return
    try:
        move_played = board.push_san(move)
        new_pgn_g = game.from_board(board)
        new_pgn = new_pgn_g.accept(pgn.StringExporter(headers =True))
        if board.is_game_over(claim_draw = True):
            result = board.result(claim_draw = True)
            fin_de_partie_bd(msg, result, new_pgn, game_id, id_blanc, id_noir, cursor)
            cdesc.commit()
            cursor.close()
            cdesc.close()
            return
        requete_update = "UPDATE games SET pgn = '{0}', joueur_jouant = '{1}' WHERE id_partie = {2};"
        req2 = requete_update.format(new_pgn, str(not joueur_jouant), game_id)
        curs.execute(req2)
        cdesc.commit()
        curs.close()
        cdesc.close()
    except ValueError:
        await msg.channel.send("Le coup est mauvais.")
        curs.close()
        cdesc.close()
        return
 

