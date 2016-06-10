class TestMachineObj:

    def __init__(self, browsers, hostname, platform, url, uuid):
        self._browsers = browsers
        self._hostname       = hostname
        self._platform = platform
        self._url      = url
        self._uuid     = uuid

    @property
    def browsers(self):
        return self._browsers

    @property
    def hostname(self):
        return self._hostname

    @property
    def platform(self):
        return self._platform

    @property
    def url(self):
        return self._url

    @property
    def uuid(self):
        return self._uuid

    def __str__(self):
        return "%s, %s, %s, %s, %s"\
               % (str(self._platform), self._hostname, self._url, str(self._browsers), self._uuid)
