import argparse
import time
import echonetlite as el

def parse_args():
    parser = argparse.ArgumentParser()
    # 必須
    parser.add_argument("b_route_id", help="Bルート認証ID")
    parser.add_argument("b_route_password", help="Bルート認証パスワード")
    # 任意
    parser.add_argument("--serialport", help="optional")
    parser.add_argument("--baudrate", help="optional")
    return parser.parse_args()



serialport = '/dev/ttyUSB0'  # linux
#serialport = 'COM1' # windows
#serialport = '/dev/cu.usbserial-XXXXX'    # mac
baudrate = 115200

def main():
    args = parse_args()
    if hasattr(args, 'serialport'):
        serialport = args.serialport
    if hasattr(args, 'baudrate'):
        baudrate = args.baudrate

    try:
        client = el.EchonetLiteClient(serialport, baudrate)
        client.ver()
        client.connect(args.b_route_id, args.b_route_password) 
        client.getValue()

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    finally:
        client.close()

if __name__ == '__main__':
    main()
