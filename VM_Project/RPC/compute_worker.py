import pika
import ast
from VM_Project import vm_libvirt


def act_parser(data):
    name_vm = data['name_vm'] if 'name_vm' in data else None
    myVM = vm_libvirt.VM(name=name_vm)
    return getattr(myVM, data['act'])(**data)


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
        print "\n\n{}\n\n".format(body)
        data = ast.literal_eval(body)
        print " [.] do next func: {}".format(data['act'])
        resp = act_parser(data)
        ch.basic_publish(exchange='workers',
                         routing_key='manager',
                         body=resp)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def listening(self):
        self.channel.queue_bind(exchange='workers',
                                queue='manager',
                                routing_key='manager')
        self.channel.queue_bind(exchange='workers',
                                queue='vm',
                                routing_key='cw')
        self.channel.basic_qos(prefetch_count=100)
        self.channel.basic_consume(self.on_request, queue='vm')
        print " [x] Awaiting RPC requests"
        self.channel.start_consuming()


if __name__ == '__main__':
    amqp = RpcClient()
    amqp.listening()
