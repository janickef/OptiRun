class TestObj:

    def __init__(self, id, title, script_name, duration, browser, platform):
        self._id = int(id)
        self._title = title
        self._script_name = script_name
        self._browser = browser
        if duration:
            self._duration = duration
        else:
            self._duration = 60.0
        self._platform = platform

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title

    @property
    def script_name(self):
        return self._script_name

    @property
    def duration(self):
        return self._duration

    @property
    def platform(self):
        return self._platform

    @property
    def browser(self):
        return self._browser

    def set_browser(self, browser):
        self._browser = browser

    def __eq__(self, other):
        try:
            return self._id != other.id and self._browser == other.browser and self._platform == other.platform
        except:
            return False

    def __str__(self):
        return "%s: %s, dur: %s, browser: %s, platform: %s" \
               % (str(self.id), self._title, str(self.duration), self._browser, self._platform)