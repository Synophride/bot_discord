import discord
import logging
import asyncio
import setproctitle
import serveur_m2 as m2
from discord.ext import commands

import commandes_echecs as e
import commandes_generales as gen

# lien d'invit = https://discordapp.com/oauth2/authorize?client_id=505813694278795264&permissions=8&scope=bot
print('Version discord :')
print( discord.__version__)


# Renommage du processus (sera utile lors du script de màj)
setproctitle.setproctitle('synobot')

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


oauth_discord = keys['oauth_discord']
id_m2 = int(keys['id_serveur_m2'])

e.init(keys)
m2.init(keys)
gen.init(keys)

async def do_nothing(msg):
    print("NE FAIT RIEN")

#######
##
## 
##
#######

descripteur_commandes = {
    'status' : 'Affiche «en ligne» si le bot est en ligne',
    'cblock' : 'Affiche la suite du message dans un bloc de code.',
    'chat' : 'Afficher une photo de chat',
    'norris' : 'Fait une blague chuck norris',
    'breakingbad' : 'Affiche une réplique de breaking bad',
    'choose' : 'Fait un choix entre plusieurs options, séparées par le signe |. Exemple d\'utilisation: !choose 1 | 2 | 3',
    'qst' : 'Répond à une question fermée',
    
    'puzzle' : 'Affiche une tactique d\'échecs',
    'soluce' : 'Affiche la solution de la dernière tactique demandée',
    'lichess': 'Affiche les elos sur le site lichess.org du pseudo donné en paramètre',
    'liembed': 'Affiche les elos sur le site lichess.org du pseudo donné en paramètre (un peu plus proprement que lichess)',
    #chesscom pas encore fonctionnel
}

descripteur_commandes_m2 = {
    'role_me' : 'Donne le rôle en paramètre',
    'blsk' : 'Affiche un fait peu connu du public sur Thibaut Balabonski'
}


async def help_msg(msg):
    em = discord.Embed()
    em.clear_fields()
    for command_name in descripteur_commandes.keys():
        em.add_field(name=command_name,
                     value=descripteur_commandes[command_name], inline=False)
    if msg.guild.id == id_m2 :
        for command_name in descripteur_commandes_m2.keys():
            em.add_field(name=command_name,
                         value=descripteur_commandes_m2[command_name], inline=False)
            
    await msg.channel.send('?', embed = em)
    
dico_fonctions = {
    ### 1 : Module général
    'status' : gen.status,
    'cblock' : gen.codeblock,
    'chat'   : gen.chat,
    'norris' : gen.norris,
    'help'   : help_msg,
    'breakingbad':gen.bbad,
    'choose' : gen.choose,
    'qst'    : gen.qst,
    'ratp'   : gen.train_problems,
    
    ### 2.1 : commandes d'échecs «générales»
    'puzzle' : e.puzzle_chesscom, # à mettre à jour
    'soluce' : e.puzzle_solution,
    'lichess': e.lichess,
    'chesscom':e.chesscomelo, # à mettre à jour: API changée
    'liembed': e.embedded_lichess,

    ### 2.2 : commandes d'échecs pour les parties
    'challenge': e.challenge_bd,
    'accept' : e.acceptation_bd,
    'move'   : e.move_bd,
    'movelist' : e.movelist_bd,
    'show_board' : e.show_board,
    ### 3.  : Commandes spécifiques au serveur m2
    'role_me' : m2.role_me,
    'blsk'    : m2.blsk,    
}


###################################
# Initialisation des variables
###################################

# préfixe de la commande
prefixes=dict()

#########################################
###
### <<main>>
###
#########################################
client=discord.Client()

@client.event
async def on_ready():
    print('Serveurs : ')
    for i in client.guilds:
        print("\t", i)


@client.event
async def on_message(msg):
    global nb_id
    global current_games
    global challenge_list
    id_s = msg.guild.id
    message = msg.content
    prefix = prefixes.get(id_s, '!')
    if( message.startswith( prefix ) ):
        full_commande = message.split(' ')[0]
        commande = full_commande.replace(prefix, '', 1)
        print("commande lue : ", commande)
        fun = dico_fonctions.get(commande, do_nothing)
        await fun(msg)

client.run(oauth_discord)
