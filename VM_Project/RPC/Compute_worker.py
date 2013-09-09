import pika
import ast
import VM_Project.libvirt_vm

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='vm')

def act_parser(data):
    try:
        myVM = VM_Project.libvirt_vm.VM(data['name_vm'])
    except KeyError:
        myVM = VM_Project.libvirt_vm.VM()
    try:
        return getattr(myVM, data['act'])()
    except TypeError:
        return getattr(myVM, data['act'])(name_vm=data['name_vm'],
                                          memory_vm=data['memory_vm'],
                                          path_to_vm=data['path_to_vm'])

def on_request(ch, method, props, body):
    data = ast.literal_eval(body)
    print " [.] do next func: {}".format(data['act'])
    response = act_parser(data)
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                     props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(on_request, queue='vm')

print " [x] Awaiting RPC requests"
channel.start_consuming()