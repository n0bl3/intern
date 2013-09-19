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
import vm_states as state


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
        self.FLAGS = SettingsInstall(os.environ['MINI_OPEN_STACK'] +
                                     '/etc/config.ini')
        self.name = name
        self.engine = create_engine('mysql://{}:{}@{}/{}'
                                    .format(self.FLAGS.mysql_user,
                                            self.FLAGS.mysql_password,
                                            self.FLAGS.mysql_host,
                                            self.FLAGS.mysql_name),
                                    echo=False)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def _cmd_kill_hup(self):
        with open('/var/run/dnsmasq/dnsmasq.pid', 'r') as pid:
            self.dnsmasq_pid = pid.read().rstrip()
        kill_hup = subprocess.Popen(["sudo", 'kill', '-HUP',
                                     '{}'.format(self.dnsmasq_pid)],
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
        return kill_hup.communicate()

    def create_vm(self, name_vm):
        self.available_adr = self.session.query(Address)\
            .filter_by(allocate=0).first()
        with open("{}".format(self.FLAGS.dnsmasq_conf_path),
                  'a') as conf:
            conf.write('{},{}\n'.format(self.available_adr.mac,
                                        self.available_adr.ip))
        self._cmd_kill_hup()
        self.new_vm = VM_DB(name_vm, state.IN_PROGRESS)
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
        mac = self.available_adr.mac
        self.session.close()
        return mac

    @for_log
    def change_vm_status_after_completed_creation(self):
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": state.UP})
        self.session.commit()
        self.session.close()

    @for_log
    def destroy_vm(self):
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": state.DOWN})
        self.session.commit()
        self.session.close()

    @for_log
    def start_vm(self):
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": state.UP})
        self.session.commit()
        self.session.close()

    def undefine_vm(self):
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

    @for_log
    def suspend_vm(self):
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": state.DOWN})
        self.session.commit()
        self.session.close()

    @for_log
    def resume_vm(self):
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": state.UP})
        self.session.commit()
        self.session.close()

    @for_log
    def shutdown_vm(self):
        self.session.query(VM_DB)\
            .filter(VM_DB.name == self.name).update({"status": state.DOWN})
        self.session.commit()
        self.session.close()

    def show_vm(self):
        resp = ''
        for id, name, status in self.session.query(VM_DB.id,
                                                   VM_DB.name,
                                                   VM_DB.status):
            resp += str(id) + " " + name + " " + status + os.linesep
        if not resp:
            resp = "There's no such VM"
        print resp
        return resp
