#!/usr/bin/env python

import ConfigParser
import socket
import sys
import threading
from os import path
from subprocess import Popen, CREATE_NEW_CONSOLE, PIPE


def process(command, creationflags, stderr):
    p = Popen(command, creationflags=creationflags, stderr=stderr)

    with p.stderr:
        for line in iter(p.stderr.readline, b''):
            print line.replace('\n', '')


def start_process(command, creationflags, stderr):
    process_thread = threading.Thread(target=process, args=(command, creationflags, stderr))
    process_thread.start()


if __name__ == "__main__":
    current_folder = sys.path[0]

    config = ConfigParser.ConfigParser()
    config_path = path.abspath(path.join(current_folder, 'config.ini'))
    config.read(config_path)

    ip = socket.gethostname()
    port = config.get('WEBSERVER', 'port')

    connect_to = ip + ":" + port

    #start_process(['python', current_folder + '\manage.py', 'runserver', connect_to], 0, PIPE)
    #start_process(['python', current_folder + '\manage.py', 'runserver', connect_to], CREATE_NEW_CONSOLE, None)
    #Popen(['python', current_folder + '\manage.py', 'runserver', connect_to], stderr=PIPE)
    Popen(['python', current_folder + '\manage.py', 'runserver', '--insecure', connect_to], creationflags=CREATE_NEW_CONSOLE)
    start_process(['python', current_folder + '\controller\hub\controller.py'], 0, PIPE)
