
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
