import argparse
import pika
import json
from webob import Request
from webob import Response
from webob import exc
from VM_Project import vm_sql
from wsgiref.simple_server import make_server


class RpcClient(object):
    def __init__(self, host='localhost'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=host))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='workers',
                                      type='direct')
        self.channel.queue_declare(queue='vm')
        self.channel.queue_declare(queue='manager')

    def on_request(self, ch, method, props, body):
        if "create" in body:
            self.myVM = vm_sql.VM(name=body.split()[0])
            self.myVM.change_vm_status_after_completed_creation()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def listening(self):
        self.channel.queue_bind(exchange='workers',
                                queue='manager',
                                routing_key='manager')
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.on_request, queue='manager')
        self.channel.start_consuming()

    def call(self, dict_data):
        self.channel.basic_publish(exchange='workers',
                                   routing_key=dict_data['routing_key'],
                                   properties=pika.BasicProperties(
                                       content_type='application/json'),
                                   body=json.dumps(dict_data))
        self.connection.close()


def send_to_worker(func):
    def some_func(self, req):
        func(self, req)
        request = RpcClient()
        request.call(self.dict_data)
    return some_func


class ApiHandler(object):
    def __call__(self, environ, start_response):
        req = Request(environ)
        self.dict_data = {key: value for key, value in req.json.items()}
        name_vm = req.json['name_vm'] if 'name_vm' in req.json else None
        self.myVM = vm_sql.VM(name=name_vm)
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

    @send_to_worker
    def connect_vm(self, req):
        pass

    @send_to_worker
    def shutdown_vm(self, req):
        return self.myVM.shutdown_vm()

    @send_to_worker
    def resume_vm(self, req):
        return self.myVM.resume_vm()

    @send_to_worker
    def suspend_vm(self, req):
        return self.myVM.suspend_vm()

    @send_to_worker
    def undefine_vm(self, req):
        return self.myVM.undefine_vm()

    @send_to_worker
    def start_vm(self, req):
        return self.myVM.start_vm()

    @send_to_worker
    def destroy_vm(self, req):
        return self.myVM.destroy_vm()

    @send_to_worker
    def create_vm(self, req):
        self.dict_data['mac'] = self.myVM\
            .create_vm(name_vm=req.json['name_vm'])


def start_httpd(host, port):
    print 'Started on http://%s:%s' % (host, port)
    handler = ApiHandler()
    httpd = make_server(host, port, handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


def start_amqp_listener():
    print "AMQP listener start"
    listener = RpcClient()
    listener.listening()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='8080', dest='port', type=int,
                        help='Port to serve on (default 8080)')
    parser.add_argument('-a', '--addr', default='localhost', dest='host',
                        help='Host to serve on (default localhost)')
    args_dict = vars(parser.parse_args())
    args = parser.parse_args()
    import multiprocessing
    p1 = multiprocessing.Process(target=start_httpd, args=(args.host,
                                                           args.port))
    p2 = multiprocessing.Process(target=start_amqp_listener, args=())
    p2.start()
    p1.start()
    p2.join()
    p1.join()
