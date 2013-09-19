import ConfigParser
import os
import sys


class SettingsInstall(dict):
    def __init__(self, way):
        if not os.path.isfile(way):
            print ("You don't have configurate file.\n"
                   "At first:\n"
                   "Please create configurate file in next folder:\n"
                   "your_project/etc/config.ini\n"
                   "Write in file next strings:\n"
                   "[DEFAULT]\n"
                   "mysql_password =\n"
                   "mysql_name =\n"
                   "mysql_host =\n"
                   "mysql_user =\n"
                   "xml_setting_for_vm =\n"
                   "libvirt_conn =\n"
                   "dnsmasq_conf_path =\n"
                   "\nSecond:\n"
                   "Please create environment variable:\n"
                   "export MINI_OPEN_STACK=\'<path to folder with project>\'")
            sys.exit()
        self.config = ConfigParser.ConfigParser()
        self.config.read(way)
        super(SettingsInstall, self).__init__(
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
