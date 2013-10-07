import libvirt
import os
from settings import SettingsInstall
from functools import wraps


def for_log(func):
    @wraps(func)
    def some_func(self, **kwargs):
        resp = "VM with name = {}" \
               " will be {}".format(self.dom.name(), str(func.__name__)[:-3])
        func(self)
        return resp
    return some_func


class VM(object):
    """
    This class can: create, stop(destroy),
    start(when VM destroy(shutdown)),
    undefine(delete)
    And this class useful for cirros.
    """
    def __init__(self, name=None, ID=None):
        self.FLAGS = SettingsInstall(os.environ['MINI_OPEN_STACK'] +
                                     '/etc/config.ini')
        self.conn = libvirt.open(self.FLAGS.libvirt_conn)
        self.xml = open(self.FLAGS.xml_setting_for_vm, "r").read()
        self.name = name
        try:
            if name:  # if we want work with already created VM
                self.dom = self.conn.lookupByName(name)
            if ID:
                self.dom = self.conn\
                    .lookupByName(self.conn.lookupByID(ID).name())
        except libvirt.libvirtError:
            print "wrong name VM, ID or no VM has been created."

    def __repr__(self):
        return self.dom.ID(), self.dom.name()

    def __str__(self):
        return "ID your VM={}, name={}".format(self.dom.ID(),
                                               self.dom.name())

    def create_vm(self, **kwargs):
        name_vm = kwargs['name_vm']
        memory_vm = kwargs['memory_vm']
        path_to_vm = kwargs['path_to_vm']
        mac_vm = kwargs['mac']
        vm_xml = self.xml.format(name=name_vm, memory=memory_vm,
                                 path='\'{}\''.format(path_to_vm),
                                 mac='\'{}\''.format(mac_vm))
        self.conn.defineXML(vm_xml)
        self.conn.lookupByName(name_vm).create()
        self.dom = self.conn.lookupByName(name_vm)
        resp = "{} " \
               "create".format(self.dom.name(),)
        return resp

    @for_log
    def destroy_vm(self, **kwargs):
        try:
            self.dom.destroy()
        except libvirt.libvirtError:
            print 'already stop'

    @for_log
    def start_vm(self, **kwargs):
        try:
            self.dom.create()
        except libvirt.libvirtError:
            print 'already start'

    @for_log
    def undefine_vm(self, **kwargs):
        resp = "VM with name={}" \
               " will be undefine".format(self.dom.name(),)
        self.dom.undefine()
        print resp
        return resp

    @for_log
    def suspend_vm(self, **kwargs):
        self.dom.suspend()

    @for_log
    def resume_vm(self, **kwargs):
        self.dom.resume()

    @for_log
    def shutdown_vm(self, **kwargs):
        self.dom.shutdown()

    def connect_vm(self, **kwargs):
        resp = "try connect to VM with name={}".format(self.dom.name(),)
        print resp
        os.system("virt-viewer --connect "
                  "qemu:///system {}".format(self.dom.name(),))
        return resp
