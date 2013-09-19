import urllib2
import json
import argparse
from VM_Project.RPC.manager import RpcClient


def act_parser(data, dict_data):
    dict_data.pop('handler')
    url = 'http://{}:{}/{}'.format(data.host, data.port, data.act)
    print url
    req = urllib2.Request(url, json.dumps(dict_data))
    print urllib2.urlopen(req).read()


def for_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='8080', dest='port',
                        help='Port to serve on (default 8080)')
    parser.add_argument('-a', '--addr', default='localhost', dest='host',
                        help='Host to serve on (default localhost)')
    parser.add_argument('-m', '--MQ', default=None, dest='routing_key',
                        help='enter routing_key')
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

    show_vm_parser = subparsers.add_parser('show_VM', help='Show_VM')
    show_vm_parser.add_argument('-s', help='<name of VM>', default='show')
    show_vm_parser.set_defaults(handler=act_parser, act='show_vm')

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
    args.handler(args, args_dict)

if __name__ == '__main__':
    for_main()
