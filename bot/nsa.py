
    
def write_file(msg):
    id_s = msg.server.id
    spy_path = "./spy/" + msg.server.name + '(' + id_s + ')_' + msg.channel.name + '(' + msg.channel.id + ')'
    em_l = msg.embeds
    str_eml = '' if len(em_l) == 0 else str(em_l)
    str_in = str(msg.author) + ':\t' + msg.content + '\n' + str_eml +'\n\n'
    fdesc = open(spy_path, 'a')
    fdesc.write(str_in)
    fdesc.close()

@client.event
async def on_message_delete(msg):
    id_s = msg.server.id
    spy_path = "./deletions/" + msg.server.name + '(' + id_s + ')_' + msg.channel.name + '(' + msg.channel.id + ')'
    em_l = msg.embeds
    str_in = str(msg.author) + ':\t' + msg.content + '\n'
    fdesc = open(spy_path, 'a')
    fdesc.write(str_in)
    fdesc.close()
    
@client.event
async def on_message_edit(bef, aft):
    id_s = bef.server.id
    edit_path = "./modifs/" + bef.server.name + '(' + id_s + ')_' + bef.channel.name + '(' \
                + bef.channel.id + ')'
    str_pre = bef.content + '\n'
    str_post= aft.content + '\n'
    str_ = str(bef.author) + ':\n' + "before:\t" + str_pre + "after:\t" + str_post + "\n"
    fdesc = open(edit_path, 'a')
    fdesc.write(str_)
    fdesc.close()

write_msg(msg):
    message = msg.content
    msg_ret = ':\n'
    ## commandes spécifiques au serveur m1
    id_s = msg.server.id
    write_file(msg)
