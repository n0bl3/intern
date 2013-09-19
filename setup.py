from setuptools import setup
import configparser
import os
setup(
    name="mini-openstack",
    description=("Internship project"),
    version="0.1.2",
    author="Yuriy Leonov",
    packages=['VM_Project', 'etc'],
    requires=['webob', 'sqlalchemy', 'ConfigParser', 'configparser',
              'alembic', 'wsgiref', 'pika'])

if not os.path.isfile('etc/config.ini'):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'mysql_name': 'None',
                         'mysql_user': 'None',
                         'mysql_password': 'None',
                         'mysql_host': 'None',
                         'libvirt_conn': 'None',
                         'xml_setting_for_VM': 'None',
                         'dnsmasq_conf_path': 'None'}
    with open('etc/config.ini', 'w') as file_conf:
        config.write(file_conf)
