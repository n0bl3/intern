import libvirt
import argparse
import subprocess
import os
from settings import SettingsInstall
from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class VM_DB(Base):
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


class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True)
    ip = Column(String(128))
    mac = Column(String(128))
    allocate = Column(Integer)
    vm = relationship("VM_DB")
    vm_id = Column(Integer, ForeignKey('vm.id'))

    def __init__(self, ip, mac, allocate):
        ''''''
        self.ip = ip
        self.mac = mac
        self.allocate = allocate

    def __repr__(self):
        return "<VM_DB('{}','{}','{}','{}','{}')>".format(self.id,
                                                          self.ip,
                                                          self.mac,
                                                          self.allocate,
                                                          self.vm_id)


def for_log(func):
    def some_func(self):
        func(self)
        self.machine = self.session.query(VM_DB)\
            .filter_by(name=self.name).one()
        resp = os.linesep + 'VM with name = %s' % self.machine.name +\
            " ID = %s" % str(self.machine.id) +\
            ' is %s' % self.machine.status + os.linesep
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
        self.FLAGS = SettingsInstall("../etc/config.ini")
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
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def __repr__(self):
        return self.dom.ID(), self.dom.name()

    def __str__(self):
        return "ID your VM={}, name={}".format(self.dom.ID(),
                                               self.dom.name())

    def _cmd_kill_hup(self):
        with open('/var/run/dnsmasq/dnsmasq.pid', 'r') as pid:
            self.dnsmasq_pid = pid.read().rstrip()
        kill_hup = subprocess.Popen(["sudo", 'kill', '-HUP',
                                     '{}'.format(self.dnsmasq_pid)],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
        return kill_hup.communicate()

    def create_vm(self, name_vm, memory_vm, path_to_vm):
        self.available_adr = self.session.query(Address)\
            .filter_by(allocate=0).first()
        vm_xml = self.xml.format(name=name_vm, memory=memory_vm,
                                 path='\'{}\''.format(path_to_vm),
                                 mac='\'{}\''.format(self.available_adr.mac))
        with open("{}".format(self.FLAGS.dnsmasq_conf_path),
                  'a') as conf:
            conf.write('{},{}\n'.format(self.available_adr.mac,
                                        self.available_adr.ip))
        self._cmd_kill_hup()
        self.conn.defineXML(vm_xml)
        self.conn.lookupByName(name_vm).create()
        self.dom = self.conn.lookupByName(name_vm)
        self.new_vm = VM_DB(name_vm, 'work')
        self.session.add(self.new_vm)
        self.session.commit()
        self.machine = self.session.query(VM_DB)\
            .filter_by(name=name_vm).one()
        self.session.query(Address)\
            .filter(Address.id == self.available_adr.id)\
            .update({'allocate': 1, 'vm_id': self.machine.id})
        self.session.commit()
        resp = '\n' + 'VM with name = ' + self.machine.name\
               + ' is ' + self.machine.status + '\n'
        self.session.close()
        print resp
        return resp

    @for_log
    def destroy_vm(self):
        self.dom.destroy()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "down"})
        self.session.commit()
        self.session.close()

    @for_log
    def start_vm(self):
        self.dom.create()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "work"})
        self.session.commit()
        self.session.close()

    def undefine_vm(self):
        resp = "VM with name={}" \
               " will be undefine".format(self.dom.name(),)
        self.dom.undefine()
        self.machine = self.session.query(VM_DB)\
            .filter_by(name=self.name).one()
        self.addr_db = self.session.query(Address)\
            .filter_by(vm_id=self.machine.id).first()
        self.session.query(Address)\
            .filter_by(vm_id=self.machine.id)\
            .update({'allocate': 0, 'vm_id': None})
        self.session.delete(self.machine)
        line_for_new_file = []
        with open("{}".format(self.FLAGS.dnsmasq_conf_path),
                  'r') as conf:
            for line in conf.readlines():
                if self.addr_db.mac not in line:
                    line_for_new_file.append(line)
        with open("{}".format(self.FLAGS.dnsmasq_conf_path),
                  'w') as conf:
            conf.write(''.join(line_for_new_file))
        self._cmd_kill_hup()
        self.session.commit()
        self.session.close()
        print resp
        return resp

    @for_log
    def suspend_vm(self):
        self.dom.suspend()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "stop"})
        self.session.commit()
        self.session.close()

    @for_log
    def resume_vm(self):
        self.dom.resume()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "works"})
        self.session.commit()
        self.session.close()

    @for_log
    def shutdown_vm(self):
        self.dom.shutdown()
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": "down"})
        self.session.commit()
        self.session.close()

    def connect_vm(self):
        resp = "try connect to VM with name={}".format(self.dom.name(),)
        print resp
        os.system("virt-viewer --connect "
                  "qemu:///system {}".format(self.dom.name(),))
        return resp

    def show_vm(self):
        resp = ''
        for id, name, status in self.session.query(VM_DB.id,
                                                   VM_DB.name,
                                                   VM_DB.status):
            resp += str(id) + " " + name + " " + status + "\n"
        print resp
        return resp


def act_parser(data):
    try:
        myVM = VM(data['name_vm'])
    except KeyError:
        myVM = VM()
    try:
        getattr(myVM, data['act'])()
    except TypeError:
        getattr(myVM, data['act'])(name_vm=data['name_vm'],
                                   memory_vm=data['memory_vm'],
                                   path_to_vm=data['path_to_vm'])


def for_main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(metavar="Chose next action")

    start_parser = subparsers.add_parser('start', help='start VM')
    start_parser.add_argument('-s', dest='name_vm', help='<name of VM>')
    start_parser.set_defaults(handler=act_parser, act='start_vm')

    destroy_parser = subparsers.add_parser('destroy', help='stop VM')
    destroy_parser.add_argument('-d', dest='name_vm', help='<name of VM>')
    destroy_parser.set_defaults(handler=act_parser, act='destroy_vm')

    connect_parser = subparsers.add_parser('connect', help='connect to VM')
    connect_parser.add_argument('-c', dest='name_vm', help='<name of VM>')
    connect_parser.set_defaults(handler=act_parser, act='connect_vm')

    show_VM_parser = subparsers.add_parser('show_VM', help='Show_VM')
    show_VM_parser.add_argument('-s', help='<name of VM>', default=None)
    show_VM_parser.set_defaults(handler=act_parser, act='show_vm')

    shutdown_parser = subparsers.add_parser('shutdown', help='shutdown VM')
    shutdown_parser.add_argument('-s', dest='name_vm', help='<name of VM>')
    shutdown_parser.set_defaults(handler=act_parser, act='shutdown_vm')

    suspend_parser = subparsers.add_parser('suspend', help='suspend VM')
    suspend_parser.add_argument('-s', dest='name_vm', help='<name of VM>')
    suspend_parser.set_defaults(handler=act_parser, act='suspend_vm')

    undefine_parser = subparsers.add_parser('undefine', help='undefine VM')
    undefine_parser.add_argument('-u', dest='name_vm', help='<name of VM>')
    undefine_parser.set_defaults(handler=act_parser, act='undefine_vm')

    resume_parser = subparsers.add_parser('resume', help='resume work VM')
    resume_parser.add_argument('-r', dest='name_vm', help='<name of VM>')
    resume_parser.set_defaults(handler=act_parser, act='resume_vm')

    create_parser = subparsers.add_parser('create', help='Create a new VM')
    create_parser.add_argument('-name', dest='name_vm', required=True,
                               help='<name of VM>')
    create_parser.add_argument('-mem', dest='memory_vm', required=True,
                               help='<memory for VM in KiB>')
    create_parser.add_argument('-path', dest='path_to_vm', required=True,
                               help='<path to VM.img>')
    create_parser.set_defaults(handler=act_parser, act='create_vm')

    args = parser.parse_args()
    args_dict = vars(parser.parse_args())
    args.handler(args_dict)

if __name__ == '__main__':
    print "\nHello! This scrypt useful for cirros in virtual machine!\n" \
          "Thanks for mutual development!\n"
    for_main()
