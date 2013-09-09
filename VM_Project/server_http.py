from wsgiref.simple_server import make_server
import argparse
from webob import Request, Response
from webob import exc
from VM_Project import libvirt_VM


class ApiHandler(object):
    def __call__(self, environ, start_response):
        req = Request(environ)
        try:
            self.myVM = libvirt_VM.VM(name=req.json['nameVM'])
        except KeyError:
            self.myVM = libvirt_VM.VM()
        meth_name = req.path[1:].replace('/', '_')
        try:
            if hasattr(self, meth_name):
                resp = Response(getattr(self, meth_name)(req))
            else:
                resp = exc.HTTPBadRequest('No such action %r' % req.path)
        except exc.HTTPException, e:
            resp = e
        return resp(environ, start_response)

    def show_VM(self, req):
        return self.myVM.show_VM()

    def connect_VM(self, req):
        return self.myVM.connect_VM()

    def shutdown_VM(self, req):
        return self.myVM.shutdown_VM()

    def resume_VM(self, req):
        return self.myVM.resume_VM()

    def suspend_VM(self, req):
        return self.myVM.suspend_VM()

    def undefine_VM(self, req):
        return self.myVM.undefine_VM()

    def start_VM(self, req):
        return self.myVM.start_VM()

    def destroy_VM(self, req):
        return self.myVM.destroy_VM()

    def create_VM(self, req):
        return self.myVM.create_VM(req.json)


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
