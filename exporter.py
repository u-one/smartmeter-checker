from prometheus_client import start_http_server, Gauge

import argparse
import json
import echonetlite as el
import time
import threading

current = 0
done = False

serialport = '/dev/ttyUSB0'  # linux
baudrate = 115200
client = el.EchonetLiteClient(serialport, baudrate)

g = Gauge('electricity_power', 'watt')


def parse_args():
    parser = argparse.ArgumentParser()
    # 必須
    parser.add_argument("b_route_id", help="Bルート認証ID")
    parser.add_argument("b_route_password", help="Bルート認証パスワード")
    # 任意
    parser.add_argument("--serialport", help="optional")
    parser.add_argument("--baudrate", help="optional")
    return parser.parse_args()


args = parse_args()
if hasattr(args, 'serialport'):
    serialport = args.serialport
if hasattr(args, 'baudrate'):
    baudrate = args.baudrate


def get_loop():
    while not done:
        res, val = client.getValue()
        if res:
            current = val
            g.set(val)
        time.sleep(30)

def dummy_loop():
    while not done:
        print("hoge")
        time.sleep(10)

try:
    client.ver()
    client.connect(args.b_route_id, args.b_route_password) 

    #thread = threading.Thread(target=get_loop)
    #thread.start()

    start_http_server(8081)

    get_loop()


except KeyboardInterrupt:
    print("KeyboardInterrupt")
finally:
    done = True
    client.close()


