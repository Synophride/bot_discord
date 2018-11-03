import threading

class Thread_bot(threading.Thread):
    def run(self):
        shell_exec('python3 bot.py')


# Se mettre dans le bon répertoire
shell_exec('')

# Tuer le programme python
ligne_ps = shell_exec('ps -A | grep synobot-python').split('\n')
for i in ligne_ps:
    pid = i.strip().split(' ')[0]
    shell_exec('kill ' + pid)
    
# Lancer une mise à jour github
ligne_pull = shell_exec('git pull origin master')

# Relancer le bot
th = Thread_bot('python3 bot.py')
th.start()
print('0')
exit
