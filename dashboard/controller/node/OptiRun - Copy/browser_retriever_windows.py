import sys

import _winreg

class BrowserRetrieverWindows:

    @staticmethod
    def get_registry_value(subkey, value, browser):
        try:
            key = getattr(_winreg, 'HKEY_LOCAL_MACHINE')
            handle = _winreg.OpenKey(key, subkey)

            if browser == 'chrome':
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

        ver = self.get_registry_value('SOFTWARE\\Wow6432Node\\Google\\Update\\Clients', None, 'chrome')
        if ver:
            browsers['chrome'] = ver

        ver = self.get_registry_value('SOFTWARE\\Mozilla\\Mozilla Firefox', 'CurrentVersion', 'firefox')
        if ver:
            browsers['firefox'] = ver

        ver = self.get_registry_value('SOFTWARE\\Microsoft\\Internet Explorer', 'Version', 'ie')
        if ver:
            browsers['internet explorer'] = ver

        return browsers


"""
def get_registry_value(key, subkey, value):
    if sys.platform != 'win32':
        raise OSError("get_registry_value is only supported on Windows")

    import _winreg
    key = getattr(_winreg, key)
    handle = _winreg.OpenKey(key, subkey)
    (value, type) = _winreg.QueryValueEx(handle, value)
    return value


class BrowserRetrieverWindows:
    @staticmethod
    def get_firefox_version():
        try:
            version = get_registry_value(
                "HKEY_LOCAL_MACHINE",
                "SOFTWARE\\Mozilla\\Mozilla Firefox",
                "CurrentVersion")
        except WindowsError:
            version = None
        return version

    @staticmethod
    def get_ie_version():
        try:
            version = get_registry_value(
                "HKEY_LOCAL_MACHINE",
                "SOFTWARE\\Microsoft\\Internet Explorer",
                "Version")
        except WindowsError:
            version = None
        return version

    @staticmethod
    def get_chrome_version():
        try:
            version = get_registry_value(
                "HKEY_LOCAL_MACHINE",
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe",
                "Path")
            if version:
                version = True
        except WindowsError:
            version = None
        return version

    def get_browsers(self):
        browsers = {}

        if self.get_firefox_version() is not None:
            browsers['firefox'] = self.get_firefox_version()

        if self.get_ie_version() is not None:
            browsers['internet explorer'] = self.get_ie_version()

        if self.get_chrome_version() is not None:
            browsers['chrome'] = self.get_chrome_version()

        return browsers
"""



