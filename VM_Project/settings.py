import ConfigParser


class Settings_install(dict):
    def __init__(self, way):
        self.config = ConfigParser.ConfigParser()
        self.config.read(way)
        super(Settings_install, self).__init__(
            {k: v for k, v in self.config.items('DEFAULT')})

    def __getattribute__(self, name):
        try:
            return self[name]
        except KeyError:
            msg = "'%s' object has no attribute '%s'"
            raise AttributeError(msg % (type(self).__name__, name))

    def __setattr__(self, name, value):  # ex_cl.s = 3
        self[name] = value

    def __delattr__(self, name):  # del ex_cl.s
        del self[name]
