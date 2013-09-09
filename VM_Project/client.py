import urllib2
import json
import argparse


def to_json(data):
    return json.dumps(data)


def super_puper_act(data, dict_data):
    url = 'http://{}:{}/{}'.format(data.host, data.port, data.act)
    dict_data.pop('handler')
    print url
    req = urllib2.Request(url, to_json(dict_data))
    print urllib2.urlopen(req).read()


def for_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='8080', dest='port',
                        help='Port to serve on (default 8080)')
    parser.add_argument('-a', '--addr', default='localhost', dest='host',
                        help='Host to serve on (default localhost)')
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
    create_parser.add_argument('-way', dest='pathVM', required=True,
                               help='<path to VM.img>')
    create_parser.set_defaults(handler=super_puper_act, act='create_VM')

    args = parser.parse_args()
    args_dict = vars(parser.parse_args())
    #print args
    #print args_dict
    args.handler(args, args_dict)

if __name__ == '__main__':
    for_main()
