import discord
import logging
import psycopg

params_db = None
dico_logs = dict()

def init(keys):
    global params_db
    global dico_logs
    password=keys['password']
    params_db = {'dbname' : 'synobot_db', 'user' : "synobot", 'password' : password}
    # initialisation du dico à partir des paramètres
    requete = "SELECT id_serveur, id_channel, type_logs FROM logs_serveur"
    
    cdesc = psycopg2.connect(**params_db)
    cursor= cdesc.cursor()
    cursor.execute(requete)
    try:
        for (ids, idc, tl) in cursor.fetchall():
            dico_logs[idc] = (ids, tl)
    except ProgrammingError e: # cas où il n'y a pas de résultat
        pass

    curs.close()
    cdes.close()
    
async def definition_log_salon(msg):
    id_salon = msg.channel
    # test si la personne a les droits
    
    pass
async def suppression_logs_salon(msg):
    pass

async def on_message_edit(msg_before, msg_after):
    pass

async def on_message_delete(msg):
    pass

