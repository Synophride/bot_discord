import discord
import logging
import asyncio
import setproctitle
from discord.ext import commands

import commandes_echecs as e
import commandes_generales as gen



dico_fonctions = {
    ### 1 : Module général
    'status' : gen.status,
    'cblock' : gen.codeblock,
    'chat'   : gen.chat,
    'norris' : gen.norris,
    'bordi'  : gen.bordi,
    'blsk'   : gen.blsk,
    'breakingbad':gen.bbad,
    'choose' : gen.choose,
    'qst'    : gen.qst,

    ### 2.1 : commandes d'échecs «générales»
    'puzzle' : e.puzzle_chesscom, # à mettre à jour
    'soluce' : e.puzzle_solution,
    'lichess': e.lichess,
    'chesscom':e.chesscomelo, # à mettre à jour
    'liembed': e.embedded_lichess,

    ### 2.2 : commandes d'échecs pour les parties
    'challenge': e.challenge_bd,
    'accept' : e.acceptation_bd,
    'move'   : e.move_bd,
    
}


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

def do_nothing(msg, client):
    print("NE FAIT RIEN")
    pass

###################################
# Initialisation des variables
###################################

oauth_discord = keys['oauth_discord']
id_serveur_m1 = keys['id_serveur_m1']
api_key_chat  = keys['api_key_chat']

# préfixe de la commande
prefixes=dict()

# Liste des commandes du bot (TODO : mettre à jour, peut-être le déplacer)
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

## commande spécifiques au serveur m1 (mettre à jour, pê le déplacer)
commandes_m1_desc={'duncan thom' : 'Génération de blagues du prof d\'anglais du g2', \
                   'blsk' : 'Découvrez un fait inconnu de la vie de blsk' }

#########################################
###
### <<main>>
###
#########################################
client=discord.Client()

@client.event
async def on_ready():
    print('Serveurs : ')
    for i in client.servers:
        print("\t", i)


@client.event
async def on_message(msg):
    global nb_id
    global current_games
    global challenge_list
    id_s = msg.server.id
    message = msg.content
    prefix = prefixes.get(id_s, '!')
    if( message.startswith( prefix ) ):
        full_commande = message.split(' ')[0]
        commande = full_commande.replace(prefix, '', 1)
        print("commande lue : ", commande)
        fun = dico_fonctions.get(commande, do_nothing)
        await fun(msg, client)


client.run(oauth_discord)
