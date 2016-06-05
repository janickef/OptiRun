import ConfigParser
import os
import socket
import sys
import uuid
from os import path
from subprocess import Popen, CREATE_NEW_CONSOLE

from browser_retriever_windows import BrowserRetrieverWindows


def get_selenium_settings():
    config = ConfigParser.ConfigParser()

    config_path = path.abspath(path.join(path.dirname(__file__), '..\..\..', 'config.ini'))
    config.read(config_path)

    port = config.get('SELENIUMSERVER', 'node_port')

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    lan_ip = s.getsockname()[0]

    return port


def get_selenium_path():
    for f in os.listdir(sys.path[0]):
        if f.startswith('selenium-server-standalone') and f.endswith('.jar'):
            return path.abspath(path.join(sys.path[0], str(f)))


def get_driver(browser):
    driver_dir = path.abspath(path.join(sys.path[0], 'drivers'))
    for f in os.listdir(driver_dir):
        if browser in f.lower():
            return '-Dwebdriver.%s.driver="%s" ' % (browser, path.abspath(path.join(driver_dir, str(f))))


def start_selenium_grid(browsers):
    selenium_path = get_selenium_path()

    port = get_selenium_settings()

    uu_id = str(uuid.uuid1())

    command = 'java -jar \"' + selenium_path + '\" '
    command += '-hubHost LNOR010710 '
    #command += '-hubHost 192.168.43.26 '
    #command += '-port %s ' % port
    command += '-port %s ' % 5555
    command += '-role webdriver '
    command += '-hostname %s ' % socket.gethostname()
    command += '-uuid %s ' % uu_id
    command += get_driver('ie')
    command += get_driver('chrome')

    for browser_name, version in browsers.iteritems():
        command += '-browser \"browserName=' + browser_name
        if version is not True:
            command += ",version=" + version
        command += ',applicationName=' + uu_id
        command += "\" "

    print command
    Popen(command, creationflags=CREATE_NEW_CONSOLE)


if __name__ == "__main__":
    get_selenium_settings()
    print socket.gethostbyname(socket.gethostname())

    browser_retriever = None
    browsers = {}

    browser_retriever = BrowserRetrieverWindows()
    browsers = browser_retriever.get_browsers()

    for k, v in browser_retriever.get_browsers().iteritems():
        print k, v

    start_selenium_grid(browsers)
