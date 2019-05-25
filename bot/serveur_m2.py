import asyncio
import discord
import requests

id_serveur_m2 = None
id_serveur_m1 = None

def init(keys):
    global id_serveur_m2
    global id_serveur_m1
    id_serveur_m1 = int(keys['id_serveur_m1'])
    id_serveur_m2 = int(keys['id_serveur_m2'])
    pass


async def role_me(msg):
    print(msg.guild.id)
    print(id_serveur_m2)
    if (msg.guild == None or msg.guild.id != id_serveur_m2):
        print('different guild')
        return
    
    tab_ = msg.content.split(' ')
    
    if(len(tab_) <= 1):
        await msg.channel.send("Indiquez un rôle en paramètre")
        return

    str_r_list = tab_[1:]
    serv_role_list = []
    membre = msg.author

    for rolename in str_r_list:
        role_found = False
        str_role_demande = rolename.lower()
        for role_server in msg.guild.roles:
            if( role_server.hoist ):
                str_role_serv = str(role_server).lower()
                if str_role_serv == str_role_demande:
                    if role_server in membre.roles:
                        await membre.remove_roles(role_server, reason="Commande appellée")
                    else:
                        await membre.add_roles(role_server, reason="Commande appellée")
                    role_found = True
        if not role_found:
            await msg.channel.send("Le rôle {0} a pas été trouvé".format(str_role_demande))
        
    

### Renvoie une blague blsk au hasard
### TODO : vérification du serveur
async def blsk(msg):
    if(msg.guild.id != id_serveur_m1 and msg.guild.id != id_serveur_m2):
        return
    requete ='https://api.chucknorris.io/jokes/random?category=dev'
    res = requests.get(requete).json()
    phrase = res['value'].replace('Norris', 'Balabonski').replace('Chuck', 'Thibaut') + ' <:blsk:498584036638457857>'
    await msg.channel.send(phrase)
