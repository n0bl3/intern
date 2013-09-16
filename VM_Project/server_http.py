import argparse
from webob import Request
from webob import Response
from webob import exc
from VM_Project import libvirt_vm
from wsgiref.simple_server import make_server


class ApiHandler(object):
    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            self.myVM = libvirt_vm.VM(name=req.json['name_vm'])
        except KeyError:
            self.myVM = libvirt_vm.VM()
        meth_name = req.path[1:].replace('/', '_')
        try:
            if hasattr(self, meth_name):
                resp = Response(getattr(self, meth_name)(req))
            else:
                resp = exc.HTTPBadRequest('No such action %r' % req.path)
        except exc.HTTPException, e:
            resp = e
        return resp(environ, start_response)

    def show_vm(self, req):
        return self.myVM.show_vm()

    def connect_vm(self, req):
        return self.myVM.connect_vm()

    def shutdown_vm(self, req):
        return self.myVM.shutdown_vm()

    def resume_vm(self, req):
        return self.myVM.resume_vm()

    def suspend_vm(self, req):
        return self.myVM.suspend_vm()

    def undefine_vm(self, req):
        return self.myVM.undefine_vm()

    def start_vm(self, req):
        return self.myVM.start_vm()

    def destroy_vm(self, req):
        return self.myVM.destroy_vm()

    def create_vm(self, req):
        return self.myVM.create_vm(req.json['name_vm'], req.json['memory_vm'], req.json['path_to_vm'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='8080', dest='port', type=int,
                        help='Port to serve on (default 8080)')
    parser.add_argument('-a', '--addr', default='localhost', dest='host',
                        help='Host to serve on (default localhost)')
    args_dict = vars(parser.parse_args())
    args = parser.parse_args()
    print args_dict
    print args.port
    handler = ApiHandler()
    httpd = make_server(args.host, args.port, handler)
    print 'Started on http://%s:%s' % (args.host, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        exit()
