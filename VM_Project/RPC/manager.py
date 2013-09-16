import pika
import uuid
import json


class RpcClient(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, dict_data):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=dict_data['routing_key'],
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         content_type = 'application/json',
                                         correlation_id = self.corr_id,
                                         ),
                                   body=json.dumps(dict_data))
        while self.response is None:
            self.connection.process_data_events()
        return self.response
