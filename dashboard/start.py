import ConfigParser
import socket
import sys
import threading
from os import path
from subprocess import Popen, CREATE_NEW_CONSOLE, PIPE


def process(command, creationflags, stderr, ):
    p = Popen(command, creationflags=creationflags, stderr=stderr, stdout=PIPE)

    with p.stderr:
        for line in iter(p.stderr.readline, b''):
            print line.replace('\n', '')

    #with p.stderr:
    #    for line in iter(p.stderr.readline, b''):
    #        print line.replace('\n', '')


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

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print s.getsockname()[0]

    import os
    import django

    project_path = os.path.abspath(os.path.join(sys.path[0], '..', '..'))

    if project_path not in sys.path:
        sys.path.append(project_path)

    os.environ['PYTHONPATH'] = os.path.abspath(os.path.join(sys.path[0], '..', '..'))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'dashboard.settings'

    django.setup()

    from django.contrib.sites.models import Site

    if not Site.objects.filter(domain=s.getsockname()[0]):
        site = Site(name=s.getsockname()[0], domain=s.getsockname()[0])
        site.save()

    #start_process(['python', current_folder + '\manage.py', 'runserver', '10.0.0.4:80'], 0, PIPE)
    #start_process(['python', current_folder + '\manage.py', 'runserver', '%s:80' % s.getsockname()[0]], 0, PIPE)
    #start_process(['python', current_folder + '\manage.py', 'runserver', connect_to], CREATE_NEW_CONSOLE, None)
    #Popen(['python', current_folder + '\manage.py', 'runserver', connect_to], stderr=PIPE)
    Popen(['python', current_folder + '\manage.py', 'runserver', '--insecure', '%s:80' % s.getsockname()[0]], creationflags=CREATE_NEW_CONSOLE, stderr=PIPE, stdout=PIPE, shell=True)
    Popen(['python', current_folder + '\controller\hub\controller.py'], creationflags=CREATE_NEW_CONSOLE, stderr=PIPE, stdout=PIPE, shell=True)
    #start_process(['python', current_folder + '\controller\hub\controller.py'], 0, PIPE)
