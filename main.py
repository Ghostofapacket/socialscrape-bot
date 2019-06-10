import os
import time

open('UPDATE', 'w').close()

launch = 1
while True:
    if launch == 1:
        os.system('git pull')
        os.system('python start.py')
        launch = 0
    if os.path.isfile('UPDATE'):
        time.sleep(60)
        os.system('git pull')
        os.system('python start.py')