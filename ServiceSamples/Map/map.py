import time
import argparse
import utl
import math
import paho.mqtt.client as mqtt


class Subscriber(object):
    def __init__(self, broker_address, topic):
        # subscriber can register multiple topic, so topics is a list
        self.topic = topic

        self.broker_address = broker_address
        self.broker_port = 1883

        mqtt.Client.connected_flag = False
        self.mqtt_client = mqtt.Client()

        self.logger = utl.get_logger('Map', 'MapLog')

        self.time_flag = time.time()
        self.buffer = []

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.connected_flag = True  # set flag
            self.logger.info("Connected to broker")
        else:
            client.connected_flag = False
            self.logger.info("Bad connection Returned code=%s" % str(rc))

    def on_message(self, client, userdata, message):
        payload = message.payload.decode()
        self.logger.info('[Subscribe] %s' % payload)
        # transfer messages
        if time.time() - self.time_flag > 5:
            record = [float(i.split(',')[2]) for i in self.buffer]
            payload = sum(record)/len(record)
            self.mqtt_client.publish(topic='%s/map' % self.topic, payload=str(payload))
            self.logger.info('[Publish] %s' % str(payload))
            self.buffer = []
            self.time_flag = time.time()
        else:
            self.buffer.append(payload)

    # handle mqtt service
    def handler(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.loop_start()
        self.mqtt_client.connect(host=self.broker_address, port=self.broker_port)
        while not self.mqtt_client.connected_flag:  # wait in loop
            self.logger.info("In wait loop")
            time.sleep(1)
            self.logger.info("Main Loop")

        # set Qos to 2
        self.mqtt_client.subscribe(topic=self.topic, qos=2)
        self.logger.info("Subscribed new topic: %s" % self.topic)

        # make subscriber loop forever to listen messages from broker
        self.mqtt_client.loop_forever()
        self.mqtt_client.disconnect()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--topic', type=str, help='Topic')
    parser.add_argument('-a', '--address', type=str, help='Broker address')
    args = parser.parse_args()
    sub = Subscriber(args.address, args.topic)
    sub.handler()