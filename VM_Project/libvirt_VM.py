#!/usr/bin/env python
import libvirt
import argparse
import os
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import Settings_install


class VM_DB(declarative_base()):
    __tablename__ = 'vm'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    status = Column(String(128))

    def __init__(self, name, status):
        self.name = name
        self.status = status

    def __repr__(self):
        return "<VM_DB('{}', '{}','{}')>".format(self.id,
                                                 self.name,
                                                 self.status)


def decor_for_return(func):
    def some_func(self):
        func(self)
        self.machine = self.session.query(VM_DB)\
            .filter_by(name=self.name).one()
        resp = '\n' + 'VM with name = ' + self.machine.name\
               + " ID = " + self.machine.id\
               + ' is ' + self.machine.status + '\n'
        print resp
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
        self.FLAGS = Settings_install("../etc/config.ini")
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
        self.engine = create_engine('mysql://{}:{}@{}/{}'
                                    .format(self.FLAGS.mysql_user,
                                            self.FLAGS.mysql_password,
                                            self.FLAGS.mysql_host,
                                            self.FLAGS.mysql_name),
                                    echo=False)
        self.Base = declarative_base()
        self.Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def __repr__(self):
        return self.dom.ID(), self.dom.name()

    def __str__(self):
        return "ID your VM={}, name={}".format(self.dom.ID(),
                                               self.dom.name())

    def create_VM(self, nameVM, memoryVM, pathVM):
        vm_xml = self.xml.format(name=nameVM, memory=memoryVM,
                                 path='\'{}\''.format(pathVM))
        self.conn.defineXML(vm_xml)
        self.conn.lookupByName(nameVM).create()
        self.dom = self.conn.lookupByName(nameVM)
        new_vm = VM_DB(nameVM, 'work')
        self.session.add(new_vm)
        self.session.commit()
        self.session.close()
        self.machine = self.session.query(VM_DB).filter_by(name=nameVM).one()
        resp = '\n' + 'VM with name = ' + self.machine.name\
               + ' is ' + self.machine.status + '\n'
        print resp
        return resp

    @decor_for_return
    def destroy_VM(self):
        self.dom.destroy()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "down"})
        self.session.commit()
        self.session.close()

    @decor_for_return
    def start_VM(self):
        self.dom.create()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "work"})
        self.session.commit()
        self.session.close()

    def undefine_VM(self):
        resp = "VM with name={}" \
               " will be undefine".format(self.dom.name(),)
        print resp
        self.dom.undefine()
        self.machine = self.session.query(VM_DB)\
            .filter_by(name=self.name).one()
        self.session.delete(self.machine)
        self.session.commit()
        self.session.close()
        return resp

    @decor_for_return
    def suspend_VM(self):
        self.dom.suspend()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "stop"})
        self.session.commit()
        self.session.close()

    @decor_for_return
    def resume_VM(self):
        self.dom.resume()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "works"})
        self.session.commit()
        self.session.close()

    @decor_for_return
    def shutdown_VM(self):
        self.dom.shutdown()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "down"})
        self.session.commit()
        self.session.close()

    def connect_VM(self):
        resp = "try connect to VM with name={}".format(self.dom.name(),)
        print resp
        os.system("virt-viewer --connect "
                  "qemu:///system {}".format(self.dom.name(),))
        return resp

    def show_VM(self):
        resp = ''
        for id, name, status in self.session.query(VM_DB.id,
                                                   VM_DB.name,
                                                   VM_DB.status):
            resp += str(id) + " " + name + " " + status + "\n"
        print resp
        return resp

    def __getattr__(self, key):
        if key == 'show_VM':
            return self.show_VM()
        elif key == 'create_VM':
            return self.create_VM()
        elif key == 'connect_VM':
            return self.connect_VM()
        elif key == 'destroy_VM':
            return self.destroy_VM()
        elif key == 'udefine_VM':
            return self.undefine_VM()
        elif key == 'start_VM':
            return self.start_VM()
        elif key == 'suspend_VM':
            return self.suspend_VM()
        elif key == 'resume_VM':
            return self.resume_VM()
        elif key == 'shutdown_VM':
            return self.shutdown_VM()


def super_puper_act(data):
    #print "\n\n\n!!!!!!!DATA!!!!!!!\n\n\n", data
    #print type(data), data['nameVM']
    try:
        myVM = VM(data['nameVM'])
    except KeyError:
        myVM = VM()
    try:
        getattr(myVM, data['act'])()
    except TypeError:
        getattr(myVM, data['act'])(nameVM=data['nameVM'],
                                   memoryVM=data['memoryVM'],
                                   pathVM=data['pathVM'])


def for_main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(metavar="Chose next action")

    start_parser = subparsers.add_parser('start', help='start VM')
    start_parser.add_argument('-s', dest='nameVM', help='<name of VM>')
    start_parser.set_defaults(handler=super_puper_act, act='start_VM')

    destroy_parser = subparsers.add_parser('destroy', help='stop VM')
    destroy_parser.add_argument('-d', dest='nameVM', help='<name of VM>')
    destroy_parser.set_defaults(handler=super_puper_act, act='destroy_VM')

    connect_parser = subparsers.add_parser('connect', help='connect to VM')
    connect_parser.add_argument('-c', dest='nameVM', help='<name of VM>')
    connect_parser.set_defaults(handler=super_puper_act, act='connect_VM')

    show_VM_parser = subparsers.add_parser('show_VM', help='Show_VM')
    show_VM_parser.add_argument('-s', help='<name of VM>', default=None)
    show_VM_parser.set_defaults(handler=super_puper_act, act='show_VM')

    shutdown_parser = subparsers.add_parser('shutdown', help='shutdown VM')
    shutdown_parser.add_argument('-s', dest='nameVM', help='<name of VM>')
    shutdown_parser.set_defaults(handler=super_puper_act, act='shutdown_VM')

    suspend_parser = subparsers.add_parser('suspend', help='suspend VM')
    suspend_parser.add_argument('-s', dest='nameVM', help='<name of VM>')
    suspend_parser.set_defaults(handler=super_puper_act, act='suspend_VM')

    undefine_parser = subparsers.add_parser('undefine', help='undefine VM')
    undefine_parser.add_argument('-u', dest='nameVM', help='<name of VM>')
    undefine_parser.set_defaults(handler=super_puper_act, act='undefine_VM')

    resume_parser = subparsers.add_parser('resume', help='resume work VM')
    resume_parser.add_argument('-r', dest='nameVM', help='<name of VM>')
    resume_parser.set_defaults(handler=super_puper_act, act='resume_VM')

    create_parser = subparsers.add_parser('create', help='Create a new VM')
    create_parser.add_argument('-name', dest='nameVM', required=True,
                               help='<name of VM>')
    create_parser.add_argument('-mem', dest='memoryVM', required=True,
                               help='<memory for VM in KiB>')
    create_parser.add_argument('-path', dest='pathVM', required=True,
                               help='<path to VM.img>')
    create_parser.set_defaults(handler=super_puper_act, act='create_VM')

    args = parser.parse_args()
    args_dict = vars(parser.parse_args())
    args.handler(args_dict)

if __name__ == '__main__':
    print "\nHello! This scrypt useful for cirros in virtual machine!\n" \
          "Thanks for mutual development!\n"
    for_main()
