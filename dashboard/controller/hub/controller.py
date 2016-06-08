"""
Main method of the Controller. Creates instances of the other modules and starts threads.
"""

import os
import shutil
import socket
import sys
import threading
from ConfigParser import SafeConfigParser
from os import path

import zipfile

from executor import Executor
from request_listener import RequestListener
from schedule_listener import ScheduleListener
from selenium_server_listener import SeleniumHub
from test_machine_manager import TestMachineManager


def zip_files():
    dirs = ['linux', 'windows']
    section = 'CONFIG'

    for item in dirs:

        print item
        src = os.path.abspath(os.path.join(sys.path[0], '..', 'node', item))
        config_path = os.path.abspath(os.path.join(src, 'config.ini'))

        config = SafeConfigParser()
        config.read(config_path)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))

        if section not in config.sections():
            config.add_section(section)

        config.set(section, 'port', '5555')
        config.set(section, 'hub_host', socket.gethostname())
        config.set(section, 'hub_ip', s.getsockname()[0])

        with open(config_path, 'w') as f:
            config.write(f)

        try:
            archive = shutil.make_archive(item, 'zip', src)
            shutil.copy(archive, os.path.abspath(os.path.join(sys.path[0], '..', '..', 'files')))
            os.remove(archive)
        except:
            print "Something went wrong while attempting to zip, move or delete %s files." % item.title()

if __name__ == "__main__":
    print("OptiRun Controller starting up...")

    zip_files()

    current_path = sys.path[0]
    controller_path = path.abspath(path.join(current_path, ".."))
    project_path = path.abspath(path.join(controller_path, ".."))

    # Creating 'Test Machine Manager' instance
    test_machine_manager = TestMachineManager(project_path)

    # Creating 'Executor' instance
    executor = Executor(test_machine_manager)

    # Creating 'Request Listener' instance and start listening in thread
    threading.Thread(target=RequestListener().listen_for_requests, args=(executor,)).start()

    # Creating 'Selenium Server Listener' instance and start listening in thread
    threading.Thread(target=SeleniumHub(project_path, controller_path, test_machine_manager).start_selenium_grid).start()

    # Creating 'Schedule Listener' instance and start threads
    threading.Thread(target=ScheduleListener(executor).start_threads).start()
