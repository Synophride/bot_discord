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


params_db = None

def init(keys):
    global params_db
    password=keys['password']
    params_db = {'dbname' : 'synobot_db', 'user' : "synobot", 'password' : password}

def status(b):
    if b:
        return "En ligne"
    else:
        return "Hors ligne"



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
    await msg.channel.send( "La solution était : ||" + pgn_dico[channel_id] + '||' )

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

##########################################
## Parties d'échecs avec base de données #
##########################################

async def challenge_bd(msg):
    id_j1 = msg.author.id
    nom_j1 = str(msg.author)

    id_j2 = 0 
    mention = False
    if(len(msg.mentions) == 1):
        mention = True
        id_j2 = msg.mentions[0].id
    elif len(msg.mentions) > 1:
        await msg.channel.send("Impossible, pour l'instant, de ping plusieurs joueurs en même temps")
    
    requete = "INSERT INTO challenges (id_j1, id_j2, name_j1) VALUES ('{0}', '{1}', '{2}');".format(id_j1, id_j2, nom_j1)
    
    conn_desc = psycopg2.connect(**params_db)
    curseur = conn_desc.cursor()
    
    curseur.execute(requete)
    curseur.execute("SELECT currval('seq_challenge');")
    
    currval = curseur.fetchone()
    conn_desc.commit()

    curseur.close()
    conn_desc.close()
    
    str_j2 = "quelqu'un"
    if len(msg.mentions)>0:
        str_j2 = str(msg.mentions[0])
        
    msg_ = "Le joueur {0} a défié {1} pour une partie d'échecs. Tapez <préfixe du serveur>accept {2} pour accepter et commencer la partie"
    msg_retour = msg_.format(nom_j1, str_j2, currval)
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
    modele_req = "SELECT id_j1, id_j2, id_challenge, name_j1 FROM challenges WHERE (id_j2='{0}' OR id_j2 = '0') AND id_challenge = {1};"
    req = modele_req.format(id_acceptant, str(id_partie_acceptee))

    curs.execute(req)
    res_tuple = curs.fetchone()
    if(res_tuple == None):
        await msg.channel.send("Identifiant de la partie non trouvé")
        return
    
    (idj1, idj2, idpartie, name_j1) = res_tuple
    
    id_white = idj1
    nom_white = name_j1
    
    id_black = msg.author.id
    nom_black = str(msg.author)
    
    if(random.random() < 0.5):
        id_white = idj2
        nom_white = nom_black
        
        id_black = idj1
        nom_black = name_j1

    pgn_game = pgn.Game() # todo : mettre 

    requete_deletion_challenge = "DELETE FROM challenges WHERE id_challenge = {0};"
    requete_ajout_games = "INSERT INTO games (pgn, id_blanc, id_noir, id_partie, nom_blanc, nom_noir) VALUES ('{0}', '{1}', '{2}', {3}, '{4}', '{5}');"

    requete_del = requete_deletion_challenge.format(idpartie)
    requete_ajout = requete_ajout_games.format(pgn_game, id_white, id_black, idpartie, nom_white, nom_black)

    curs.execute(requete_del)
    curs.execute(requete_ajout)

    cdesc.commit()
    curs.close()
    cdesc.close()

    message_retour = "La partie opposant {0} avec les blancs, et {1} avec les noirs peut commencer" 
    await msg.channel.send(message_retour.format(nom_white, nom_black))

## Renommer la table
async def fin_de_partie_bd(msg, result, pgn, game_id, id_blanc, id_noir, nom_blanc, nom_noir, cursor):
    requete_remove = "DELETE FROM games WHERE id_partie = {0};"
    req1 = requete_remove.format(game_id)

    requete_add = "INSERT INTO parties_terminees (pgn, resultat, id_blanc, id_noir, nom_blanc, nom_noir, id_partie) VALUES ('{0}','{1}', '{2}', '{3}', '{4}', '{5}', {6});"
    req2 = requete_add.format(pgn, result, id_blanc, id_noir, nom_blanc, nom_noir, game_id)

    cursor.execute(req1)
    cursor.execute(req2)

    msg_retour = "Fin de la partie. résultat : {0} {1} {2}" 
    await msg.channel.send(msg_retour.format(nom_blanc, result, nom_noir))

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
    
    requete_modele = "SELECT pgn, id_blanc, id_noir, joueur_jouant, nom_blanc, nom_noir FROM games WHERE id_partie = {0};"

    req = requete_modele.format(str(game_id))

    curs.execute(req)
    l = curs.fetchone()
    
    if(l == None):
        await msg.channel.send("Identifiant de la partie non trouvé")
        curs.close()
        cdesc.close()
        return
    
    (game_pgn, id_blanc, id_noir, joueur_jouant, nom_blanc, nom_noir) = l
    
    board = chess.Board()
    pgn_ = io.StringIO(game_pgn)
    game = pgn.read_game(pgn_)
    
    for m in game.mainline_moves():
        board.push(m)

    id_messager = str(msg.author.id)
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
            await fin_de_partie_bd(msg, result, new_pgn, game_id, id_blanc, id_noir, nom_blanc, nom_noir, curs)
            cdesc.commit()
            curs.close()
            cdesc.close()
            return
        
        requete_update = "UPDATE games SET pgn = '{0}', joueur_jouant = '{1}' WHERE id_partie = {2};"
        req2 = requete_update.format(new_pgn, str(not joueur_jouant), game_id)

        curs.execute(req2)
        cdesc.commit()
        curs.close()
        cdesc.close()
        
        await msg.channel.send("Le coup a été joué")
        
    except ValueError:
        await msg.channel.send("Le coup est mauvais.")
        curs.close()
        cdesc.close()
        return
 

async def movelist_bd(msg):
    contents = msg.content.split(' ')
    if len(contents) == 1:
        await msg.channel.send('Pas d\'identifiant de partie donné')
        return
    else:
        id_partie = int(contents[1])
        modele_requete = "SELECT pgn FROM games WHERE id_partie = '{0}';"
        requete = modele_requete.format(id_partie)
        cdesc = psycopg2.connect(**params_db)
        cursor = cdesc.cursor()

        cursor.execute(requete)
        (pgn_, ) = cursor.fetchone()
        pgn_strio = io.StringIO(pgn_)
        game = pgn.read_game(pgn_strio)
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)

        movelist = board.legal_moves
        strlist = map(lambda x : board.san(x), movelist)
        await msg.channel.send(' '.join(strlist))
        return
        
# Factoriser la recherche de pgn d'une partie ?
# Gestion plus propre du cas où la partie est pas trouvée
async def show_board(msg):
    contenu = msg.content.split(' ')
    if len(contenu) == 1:
        await msg.channel.send("Pas d'id de partie donné")
        return
    id_partie = 0
    try:
        id_partie = int(contenu[1])
    except ValueError:
        await msg.channel.send("Pas le bon format d'identifiant")
        return
    em = discord.Embed(title = 'Partie ' + str(id_partie))
    modele_requete = "SELECT pgn FROM games WHERE id_partie = '{0}';"
    requete = modele_requete.format(id_partie)
    cdesc = psycopg2.connect(**params_db)
    cursor = cdesc.cursor()
    
    cursor.execute(requete)
    (pgn_, ) = cursor.fetchone()
    pgn_strio = io.StringIO(pgn_)
    game = pgn.read_game(pgn_strio)
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
    fen = board.fen().split()[0].strip()
    addr="https://backscattering.de/web-boardimage/board.png?fen=" + fen
    em.set_image(url=addr)
    await msg.channel.send(embed = em)

### Todo : liste(s) de parties / challenges. 
###  Garder l'id serveur de la partie
###  Recherche d'archives
