import ConfigParser
import _winreg
import os
import socket
import sys
import urllib2
import uuid
from subprocess import Popen, CREATE_NEW_CONSOLE, PIPE


class BrowserRetrieverWindows:

    @staticmethod
    def get_registry_value(the_key, subkey, value, browser):
        try:
            key = getattr(_winreg, the_key)
            handle = _winreg.OpenKey(key, subkey)

            if browser == 'chrome1':
                version = False
                try:
                    i = 0
                    while True:
                        newHandle = _winreg.OpenKey(key, '%s\\%s' % (subkey, _winreg.EnumKey(handle, i)))
                        name, _ = _winreg.QueryValueEx(newHandle, 'name')
                        if name == 'Google Chrome':
                            version, _ = _winreg.QueryValueEx(newHandle, 'pv')
                            break
                        i += 1
                except WindowsError:
                    pass
            else:
                version, _ = _winreg.QueryValueEx(handle, value)
        except:
            return False

        return version

    def get_browsers(self):
        browsers = {}

        if self.get_registry_value('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Wow6432Node\\Google\\Update\\Clients', None, 'chrome1'):
            browsers['chrome'] = self.get_registry_value('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Wow6432Node\\Google\\Update\\Clients', None, 'chrome1')
        elif self.get_registry_value('HKEY_CURRENT_USER', 'SOFTWARE\\Google\\Chrome\\BLBeacon', 'version', 'chrome'):
            browsers['chrome'] = self.get_registry_value('HKEY_CURRENT_USER', 'SOFTWARE\\Google\\Chrome\\BLBeacon', 'version', 'chrome')
        elif self.get_registry_value('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome', 'version', 'chrome'):
            browsers['chrome'] = self.get_registry_value('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome', 'version', 'chrome')

        ver = self.get_registry_value('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Mozilla\\Mozilla Firefox', 'CurrentVersion', 'firefox')
        print ver
        if ver:
            browsers['firefox'] = ver

        ver = self.get_registry_value('HKEY_LOCAL_MACHINE', 'SOFTWARE\\Microsoft\\Internet Explorer', 'Version', 'ie')
        print ver
        if ver:
            browsers['internet explorer'] = ver

        if os.path.isfile("C:\Windows\SystemApps\Microsoft.MicrosoftEdge_8wekyb3d8bbwe\MicrosoftEdge.exe"):
            browsers['microsoft edge'] = True

        return browsers


def get_selenium_settings():
    config = ConfigParser.ConfigParser()
    config.read(os.path.abspath(os.path.join(sys.path[0], 'config.ini')))
    port = config.get('CONFIG', 'port')
    hub_host = config.get('CONFIG', 'hub_host')

    try:
        socket.inet_aton(socket.gethostbyname(hub_host))
        return port, hub_host
    except socket.error:
        return port, config.get('CONFIG', 'hub_ip')


def get_selenium_path():
    """
    This method locates the Selenium Standalone Server in the 'controller' directory and returns its location and
    file name (enables upgrading the Selenium Standalone Server without having to change the code).
    """

    for f in os.listdir(sys.path[0]):
        if f.startswith('selenium-server-standalone') and f.endswith('.jar'):
            return os.path.abspath(os.path.join(sys.path[0], str(f)))
    try:
        print "Could not find Selenium Standalone Server. Attempting to download..."
        response = urllib2.urlopen(
            "https://selenium-release.storage.googleapis.com/2.53/selenium-server-standalone-2.53.0.jar")
        CHUNK = 16 * 1024
        with open(os.path.abspath(os.path.join(sys.path[0], 'selenium-server-standalone-2.53.0.jar')), 'wb') as f:
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
        print "Finished downloading Selenium Standalone Server."
        return os.path.abspath(os.path.join(sys.path[0], 'selenium-server-standalone-2.53.0.jar'))
    except:
        print "Something went wrong while attempting to download Selenium Standalone Server. Exiting..."


def get_driver(browser, name=None):
    driver_dir = os.path.abspath(os.path.join(sys.path[0], 'drivers'))
    for f in os.listdir(driver_dir):
        if browser in f.lower():
            if name:
                return '-Dwebdriver.%s.driver="%s" ' % (name, os.path.abspath(os.path.join(driver_dir, str(f))))
            else:
                return '-Dwebdriver.%s.driver="%s" ' % (browser, os.path.abspath(os.path.join(driver_dir, str(f))))


def start_selenium_grid(browsers):
    selenium_path = get_selenium_path()

    port, hub_host = get_selenium_settings()

    uu_id = str(uuid.uuid1())

    command = 'java -jar \"' + selenium_path + '\" '
    command += '-port %s ' % port
    command += '-hubHost %s ' % hub_host
    command += '-role webdriver '
    command += '-hostname %s ' % socket.gethostname()
    command += '-uuid %s ' % uu_id
    command += get_driver('ie')
    command += get_driver('chrome')
    command += get_driver('microsoft', 'edge')

    for browser_name, version in browsers.iteritems():
        if browser_name == 'microsoft edge':
            browser_name = browser_name.title().replace(' ', '')
        command += '-browser \"browserName=' + browser_name
        if version is not True:
            command += ",version=" + version
        command += ',applicationName=' + uu_id
        command += "\" "

    print command
    p=Popen(command, creationflags=0, stderr=PIPE)

    with p.stderr:
        for line in iter(p.stderr.readline, b''):
            print line.split('\n')[0]

if __name__ == "__main__":
    browser_retriever = BrowserRetrieverWindows()
    browsers = browser_retriever.get_browsers()

    start_selenium_grid(browsers)
