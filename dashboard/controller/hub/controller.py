"""
Main method of the Controller. Creates instances of the other modules and starts threads.
"""

import sys
import threading
from os import path

from executor import Executor
from request_listener import RequestListener
from schedule_checker import ScheduleChecker
from selenium_server_listener import SeleniumHub
from test_machine_manager import TestMachineManager



if __name__ == "__main__":
    print("OptiRun Controller starting up...")

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

    # Creating 'Schedule Checker' instance and start threads
    threading.Thread(target=ScheduleChecker(executor).start_threads).start()

    """

    import time
    time.sleep(5)

    import urllib2  # the lib that handles the url stuff

    #data = urllib2.urlopen("http://localhost:4444/grid/console?config=true&configDebug=true")  # it's a file like object and works just like a file
    #for line in data:  # files are iterable
    #    print line

    #print '\n\n\n'

    import httplib

    data = urllib2.urlopen("http://localhost:4444/grid/console")  # it's a file like object and works just like a file
    print data.info()
    #for line in data:  # files are iterable
    #    print line

    #exit()
    """