#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import sys
import serial
import time

class EchonetLiteClient:
    def __init__(self, serialport, baudrate):
        print("serialport={}, baudrate={}".format(serialport, baudrate))
        self.ser = serial.Serial(serialport, baudrate)

    def send(self, command):
        self.ser.write(command.encode())
        print(self.ser.readline())
        print(self.ser.readline())
        print(self.ser.readline(), end="\n")

    def ver(self):
        command = "SKVER\r\n"
        self.send(command)

    #Bルート認証パスワード設定
    def set_pw(self, password):
        command = "SKSETPWD C " + password + "\r\n"
        self.send(command)

    # Bルート認証ID設定
    def set_id(self, id):
        command = "SKSETRBID " + id + "\r\n"
        self.send(command)

    def scan(self):
        duration = 6;   # スキャン時間
        results = {} # スキャン結果の入れ物

        while not "Channel" in results:
            self.ser.write("SKSCAN 2 FFFFFFFF " + str(scanDuration) + " 0 \r\n")
            scan_end = False
            while not scan_end:
                line = self.ser.readline()
                print(line)

                if line.startsWith("EVENT 22"):
                    scan_end = True
                elif line.startswith("  ") :
                    cols = line.strip().split(':')
                    results[cols[0]] = cols[1]
            duration+=1
            if duration > 7 and not "Channel" in results:
                # 引数としては14まで指定できるが、7で失敗したらそれ以上は無駄らしい
                print("scan failed")
                sys.exit()


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

    client = EchonetLiteClient(serialport, baudrate)
    client.ver()
    #client.set_id(args.b_route_id)
    #client.set_pw(args.b_route_password)

if __name__ == '__main__':
    main()
