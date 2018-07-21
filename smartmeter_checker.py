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
        self.ser = serial.Serial(serialport, baudrate, timeout=1)
        self.scan_results = {}

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

        while not b"Channel" in self.scan_results:
            command = "SKSCAN 2 FFFFFFFF " + str(duration) + " 0 \r\n"
            self.ser.write(command.encode())
            scan_end = False
            while not scan_end:
                line = self.ser.readline()
                print(line)

                if line.startswith(b"EVENT 22"):
                    scan_end = True
                    pass
                elif line.startswith(b"  "):
                    cols = line.strip().split(b':')
                    self.scan_results[cols[0]] = cols[1]
            duration+=1
            if duration > 8 and not b"Channel" in self.scan_results:
                # 引数としては14まで指定できるが、7で失敗したらそれ以上は無駄らしい
                print("scan failed")
                sys.exit()

    def set_channel(self):
        # スキャン結果からChannelを設定。
        command = "SKSREG S2 " + self.scan_results[b"Channel"].decode() + "\r\n"
        self.send(command)

    def set_panid(self):
        # スキャン結果からPan IDを設定
        command = "SKSREG S3 " + self.scan_results[b"Pan ID"].decode() + "\r\n"
        self.send(command)

    def translate_address(self):
        # MACアドレス(64bit)をIPV6リンクローカルアドレスに変換
        command = "SKLL64 " + self.scan_results[b"Addr"].decode() + "\r\n"
        self.ser.write(command.encode())
        print(self.ser.readline(), end="") # エコーバック
        self.ipv6Addr = self.ser.readline().strip().decode()
        print(self.ipv6Addr)

    def start_join(self):
        # PANA 接続シーケンスを開始します。
        command = "SKJOIN " + self.ipv6Addr + "\r\n"
        print(command)

    def wait_join(self):
        # PANA 接続完了待ち（10行ぐらいなんか返してくる）
        bConnected = False
        while not bConnected :
            line = ser.readline()
            print(line, end="")
            if line.startswith("EVENT 24") :
                print("PANA 接続失敗")↲
                sys.exit()  #### 糸冬了 ####↲
            elif line.startswith("EVENT 25") :
                # 接続完了！
                bConnected = True


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
    client.set_id(args.b_route_id)
    client.set_pw(args.b_route_password)
    client.scan()
    client.set_channel()
    client.set_panid()
    client.translate_address()
    client.start_join()

if __name__ == '__main__':
    main()
