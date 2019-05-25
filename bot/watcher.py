import setproctitle
import subprocess


nb_relances = 0
setproctitle.setproctitle('synobot_watcher')

while(True):
    process= subprocess.run(['python3', 'bot.py'])
